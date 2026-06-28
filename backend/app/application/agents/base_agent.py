import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.application.conversation.prompts import MOBIUS_SYSTEM_PROMPT
from app.application.knowledge.rag_service import RAGService
from app.domain.knowledge import AgentType
from app.infrastructure.ai.provider_registry import llm_registry


@dataclass
class AgentResponse:
    content: str
    agent: str
    context_used: bool = False
    metadata: dict | None = None


class BaseAgent:
    agent_type: AgentType = AgentType.CONVERSATION

    def __init__(self, rag_service: RAGService | None = None) -> None:
        self._rag = rag_service

    @property
    def system_prompt(self) -> str:
        return MOBIUS_SYSTEM_PROMPT

    async def build_system_prompt(
        self,
        user_id,
        query: str,
        *,
        space_ids: list | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        extra_memories: list | None = None,
    ) -> str:
        parts = [self.system_prompt]
        if self._rag:
            results = await self._rag.retrieve(
                user_id,
                query,
                space_ids=space_ids,
                conversation_context=conversation_context,
                limit=8,
            )
            if results:
                context = self._rag.format_context(results)
                parts.append(f"\nRelevant knowledge base context:\n{context}")
        if extra_memories:
            memory_block = "\n".join(f"- [{m.category}] {m.content}" for m in extra_memories)
            parts.append(f"\nRelevant memories:\n{memory_block}")
        return "\n".join(parts)

    async def run(
        self,
        user_id,
        messages: list[dict[str, str]],
        *,
        space_ids: list | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        extra_memories: list | None = None,
    ) -> AgentResponse:
        query = messages[-1]["content"] if messages else ""
        system = await self.build_system_prompt(
            user_id, query,
            space_ids=space_ids,
            conversation_context=conversation_context,
            extra_memories=extra_memories,
        )
        provider = llm_registry.get_with_fallback()
        content = await provider.complete(messages, system=system)
        return AgentResponse(content=content, agent=self.agent_type.value, context_used=bool(self._rag))

    async def stream(
        self,
        user_id,
        messages: list[dict[str, str]],
        *,
        space_ids: list | None = None,
        conversation_context: list[dict[str, str]] | None = None,
        extra_memories: list | None = None,
    ) -> AsyncIterator[str]:
        query = messages[-1]["content"] if messages else ""
        system = await self.build_system_prompt(
            user_id, query,
            space_ids=space_ids,
            conversation_context=conversation_context,
            extra_memories=extra_memories,
        )
        provider = llm_registry.get_with_fallback()
        async for token in provider.stream(messages, system=system):
            yield token
