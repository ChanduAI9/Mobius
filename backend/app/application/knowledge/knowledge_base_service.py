import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.knowledge.ingestion_service import IngestionService
from app.application.knowledge.rag_service import RAGService
from app.application.memory.memory_service import MemoryService
from app.infrastructure.database.repositories.document_repository import DocumentRepository


class KnowledgeBaseService:
    def __init__(self, session: AsyncSession, memory_service: MemoryService | None = None) -> None:
        self._session = session
        self._repo = DocumentRepository(session)
        self._ingestion = IngestionService(session)
        self._rag = RAGService(session, memory_service)

    async def create_space(
        self,
        user_id: uuid.UUID,
        name: str,
        description: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> dict:
        space = await self._repo.create_space(user_id, name, description, project_id)
        return self._space_dict(space)

    async def list_spaces(self, user_id: uuid.UUID, project_id: uuid.UUID | None = None) -> list[dict]:
        spaces = await self._repo.list_spaces(user_id, project_id)
        result = []
        for space in spaces:
            stats = await self._repo.get_space_stats(space.id)
            result.append({**self._space_dict(space), **stats})
        return result

    async def get_space(self, space_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            return None
        stats = await self._repo.get_space_stats(space.id)
        sources = await self._repo.list_sources(space_id, user_id)
        return {
            **self._space_dict(space),
            **stats,
            "sources": [self._source_dict(s) for s in sources],
        }

    async def add_local_source(
        self,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        path: str,
        watch_enabled: bool = True,
    ) -> dict:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            raise ValueError("Knowledge space not found")

        source = await self._repo.create_source(
            space_id=space_id,
            user_id=user_id,
            source_type="local_folder",
            name=name,
            config={"path": path},
            watch_enabled=watch_enabled,
        )
        return self._source_dict(source)

    async def add_github_source(
        self,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        repo: str,
        branch: str = "main",
        path: str = "",
        watch_enabled: bool = True,
    ) -> dict:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            raise ValueError("Knowledge space not found")

        source = await self._repo.create_source(
            space_id=space_id,
            user_id=user_id,
            source_type="github",
            name=name,
            config={"repo": repo, "branch": branch, "path": path},
            watch_enabled=watch_enabled,
        )
        return self._source_dict(source)

    async def add_notion_source(
        self,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        *,
        token: str | None = None,
        database_id: str | None = None,
        page_ids: list[str] | None = None,
        watch_enabled: bool = True,
    ) -> dict:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            raise ValueError("Knowledge space not found")
        config: dict = {}
        if token:
            config["token"] = token
        if database_id:
            config["database_id"] = database_id
        if page_ids:
            config["page_ids"] = page_ids
        source = await self._repo.create_source(
            space_id=space_id, user_id=user_id, source_type="notion",
            name=name, config=config, watch_enabled=watch_enabled,
        )
        return self._source_dict(source)

    async def add_gdrive_source(
        self,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        *,
        access_token: str | None = None,
        folder_id: str = "root",
        watch_enabled: bool = True,
    ) -> dict:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            raise ValueError("Knowledge space not found")
        config: dict = {"folder_id": folder_id}
        if access_token:
            config["access_token"] = access_token
        source = await self._repo.create_source(
            space_id=space_id, user_id=user_id, source_type="google_drive",
            name=name, config=config, watch_enabled=watch_enabled,
        )
        return self._source_dict(source)

    async def trigger_ingestion(self, source_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        return await self._ingestion.ingest_source(source_id, user_id)

    async def upload_document(
        self, space_id: uuid.UUID, user_id: uuid.UUID, filename: str, data: bytes
    ) -> dict:
        return await self._ingestion.ingest_upload(space_id, user_id, filename, data)

    async def list_documents(self, space_id: uuid.UUID, user_id: uuid.UUID) -> list[dict]:
        space = await self._repo.get_space(space_id, user_id)
        if not space:
            raise ValueError("Knowledge space not found")
        docs = await self._repo.list_documents(space_id, user_id)
        return [self._document_dict(d) for d in docs]

    async def search(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        space_id: uuid.UUID | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        space_ids = [space_id] if space_id else None
        results = await self._rag.retrieve(
            user_id,
            query,
            space_ids=space_ids,
            conversation_context=conversation_context,
            limit=limit,
        )
        return [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "space_id": r.space_id,
                "filename": r.filename,
                "file_path": r.file_path,
                "content": r.content[:500],
                "score": round(r.score, 4),
                "metadata": r.metadata,
            }
            for r in results
        ]

    async def get_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        job = await self._repo.get_job(job_id, user_id)
        if not job:
            return None
        return self._job_dict(job)

    @staticmethod
    def _space_dict(space) -> dict:
        return {
            "id": str(space.id),
            "name": space.name,
            "description": space.description,
            "project_id": str(space.project_id) if space.project_id else None,
            "status": space.status,
            "created_at": space.created_at.isoformat(),
            "updated_at": space.updated_at.isoformat(),
        }

    @staticmethod
    def _source_dict(source) -> dict:
        return {
            "id": str(source.id),
            "space_id": str(source.space_id),
            "source_type": source.source_type,
            "name": source.name,
            "config": source.config,
            "status": source.status,
            "watch_enabled": source.watch_enabled,
            "last_synced_at": source.last_synced_at.isoformat() if source.last_synced_at else None,
            "created_at": source.created_at.isoformat(),
        }

    @staticmethod
    def _document_dict(doc) -> dict:
        return {
            "id": str(doc.id),
            "filename": doc.filename,
            "file_path": doc.file_path,
            "mime_type": doc.mime_type,
            "chunk_count": doc.chunk_count,
            "file_size": doc.file_size,
            "content_hash": doc.content_hash,
            "updated_at": doc.updated_at.isoformat(),
        }

    @staticmethod
    def _job_dict(job) -> dict:
        return {
            "id": str(job.id),
            "space_id": str(job.space_id),
            "source_id": str(job.source_id) if job.source_id else None,
            "status": job.status,
            "progress": job.progress,
            "files_processed": job.files_processed,
            "chunks_created": job.chunks_created,
            "error": job.error,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
