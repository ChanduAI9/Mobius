from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from app.application.agents.architecture_agent import ArchitectureAgent
from app.application.agents.base_agent import AgentResponse, BaseAgent
from app.application.agents.coding_agent import CodingAgent
from app.application.agents.research_agent import ResearchAgent
from app.application.knowledge.rag_service import RAGService
from app.application.memory.memory_service import MemoryService
from app.application.research.research_service import ResearchService
from app.domain.knowledge import AgentType

if TYPE_CHECKING:
    from app.application.tools.tool_orchestrator import ToolOrchestrator


class Orchestrator:
    """Routes requests to specialized agents based on intent detection."""

    CODING_PATTERNS = [
        r"\b(write|implement|fix|debug|refactor|review)\b.*\b(code|function|class|module|bug|test)\b",
        r"\b(python|typescript|javascript|react|fastapi|sql|docker|git)\b",
        r"\bhow (?:do|to) (?:i )?(?:implement|write|fix|create)\b",
        r"```",
        r"\b(pull request|pr review|code review)\b",
    ]

    ARCHITECTURE_PATTERNS = [
        r"\b(architect|architecture|system design|microservice|scalab|infrastructure)\b",
        r"\b(database|cache|queue|event.?driven|api design|cloud)\b",
        r"\b(c4 diagram|sequence diagram|mermaid|diagram)\b",
        r"\b(trade.?offs?|availability|latency|throughput|cap theorem)\b",
        r"\breview (?:my|this|the) (?:design|architecture|system)\b",
    ]

    RESEARCH_PATTERNS = [
        r"\b(research|investigate|analyze|compare|competitor|market)\b",
        r"\b(summarize|explain|what is|how does)\b.*\b(paper|article|technology|tool|framework)\b",
        r"\b(documentation|paper|article|docs|study|report)\b",
        r"\bvs\.?\b|\bversus\b|\bcompare\b",
    ]

    def __init__(
        self,
        rag_service: RAGService,
        memory_service: MemoryService,
        research_service: ResearchService | None = None,
    ) -> None:
        self._rag = rag_service
        self._memory = memory_service
        self._research_service = research_service
        self._agents: dict[AgentType, BaseAgent] = {
            AgentType.CONVERSATION: BaseAgent(rag_service),
            AgentType.CODING: CodingAgent(rag_service),
            AgentType.ARCHITECTURE: ArchitectureAgent(rag_service),
            AgentType.RESEARCH: ResearchAgent(rag_service, research_service),
        }

    def classify_intent(self, message: str, agent_override: str | None = None) -> AgentType:
        if agent_override:
            try:
                return AgentType(agent_override)
            except ValueError:
                pass

        msg_lower = message.lower()
        for pattern in self.ARCHITECTURE_PATTERNS:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return AgentType.ARCHITECTURE
        for pattern in self.CODING_PATTERNS:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return AgentType.CODING
        for pattern in self.RESEARCH_PATTERNS:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return AgentType.RESEARCH
        return AgentType.CONVERSATION

    async def process(
        self,
        user_id: uuid.UUID,
        messages: list[dict[str, str]],
        *,
        agent_override: str | None = None,
        space_ids: list[uuid.UUID] | None = None,
        tool_orchestrator: ToolOrchestrator | None = None,
    ) -> AgentResponse:
        query = messages[-1]["content"] if messages else ""

        if tool_orchestrator and tool_orchestrator.needs_tool_orchestration(query):
            result = await tool_orchestrator.execute(user_id, query, space_ids=space_ids)
            return AgentResponse(
                content=result.final_response,
                agent="tool_orchestrator",
                context_used=True,
                metadata={"plan": [s.tool.value for s in result.plan]},
            )

        agent_type = self.classify_intent(query, agent_override)
        agent = self._agents[agent_type]
        memories = await self._memory.retrieve_relevant(user_id, query, limit=5)
        return await agent.run(
            user_id,
            messages,
            space_ids=space_ids,
            conversation_context=messages[:-1],
            extra_memories=memories,
        )

    async def stream(
        self,
        user_id: uuid.UUID,
        messages: list[dict[str, str]],
        *,
        agent_override: str | None = None,
        space_ids: list[uuid.UUID] | None = None,
        tool_orchestrator: ToolOrchestrator | None = None,
    ) -> AsyncIterator[str]:
        query = messages[-1]["content"] if messages else ""

        if tool_orchestrator and tool_orchestrator.needs_tool_orchestration(query):
            result = await tool_orchestrator.execute(user_id, query, space_ids=space_ids)
            yield result.final_response
            return

        agent_type = self.classify_intent(query, agent_override)
        agent = self._agents[agent_type]
        memories = await self._memory.retrieve_relevant(user_id, query, limit=5)
        async for token in agent.stream(
            user_id,
            messages,
            space_ids=space_ids,
            conversation_context=messages[:-1],
            extra_memories=memories,
        ):
            yield token

    def get_agent_for_message(self, message: str, agent_override: str | None = None) -> str:
        return self.classify_intent(message, agent_override).value
