import uuid

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.knowledge.knowledge_base_service import KnowledgeBaseService
from app.application.memory.memory_service import MemoryService
from app.infrastructure.database.models import ConversationModel, IdeaModel, MessageModel


class SearchService:
    def __init__(self, session: AsyncSession, memory_service: MemoryService) -> None:
        self._session = session
        self._memory = memory_service
        self._knowledge = KnowledgeBaseService(session, memory_service)

    async def search(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        types: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        search_types = types or ["memories", "ideas", "conversations", "knowledge"]
        results: list[dict] = []

        if "memories" in search_types:
            memory_results = await self._memory.search(user_id, query, limit=limit)
            for entity, score in memory_results:
                results.append({
                    "type": "memory",
                    "id": str(entity.id),
                    "title": entity.category,
                    "snippet": entity.summary or entity.content[:200],
                    "score": round(score, 3),
                })

        if "ideas" in search_types:
            idea_results = await self._session.execute(
                select(IdeaModel)
                .where(
                    IdeaModel.user_id == user_id,
                    or_(
                        IdeaModel.raw_input.ilike(f"%{query}%"),
                        IdeaModel.summary.ilike(f"%{query}%"),
                    ),
                )
                .limit(limit)
            )
            for idea in idea_results.scalars().all():
                results.append({
                    "type": "idea",
                    "id": str(idea.id),
                    "title": idea.summary or "Untitled idea",
                    "snippet": idea.raw_input[:200],
                    "score": 0.5,
                })

        if "conversations" in search_types:
            conv_sql = text("""
                SELECT c.id, c.title, m.content,
                       ts_rank(to_tsvector('english', m.content), plainto_tsquery('english', :query)) AS score
                FROM conversations c
                JOIN messages m ON m.conversation_id = c.id
                WHERE c.user_id = :user_id
                  AND to_tsvector('english', m.content) @@ plainto_tsquery('english', :query)
                ORDER BY score DESC
                LIMIT :limit
            """)
            try:
                conv_results = await self._session.execute(
                    conv_sql, {"user_id": user_id, "query": query, "limit": limit}
                )
                for row in conv_results.fetchall():
                    results.append({
                        "type": "conversation",
                        "id": str(row.id),
                        "title": row.title,
                        "snippet": row.content[:200],
                        "score": round(float(row.score), 3),
                    })
            except Exception:
                fallback = await self._session.execute(
                    select(ConversationModel, MessageModel)
                    .join(MessageModel, MessageModel.conversation_id == ConversationModel.id)
                    .where(
                        ConversationModel.user_id == user_id,
                        MessageModel.content.ilike(f"%{query}%"),
                    )
                    .limit(limit)
                )
                for conv, msg in fallback.all():
                    results.append({
                        "type": "conversation",
                        "id": str(conv.id),
                        "title": conv.title,
                        "snippet": msg.content[:200],
                        "score": 0.4,
                    })

        if "knowledge" in search_types:
            kb_results = await self._knowledge.search(user_id, query, limit=limit)
            for item in kb_results:
                results.append({
                    "type": "knowledge",
                    "id": item["chunk_id"],
                    "title": item["filename"],
                    "snippet": item["content"][:200],
                    "score": item["score"],
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
