from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from app.domain.entities import MemoryEntity, MemoryTier


class LLMMessage(dict):
    """Typed dict-like: {"role": "user"|"assistant"|"system", "content": str}"""


class LLMProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str: ...

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]: ...


class EmbeddingService(Protocol):
    async def embed(self, text: str) -> list[float]: ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class MemoryRepository(Protocol):
    async def create(self, memory: MemoryEntity, embedding: list[float] | None = None) -> MemoryEntity: ...

    async def get_by_id(self, memory_id: UUID, user_id: UUID) -> MemoryEntity | None: ...

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        tier: MemoryTier | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MemoryEntity], int]: ...

    async def update(self, memory: MemoryEntity) -> MemoryEntity: ...

    async def delete(self, memory_id: UUID, user_id: UUID) -> bool: ...

    async def semantic_search(
        self,
        user_id: UUID,
        query_embedding: list[float],
        *,
        limit: int = 10,
        tiers: list[MemoryTier] | None = None,
        min_importance: float = 0.0,
    ) -> list[tuple[MemoryEntity, float]]: ...

    async def full_text_search(
        self,
        user_id: UUID,
        query: str,
        *,
        limit: int = 10,
    ) -> list[tuple[MemoryEntity, float]]: ...
