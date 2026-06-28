import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domain.knowledge import RetrievalResult
from app.infrastructure.database.models import (
    DocumentChunkModel,
    DocumentModel,
    IngestionJobModel,
    KnowledgeSourceModel,
    KnowledgeSpaceModel,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_space(self, space_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeSpaceModel | None:
        result = await self._session.execute(
            select(KnowledgeSpaceModel).where(
                KnowledgeSpaceModel.id == space_id, KnowledgeSpaceModel.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_spaces(self, user_id: uuid.UUID, project_id: uuid.UUID | None = None) -> list[KnowledgeSpaceModel]:
        query = select(KnowledgeSpaceModel).where(KnowledgeSpaceModel.user_id == user_id)
        if project_id:
            query = query.where(KnowledgeSpaceModel.project_id == project_id)
        query = query.order_by(KnowledgeSpaceModel.updated_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create_space(
        self, user_id: uuid.UUID, name: str, description: str | None = None, project_id: uuid.UUID | None = None
    ) -> KnowledgeSpaceModel:
        space = KnowledgeSpaceModel(
            user_id=user_id, name=name, description=description, project_id=project_id
        )
        self._session.add(space)
        await self._session.flush()
        return space

    async def get_source(self, source_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeSourceModel | None:
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(
                KnowledgeSourceModel.id == source_id, KnowledgeSourceModel.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_sources(self, space_id: uuid.UUID, user_id: uuid.UUID) -> list[KnowledgeSourceModel]:
        result = await self._session.execute(
            select(KnowledgeSourceModel)
            .where(KnowledgeSourceModel.space_id == space_id, KnowledgeSourceModel.user_id == user_id)
            .order_by(KnowledgeSourceModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_source(
        self,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        source_type: str,
        name: str,
        config: dict,
        watch_enabled: bool = True,
    ) -> KnowledgeSourceModel:
        source = KnowledgeSourceModel(
            space_id=space_id,
            user_id=user_id,
            source_type=source_type,
            name=name,
            config=config,
            watch_enabled=watch_enabled,
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def get_document_by_path(
        self, space_id: uuid.UUID, file_path: str
    ) -> DocumentModel | None:
        result = await self._session.execute(
            select(DocumentModel).where(
                DocumentModel.space_id == space_id, DocumentModel.file_path == file_path
            )
        )
        return result.scalar_one_or_none()

    async def upsert_document(
        self,
        *,
        space_id: uuid.UUID,
        source_id: uuid.UUID | None,
        user_id: uuid.UUID,
        filename: str,
        file_path: str,
        mime_type: str,
        content_hash: str,
        file_size: int,
        chunk_count: int,
        metadata: dict,
    ) -> DocumentModel:
        existing = await self.get_document_by_path(space_id, file_path)
        if existing:
            existing.filename = filename
            existing.content_hash = content_hash
            existing.file_size = file_size
            existing.chunk_count = chunk_count
            existing.mime_type = mime_type
            existing.metadata_ = metadata
            existing.updated_at = datetime.now(UTC)
            await self._session.execute(
                delete(DocumentChunkModel).where(DocumentChunkModel.document_id == existing.id)
            )
            await self._session.flush()
            return existing

        doc = DocumentModel(
            space_id=space_id,
            source_id=source_id,
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            mime_type=mime_type,
            content_hash=content_hash,
            file_size=file_size,
            chunk_count=chunk_count,
            metadata_=metadata,
        )
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def store_chunks(
        self,
        document_id: uuid.UUID,
        space_id: uuid.UUID,
        user_id: uuid.UUID,
        chunks: list[tuple[str, int, dict, list[float]]],
    ) -> int:
        for content, index, metadata, embedding in chunks:
            chunk = DocumentChunkModel(
                document_id=document_id,
                space_id=space_id,
                user_id=user_id,
                chunk_index=index,
                content=content,
                embedding=embedding,
                metadata_=metadata,
            )
            self._session.add(chunk)
        await self._session.flush()

        for content, index, metadata, embedding in chunks:
            await self._session.execute(
                text(
                    "UPDATE document_chunks SET search_vector = to_tsvector('english', content) "
                    "WHERE document_id = :doc_id AND chunk_index = :idx"
                ),
                {"doc_id": document_id, "idx": index},
            )
        return len(chunks)

    async def list_documents(self, space_id: uuid.UUID, user_id: uuid.UUID) -> list[DocumentModel]:
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.space_id == space_id, DocumentModel.user_id == user_id)
            .order_by(DocumentModel.updated_at.desc())
        )
        return list(result.scalars().all())

    async def hybrid_search(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        query_text: str,
        *,
        space_ids: list[uuid.UUID] | None = None,
        limit: int = 10,
    ) -> list[RetrievalResult]:
        space_filter = ""
        params: dict = {
            "user_id": user_id,
            "query_embedding": query_embedding,
            "limit": limit * 2,
        }
        if space_ids:
            space_filter = "AND dc.space_id = ANY(:space_ids)"
            params["space_ids"] = space_ids

        vector_sql = text(f"""
            SELECT dc.id, dc.document_id, dc.space_id, dc.content, dc.metadata,
                   d.filename, d.file_path,
                   1 - (dc.embedding <=> :query_embedding) AS score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE dc.user_id = :user_id
              AND dc.embedding IS NOT NULL
              {space_filter}
            ORDER BY dc.embedding <=> :query_embedding
            LIMIT :limit
        """)
        vector_results = await self._session.execute(vector_sql, params)
        vector_rows = vector_results.fetchall()

        keyword_results: list = []
        sanitized = re.sub(r"[^\w\s]", " ", query_text)
        ts_query = " & ".join(sanitized.split())
        if ts_query:
            kw_params = {"user_id": user_id, "query": ts_query, "limit": limit * 2}
            if space_ids:
                kw_params["space_ids"] = space_ids
            keyword_sql = text(f"""
                SELECT dc.id, dc.document_id, dc.space_id, dc.content, dc.metadata,
                       d.filename, d.file_path,
                       ts_rank(dc.search_vector, to_tsquery('english', :query)) AS score
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE dc.user_id = :user_id
                  AND dc.search_vector @@ to_tsquery('english', :query)
                  {space_filter}
                ORDER BY score DESC
                LIMIT :limit
            """)
            try:
                kw_res = await self._session.execute(keyword_sql, kw_params)
                keyword_results = kw_res.fetchall()
            except Exception:
                keyword_results = []

        combined: dict[uuid.UUID, RetrievalResult] = {}
        vw = settings.hybrid_vector_weight
        kw = settings.hybrid_keyword_weight

        for row in vector_rows:
            combined[row.id] = RetrievalResult(
                chunk_id=str(row.id),
                document_id=str(row.document_id),
                space_id=str(row.space_id),
                content=row.content,
                filename=row.filename,
                file_path=row.file_path,
                score=float(row.score) * vw,
                metadata=row.metadata or {},
            )

        for row in keyword_results:
            if row.id in combined:
                combined[row.id].score += float(row.score) * kw
            else:
                combined[row.id] = RetrievalResult(
                    chunk_id=str(row.id),
                    document_id=str(row.document_id),
                    space_id=str(row.space_id),
                    content=row.content,
                    filename=row.filename,
                    file_path=row.file_path,
                    score=float(row.score) * kw,
                    metadata=row.metadata or {},
                )

        ranked = sorted(combined.values(), key=lambda r: r.score, reverse=True)
        return ranked[:limit]

    async def create_job(
        self, space_id: uuid.UUID, user_id: uuid.UUID, source_id: uuid.UUID | None = None
    ) -> IngestionJobModel:
        job = IngestionJobModel(
            space_id=space_id, source_id=source_id, user_id=user_id, status="pending"
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def update_job(self, job_id: uuid.UUID, **kwargs) -> None:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if kwargs:
            await self._session.execute(
                update(IngestionJobModel).where(IngestionJobModel.id == job_id).values(**kwargs)
            )

    async def get_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> IngestionJobModel | None:
        result = await self._session.execute(
            select(IngestionJobModel).where(
                IngestionJobModel.id == job_id, IngestionJobModel.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_watchable_sources(self) -> list[KnowledgeSourceModel]:
        result = await self._session.execute(
            select(KnowledgeSourceModel).where(
                KnowledgeSourceModel.watch_enabled.is_(True),
                KnowledgeSourceModel.status == "active",
            )
        )
        return list(result.scalars().all())

    async def update_source_sync(self, source_id: uuid.UUID, sync_cursor: dict) -> None:
        await self._session.execute(
            update(KnowledgeSourceModel)
            .where(KnowledgeSourceModel.id == source_id)
            .values(last_synced_at=datetime.now(UTC), sync_cursor=sync_cursor)
        )

    async def get_space_stats(self, space_id: uuid.UUID) -> dict:
        doc_count = (
            await self._session.execute(
                select(func.count()).select_from(DocumentModel).where(DocumentModel.space_id == space_id)
            )
        ).scalar() or 0
        chunk_count = (
            await self._session.execute(
                select(func.count()).select_from(DocumentChunkModel).where(DocumentChunkModel.space_id == space_id)
            )
        ).scalar() or 0
        return {"document_count": doc_count, "chunk_count": chunk_count}
