import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.memory.memory_service import MemoryService
from app.config import settings
from app.domain.knowledge import RetrievalResult
from app.infrastructure.database.repositories.document_repository import DocumentRepository
from app.infrastructure.embeddings.sentence_transformer import get_embedding_service


class RAGService:
    """Hybrid retrieval-augmented generation with conversation-aware query expansion."""

    def __init__(self, session: AsyncSession, memory_service: MemoryService | None = None) -> None:
        self._repo = DocumentRepository(session)
        self._embeddings = get_embedding_service()
        self._memory = memory_service

    async def retrieve(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        space_ids: list[uuid.UUID] | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        limit: int | None = None,
        include_memories: bool = True,
    ) -> list[RetrievalResult]:
        expanded_query = self._expand_query(query, conversation_context)
        embedding = await self._embeddings.embed(expanded_query)

        results = await self._repo.hybrid_search(
            user_id,
            embedding,
            expanded_query,
            space_ids=space_ids,
            limit=limit or settings.rag_top_k,
        )

        if include_memories and self._memory:
            memory_results = await self._memory.search(user_id, expanded_query, limit=3)
            for entity, score in memory_results:
                results.append(
                    RetrievalResult(
                        chunk_id=f"memory-{entity.id}",
                        document_id=str(entity.id),
                        space_id="memory",
                        content=entity.content,
                        filename=f"memory:{entity.category}",
                        file_path="memory",
                        score=score * 0.5,
                        metadata={"type": "memory", "tier": entity.tier.value},
                    )
                )
            results.sort(key=lambda r: r.score, reverse=True)
            results = results[: limit or settings.rag_top_k]

        return results

    def format_context(self, results: list[RetrievalResult]) -> str:
        if not results:
            return ""
        blocks = []
        for r in results:
            header = f"[{r.filename} — {r.file_path}]"
            blocks.append(f"{header}\n{r.content}")
        return "\n\n---\n\n".join(blocks)

    @staticmethod
    def _expand_query(query: str, conversation_context: list[dict[str, str]] | None) -> str:
        if not conversation_context:
            return query
        recent = conversation_context[-3:]
        context_parts = [m["content"][:200] for m in recent if m.get("role") == "user"]
        if context_parts:
            return f"{' '.join(context_parts)} {query}"
        return query
