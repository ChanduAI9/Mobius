import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.knowledge import ParsedDocument, SourceType
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.embeddings.sentence_transformer import get_embedding_service
from app.infrastructure.knowledge.chunking import ChunkingService
from app.infrastructure.knowledge.connectors.github import GitHubConnector
from app.infrastructure.knowledge.connectors.local_folder import LocalFolderConnector
from app.infrastructure.knowledge.parsers import DocumentParser


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = DocumentRepository(session)
        self._embeddings = get_embedding_service()
        self._chunker = ChunkingService()
        self._parser = DocumentParser()
        self._local = LocalFolderConnector(self._parser)
        self._github = GitHubConnector()

    async def ingest_source(
        self, source_id: uuid.UUID, user_id: uuid.UUID, job_id: uuid.UUID | None = None
    ) -> dict:
        source = await self._repo.get_source(source_id, user_id)
        if not source:
            raise ValueError("Source not found")

        job = await self._repo.get_job(job_id, user_id) if job_id else None
        if not job:
            job = await self._repo.create_job(source.space_id, user_id, source_id)

        await self._repo.update_job(
            job.id, status="running", started_at=datetime.now(UTC), progress=0.0
        )

        try:
            if source.source_type == SourceType.LOCAL_FOLDER.value:
                stats = await self._ingest_local(source, user_id, job.id)
            elif source.source_type == SourceType.GITHUB.value:
                stats = await self._ingest_github(source, user_id, job.id)
            elif source.source_type in (SourceType.NOTION.value, SourceType.GOOGLE_DRIVE.value):
                stats = await self._ingest_plugin(source, user_id, job.id)
            else:
                raise ValueError(f"Unsupported source type: {source.source_type}")

            await self._repo.update_job(
                job.id,
                status="completed",
                progress=1.0,
                files_processed=stats["files_processed"],
                chunks_created=stats["chunks_created"],
                completed_at=datetime.now(UTC),
            )
            await self._repo.update_source_sync(source.id, stats.get("sync_cursor", {}))
            return {"job_id": str(job.id), **stats}
        except Exception as e:
            await self._repo.update_job(
                job.id, status="failed", error=str(e), completed_at=datetime.now(UTC)
            )
            raise

    async def ingest_upload(
        self,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        data: bytes,
    ) -> dict:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            raise ValueError("Knowledge space not found")

        parsed = self._parser.parse(filename, filename, data)
        chunks_created = await self._index_document(
            space_id=space_id,
            source_id=None,
            user_id=user_id,
            parsed=parsed,
        )
        return {"filename": filename, "chunks_created": chunks_created}

    async def _ingest_local(self, source, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        config = source.config
        root_path = config.get("path", "")
        if not root_path:
            raise ValueError("Local folder source requires 'path' in config")

        files = self._local.list_files(root_path)
        total = len(files)
        files_processed = 0
        chunks_created = 0
        sync_cursor: dict = {"files": {}}

        for i, abs_path in enumerate(files):
            rel_path = str(Path(abs_path).relative_to(Path(root_path).resolve())).replace("\\", "/")
            try:
                mtime = self._local.get_file_mtime(abs_path)
                existing = await self._repo.get_document_by_path(source.space_id, rel_path)
                if existing and existing.content_hash and existing.metadata_.get("mtime") == mtime:
                    sync_cursor["files"][rel_path] = {"mtime": mtime, "skipped": True}
                    continue

                parsed = self._local.read_file(abs_path)
                parsed.file_path = rel_path
                parsed.metadata["mtime"] = mtime
                parsed.metadata["absolute_path"] = abs_path

                count = await self._index_document(
                    space_id=source.space_id,
                    source_id=source.id,
                    user_id=user_id,
                    parsed=parsed,
                )
                chunks_created += count
                files_processed += 1
                sync_cursor["files"][rel_path] = {"mtime": mtime, "hash": parsed.content_hash}
            except Exception:
                continue

            await self._repo.update_job(
                job_id, progress=(i + 1) / max(total, 1), files_processed=files_processed
            )

        return {
            "files_processed": files_processed,
            "chunks_created": chunks_created,
            "sync_cursor": sync_cursor,
        }

    async def _ingest_github(self, source, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        config = source.config
        repo = config.get("repo", "")
        branch = config.get("branch", "main")
        path_prefix = config.get("path", "")

        if not repo:
            raise ValueError("GitHub source requires 'repo' in config")

        owner, repo_name = self._github.parse_repo_url(repo)
        file_list = await self._github.list_files(owner, repo_name, branch=branch, path=path_prefix)
        total = len(file_list)
        files_processed = 0
        chunks_created = 0
        sync_cursor: dict = {"files": {}, "branch": branch}

        for i, item in enumerate(file_list):
            file_path = item["path"]
            sha = item.get("sha")
            try:
                existing = await self._repo.get_document_by_path(source.space_id, file_path)
                if existing and existing.metadata_.get("github_sha") == sha:
                    sync_cursor["files"][file_path] = {"sha": sha, "skipped": True}
                    continue

                parsed = await self._github.fetch_file(owner, repo_name, file_path, branch=branch)
                count = await self._index_document(
                    space_id=source.space_id,
                    source_id=source.id,
                    user_id=user_id,
                    parsed=parsed,
                )
                chunks_created += count
                files_processed += 1
                sync_cursor["files"][file_path] = {"sha": sha, "hash": parsed.content_hash}
            except Exception:
                continue

            await self._repo.update_job(
                job_id, progress=(i + 1) / max(total, 1), files_processed=files_processed
            )

        return {
            "files_processed": files_processed,
            "chunks_created": chunks_created,
            "sync_cursor": sync_cursor,
        }

    async def _ingest_plugin(self, source, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        from app.plugins.registry import PluginRegistry

        config = source.config
        connector = PluginRegistry.get_connector(source.source_type)
        if not connector:
            raise ValueError(f"No plugin for source type: {source.source_type}")

        await connector.initialize(config)
        doc_refs = await connector.list_documents(config)
        total = len(doc_refs)
        files_processed = 0
        chunks_created = 0
        sync_cursor: dict = {"files": {}}

        for i, ref in enumerate(doc_refs):
            file_path = ref["path"]
            try:
                doc_hash = ref.get("hash", ref.get("id", ""))
                existing = await self._repo.get_document_by_path(source.space_id, file_path)
                if existing and existing.content_hash == doc_hash:
                    sync_cursor["files"][file_path] = {"skipped": True}
                    continue

                parsed = await connector.fetch_document(config, ref)
                count = await self._index_document(
                    space_id=source.space_id,
                    source_id=source.id,
                    user_id=user_id,
                    parsed=parsed,
                )
                chunks_created += count
                files_processed += 1
                sync_cursor["files"][file_path] = {"hash": parsed.content_hash}
            except Exception:
                continue

            await self._repo.update_job(
                job_id, progress=(i + 1) / max(total, 1), files_processed=files_processed
            )

        return {
            "files_processed": files_processed,
            "chunks_created": chunks_created,
            "sync_cursor": sync_cursor,
        }

    async def _index_document(
        self,
        *,
        space_id: uuid.UUID,
        source_id: uuid.UUID | None,
        user_id: uuid.UUID,
        parsed: ParsedDocument,
    ) -> int:
        if not parsed.content.strip():
            return 0

        text_chunks = self._chunker.chunk_text(
            parsed.content, filename=parsed.filename, file_path=parsed.file_path
        )
        if not text_chunks:
            return 0

        texts = [c.content for c in text_chunks]
        embeddings = await self._embeddings.embed_batch(texts)

        doc = await self._repo.upsert_document(
            space_id=space_id,
            source_id=source_id,
            user_id=user_id,
            filename=parsed.filename,
            file_path=parsed.file_path,
            mime_type=parsed.mime_type,
            content_hash=parsed.content_hash,
            file_size=parsed.file_size,
            chunk_count=len(text_chunks),
            metadata={**parsed.metadata, "mime_type": parsed.mime_type},
        )

        chunk_data = [
            (c.content, c.chunk_index, c.metadata, emb)
            for c, emb in zip(text_chunks, embeddings, strict=True)
        ]
        return await self._repo.store_chunks(doc.id, space_id, user_id, chunk_data)

    async def check_source_changes(self, source_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Returns True if changes detected and re-ingestion triggered."""
        source = await self._repo.get_source(source_id, user_id)
        if not source or not source.watch_enabled:
            return False

        if source.source_type == SourceType.LOCAL_FOLDER.value:
            return await self._check_local_changes(source)
        if source.source_type == SourceType.GITHUB.value:
            return await self._check_github_changes(source, user_id)
        if source.source_type in (SourceType.NOTION.value, SourceType.GOOGLE_DRIVE.value):
            await self.ingest_source(source.id, user_id)
            return True
        return False

    async def _check_local_changes(self, source) -> bool:
        root_path = source.config.get("path", "")
        if not root_path:
            return False

        cursor = source.sync_cursor or {}
        cursor_files = cursor.get("files", {})
        changed = False

        for abs_path in self._local.list_files(root_path):
            rel_path = str(Path(abs_path).relative_to(Path(root_path).resolve())).replace("\\", "/")
            mtime = self._local.get_file_mtime(abs_path)
            prev = cursor_files.get(rel_path, {})
            if prev.get("mtime") != mtime:
                changed = True
                break

        if changed:
            await self.ingest_source(source.id, source.user_id)
        return changed

    async def _check_github_changes(self, source, user_id: uuid.UUID) -> bool:
        config = source.config
        repo = config.get("repo", "")
        branch = config.get("branch", "main")
        owner, repo_name = self._github.parse_repo_url(repo)
        file_list = await self._github.list_files(owner, repo_name, branch=branch)
        cursor_files = (source.sync_cursor or {}).get("files", {})
        changed = False

        for item in file_list:
            prev = cursor_files.get(item["path"], {})
            if prev.get("sha") != item.get("sha"):
                changed = True
                break

        if changed:
            await self.ingest_source(source.id, user_id)
        return changed
