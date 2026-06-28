import re
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import MemoryEntity, MemoryTier
from app.infrastructure.database.repositories.memory_repository import SQLMemoryRepository
from app.infrastructure.embeddings.sentence_transformer import get_embedding_service


class MemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SQLMemoryRepository(session)
        self._embeddings = get_embedding_service()
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        content: str,
        *,
        category: str = "general",
        tier: MemoryTier = MemoryTier.LONG_TERM,
        importance: float = 0.5,
        tags: list[str] | None = None,
        project_id: uuid.UUID | None = None,
        summary: str | None = None,
        source_type: str | None = None,
        source_id: uuid.UUID | None = None,
    ) -> MemoryEntity:
        embedding = await self._embeddings.embed(content)
        memory = MemoryEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            project_id=project_id,
            tier=tier,
            category=category,
            content=content,
            summary=summary,
            importance=min(max(importance, 0.0), 1.0),
            tags=tags or [],
            source_type=source_type,
            source_id=source_id,
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self._repo.create(memory, embedding)

    async def get(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> MemoryEntity | None:
        return await self._repo.get_by_id(memory_id, user_id)

    async def list_memories(
        self,
        user_id: uuid.UUID,
        *,
        tier: MemoryTier | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MemoryEntity], int]:
        return await self._repo.list_for_user(user_id, tier=tier, category=category, limit=limit, offset=offset)

    async def update(self, memory_id: uuid.UUID, user_id: uuid.UUID, **updates) -> MemoryEntity | None:
        memory = await self._repo.get_by_id(memory_id, user_id)
        if not memory:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(memory, key):
                setattr(memory, key, value)
        memory.updated_at = datetime.now(UTC)
        return await self._repo.update(memory)

    async def delete(self, memory_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return await self._repo.delete(memory_id, user_id)

    async def search(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        limit: int = 10,
        tiers: list[MemoryTier] | None = None,
        min_importance: float = 0.0,
    ) -> list[tuple[MemoryEntity, float]]:
        embedding = await self._embeddings.embed(query)
        semantic = await self._repo.semantic_search(
            user_id, embedding, limit=limit, tiers=tiers, min_importance=min_importance
        )
        fulltext = await self._repo.full_text_search(user_id, query, limit=limit)

        combined: dict[uuid.UUID, tuple[MemoryEntity, float]] = {}
        for entity, score in semantic:
            combined[entity.id] = (entity, score * 0.7)
        for entity, score in fulltext:
            if entity.id in combined:
                existing_entity, existing_score = combined[entity.id]
                combined[entity.id] = (existing_entity, existing_score + score * 0.3)
            else:
                combined[entity.id] = (entity, score * 0.3)

        ranked = sorted(combined.values(), key=lambda x: x[1], reverse=True)
        return ranked[:limit]

    async def retrieve_relevant(
        self, user_id: uuid.UUID, query: str, limit: int = 5
    ) -> list[MemoryEntity]:
        results = await self.search(
            user_id,
            query,
            limit=limit,
            tiers=[MemoryTier.LONG_TERM, MemoryTier.SEMANTIC, MemoryTier.PROJECT, MemoryTier.REFLECTION],
            min_importance=0.3,
        )
        return [entity for entity, _ in results]

    async def extract_from_conversation(
        self,
        user_id: uuid.UUID,
        user_message: str,
        assistant_message: str,
        conversation_id: uuid.UUID,
    ) -> None:
        """Extract storable memories from conversation when patterns detected."""
        patterns = [
            (r"(?:remember|note that|don't forget)\s+(?:that\s+)?(.+)", "preference", 0.7),
            (r"(?:my preference is|i prefer|i like to)\s+(.+)", "preference", 0.8),
            (r"(?:project|working on|building)\s+(?:called\s+)?([A-Z][\w\s]+)", "project", 0.6),
        ]
        for pattern, category, importance in patterns:
            for text in [user_message, assistant_message]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    content = match.group(1).strip()[:500]
                    if len(content) > 10:
                        await self.create(
                            user_id,
                            content,
                            category=category,
                            tier=MemoryTier.SHORT_TERM if importance < 0.7 else MemoryTier.LONG_TERM,
                            importance=importance,
                            source_type="conversation",
                            source_id=conversation_id,
                        )

        await self.create(
            user_id,
            f"User asked: {user_message[:200]}",
            category="conversation",
            tier=MemoryTier.WORKING,
            importance=0.3,
            source_type="conversation",
            source_id=conversation_id,
        )
