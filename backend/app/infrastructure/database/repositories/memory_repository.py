import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import MemoryEntity, MemoryTier
from app.infrastructure.database.models import MemoryModel, MemoryTagModel, TagModel


def _to_entity(model: MemoryModel, tags: list[str] | None = None) -> MemoryEntity:
    return MemoryEntity(
        id=model.id,
        user_id=model.user_id,
        project_id=model.project_id,
        tier=MemoryTier(model.tier),
        category=model.category,
        content=model.content,
        summary=model.summary,
        importance=model.importance,
        source_type=model.source_type,
        source_id=model.source_id,
        metadata=model.metadata_ or {},
        tags=tags or [],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_tags(self, memory_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(TagModel.name)
            .join(MemoryTagModel, MemoryTagModel.tag_id == TagModel.id)
            .where(MemoryTagModel.memory_id == memory_id)
        )
        return list(result.scalars().all())

    async def _sync_tags(self, memory_id: uuid.UUID, tags: list[str]) -> None:
        await self._session.execute(delete(MemoryTagModel).where(MemoryTagModel.memory_id == memory_id))
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            result = await self._session.execute(select(TagModel).where(TagModel.name == tag_name))
            tag = result.scalar_one_or_none()
            if not tag:
                tag = TagModel(name=tag_name)
                self._session.add(tag)
                await self._session.flush()
            self._session.add(MemoryTagModel(memory_id=memory_id, tag_id=tag.id))

    async def create(self, memory: MemoryEntity, embedding: list[float] | None = None) -> MemoryEntity:
        model = MemoryModel(
            id=memory.id or uuid.uuid4(),
            user_id=memory.user_id,
            project_id=memory.project_id,
            tier=memory.tier.value,
            category=memory.category,
            content=memory.content,
            summary=memory.summary,
            importance=memory.importance,
            embedding=embedding,
            source_type=memory.source_type,
            source_id=memory.source_id,
            metadata_=memory.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        if memory.tags:
            await self._sync_tags(model.id, memory.tags)
        await self._session.execute(
            text(
                "UPDATE memories SET search_vector = to_tsvector('english', coalesce(summary, '') || ' ' || content) "
                "WHERE id = :id"
            ),
            {"id": model.id},
        )
        return _to_entity(model, memory.tags)

    async def get_by_id(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> MemoryEntity | None:
        result = await self._session.execute(
            select(MemoryModel).where(MemoryModel.id == memory_id, MemoryModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        tags = await self._get_tags(model.id)
        return _to_entity(model, tags)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        tier: MemoryTier | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MemoryEntity], int]:
        query = select(MemoryModel).where(MemoryModel.user_id == user_id)
        count_query = select(func.count()).select_from(MemoryModel).where(MemoryModel.user_id == user_id)
        if tier:
            query = query.where(MemoryModel.tier == tier.value)
            count_query = count_query.where(MemoryModel.tier == tier.value)
        if category:
            query = query.where(MemoryModel.category == category)
            count_query = count_query.where(MemoryModel.category == category)
        query = query.order_by(MemoryModel.importance.desc(), MemoryModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        models = result.scalars().all()
        total = (await self._session.execute(count_query)).scalar() or 0
        entities = []
        for model in models:
            tags = await self._get_tags(model.id)
            entities.append(_to_entity(model, tags))
        return entities, total

    async def update(self, memory: MemoryEntity) -> MemoryEntity:
        await self._session.execute(
            update(MemoryModel)
            .where(MemoryModel.id == memory.id, MemoryModel.user_id == memory.user_id)
            .values(
                tier=memory.tier.value,
                category=memory.category,
                content=memory.content,
                summary=memory.summary,
                importance=memory.importance,
                metadata_=memory.metadata,
                updated_at=datetime.now(UTC),
            )
        )
        await self._sync_tags(memory.id, memory.tags)
        await self._session.execute(
            text(
                "UPDATE memories SET search_vector = to_tsvector('english', coalesce(summary, '') || ' ' || content) "
                "WHERE id = :id"
            ),
            {"id": memory.id},
        )
        updated = await self.get_by_id(memory.id, memory.user_id)
        assert updated is not None
        return updated

    async def delete(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(MemoryModel).where(MemoryModel.id == memory_id, MemoryModel.user_id == user_id)
        )
        return result.rowcount > 0

    async def semantic_search(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        *,
        limit: int = 10,
        tiers: list[MemoryTier] | None = None,
        min_importance: float = 0.0,
    ) -> list[tuple[MemoryEntity, float]]:
        tier_filter = ""
        params: dict = {
            "user_id": user_id,
            "query_embedding": query_embedding,
            "limit": limit,
            "min_importance": min_importance,
        }
        if tiers:
            tier_values = [t.value for t in tiers]
            tier_filter = "AND tier = ANY(:tiers)"
            params["tiers"] = tier_values

        sql = text(f"""
            SELECT id, 1 - (embedding <=> :query_embedding) AS score
            FROM memories
            WHERE user_id = :user_id
              AND embedding IS NOT NULL
              AND importance >= :min_importance
              {tier_filter}
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """)
        result = await self._session.execute(sql, params)
        rows = result.fetchall()
        entities_with_scores = []
        for row in rows:
            entity = await self.get_by_id(row.id, user_id)
            if entity:
                entities_with_scores.append((entity, float(row.score)))
        return entities_with_scores

    async def full_text_search(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        limit: int = 10,
    ) -> list[tuple[MemoryEntity, float]]:
        sanitized = re.sub(r"[^\w\s]", " ", query)
        ts_query = " & ".join(sanitized.split())
        if not ts_query:
            return []
        sql = text("""
            SELECT id, ts_rank(search_vector, to_tsquery('english', :query)) AS score
            FROM memories
            WHERE user_id = :user_id
              AND search_vector @@ to_tsquery('english', :query)
            ORDER BY score DESC
            LIMIT :limit
        """)
        try:
            result = await self._session.execute(sql, {"user_id": user_id, "query": ts_query, "limit": limit})
        except Exception:
            return []
        rows = result.fetchall()
        entities_with_scores = []
        for row in rows:
            entity = await self.get_by_id(row.id, user_id)
            if entity:
                entities_with_scores.append((entity, float(row.score)))
        return entities_with_scores
