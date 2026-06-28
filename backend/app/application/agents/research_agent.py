from collections.abc import AsyncIterator

from app.application.agents.base_agent import BaseAgent
from app.application.research.research_service import ResearchService
from app.domain.knowledge import AgentType


RESEARCH_SYSTEM_PROMPT = """You are MOBIUS Research Agent — an expert research analyst and knowledge synthesizer.

Capabilities:
- Web research with source citations [1], [2], ...
- Multi-source comparison and synthesis
- Technology evaluation and competitor analysis
- Research paper breakdown (contributions, methodology, limitations)
- Document summarization with key insights

Behaviors:
- Always cite sources when making factual claims
- Present balanced perspectives; note confidence levels
- Distinguish verified facts from reasonable inference
- Structure: Summary → Key Findings → Analysis → Sources
- Challenge unsupported assumptions in the user's question
- Suggest follow-up research when gaps exist

When web/knowledge context is provided, prioritize it over general knowledge."""


class ResearchAgent(BaseAgent):
    agent_type = AgentType.RESEARCH

    def __init__(self, rag_service, research_service: ResearchService | None = None) -> None:
        super().__init__(rag_service)
        self._research = research_service

    @property
    def system_prompt(self) -> str:
        return RESEARCH_SYSTEM_PROMPT

    async def build_system_prompt(
        self,
        user_id,
        query: str,
        *,
        space_ids=None,
        conversation_context=None,
        extra_memories=None,
    ) -> str:
        parts = [self.system_prompt]

        if self._research:
            web_results = await self._research._web.search(query, max_results=6)
            if web_results:
                web_block = "\n".join(
                    f"[{i}] {r.title} ({r.url}): {r.snippet}"
                    for i, r in enumerate(web_results, 1)
                )
                parts.append(f"\nWeb research results:\n{web_block}")

        base_prompt = await super().build_system_prompt(
            user_id, query,
            space_ids=space_ids,
            conversation_context=conversation_context,
            extra_memories=extra_memories,
        )
        parts.append(base_prompt.replace(RESEARCH_SYSTEM_PROMPT, "").strip())
        return "\n".join(p for p in parts if p)
