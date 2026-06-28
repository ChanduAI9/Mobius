import json
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.knowledge.rag_service import RAGService
from app.application.memory.memory_service import MemoryService
from app.application.projects.project_service import ProjectService
from app.application.research.research_service import ResearchService
from app.application.tools.types import OrchestrationResult, PlanStep, ToolName, ToolResult
from app.infrastructure.ai.provider_registry import llm_registry


PLANNING_PROMPT = """Analyze the user request and create a step-by-step tool execution plan.
Return ONLY valid JSON array:
[
  {"step": 1, "tool": "memory_search|knowledge_search|web_search|project_summary|research|store_finding", "query": "...", "reason": "..."}
]

Available tools:
- memory_search: Retrieve user memories and preferences
- knowledge_search: Search indexed documents and repos
- web_search: Search the web for current information
- project_summary: Get project tasks, sprints, milestones status
- research: Deep research with citations (for complex research tasks)
- store_finding: Store important findings to memory (use last)

Use 1-4 steps. Prefer knowledge_search for codebase questions, web_search for current events."""


class ToolRegistry:
    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self._session = session
        self._user_id = user_id
        self._memory = MemoryService(session)
        self._rag = RAGService(session, self._memory)
        self._research = ResearchService(session, self._memory)
        self._projects = ProjectService(session)

    async def execute(self, tool: ToolName, query: str, **kwargs) -> ToolResult:
        handlers = {
            ToolName.MEMORY_SEARCH: self._memory_search,
            ToolName.KNOWLEDGE_SEARCH: self._knowledge_search,
            ToolName.WEB_SEARCH: self._web_search,
            ToolName.PROJECT_SUMMARY: self._project_summary,
            ToolName.RESEARCH: self._research_tool,
            ToolName.STORE_FINDING: self._store_finding,
        }
        handler = handlers.get(tool)
        if not handler:
            return ToolResult(tool=tool.value, success=False, output=f"Unknown tool: {tool}")
        try:
            return await handler(query, **kwargs)
        except Exception as e:
            return ToolResult(tool=tool.value, success=False, output=str(e))

    async def _memory_search(self, query: str, **kwargs) -> ToolResult:
        results = await self._memory.search(self._user_id, query, limit=5)
        if not results:
            return ToolResult(tool="memory_search", success=True, output="No relevant memories found.")
        lines = [f"- [{e.category}] {e.content[:200]} (score: {s:.2f})" for e, s in results]
        return ToolResult(tool="memory_search", success=True, output="\n".join(lines))

    async def _knowledge_search(self, query: str, **kwargs) -> ToolResult:
        space_ids = kwargs.get("space_ids")
        results = await self._rag.retrieve(self._user_id, query, space_ids=space_ids, limit=6)
        if not results:
            return ToolResult(tool="knowledge_search", success=True, output="No knowledge base results.")
        lines = [f"- [{r.filename}] {r.content[:300]}" for r in results]
        return ToolResult(tool="knowledge_search", success=True, output="\n".join(lines))

    async def _web_search(self, query: str, **kwargs) -> ToolResult:
        results = await self._research._web.search(query, max_results=6)
        if not results:
            return ToolResult(tool="web_search", success=True, output="No web results.")
        lines = [f"[{i}] {r.title} ({r.url}): {r.snippet}" for i, r in enumerate(results, 1)]
        return ToolResult(tool="web_search", success=True, output="\n".join(lines))

    async def _project_summary(self, query: str, **kwargs) -> ToolResult:
        project_id = kwargs.get("project_id")
        if project_id:
            summary = await self._projects.get_project_analytics(uuid.UUID(str(project_id)), self._user_id)
        else:
            projects, _ = await self._projects.list_projects(self._user_id, limit=5)
            summary = {"projects": projects}
        return ToolResult(tool="project_summary", success=True, output=json.dumps(summary, default=str))

    async def _research_tool(self, query: str, **kwargs) -> ToolResult:
        finding = await self._research.research(
            self._user_id, query, space_ids=kwargs.get("space_ids"), store_findings=False
        )
        return ToolResult(
            tool="research",
            success=True,
            output=finding.content,
            metadata={"citations": [{"title": c.title, "url": c.url} for c in finding.citations]},
        )

    async def _store_finding(self, query: str, **kwargs) -> ToolResult:
        content = kwargs.get("content", query)
        from app.domain.entities import MemoryTier

        await self._memory.create(
            self._user_id,
            content[:2000],
            category="orchestrator_finding",
            tier=MemoryTier.LONG_TERM,
            importance=0.7,
            tags=["tool_orchestrator"],
        )
        return ToolResult(tool="store_finding", success=True, output="Finding stored in memory.")


class ToolOrchestrator:
    """Multi-step planner coordinating tools, memory, KB, web, and agents."""

    COMPLEX_PATTERNS = [
        r"\b(research|investigate|analyze|compare|comprehensive)\b.*\b(and|with|using)\b",
        r"\b(step by step|multi.?step|full analysis)\b",
        r"\b(project status|roadmap|sprint).*\b(and|with)\b.*\b(research|web|compare)\b",
    ]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def needs_tool_orchestration(self, message: str) -> bool:
        return any(re.search(p, message, re.IGNORECASE) for p in self.COMPLEX_PATTERNS)

    async def execute(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        space_ids: list[uuid.UUID] | None = None,
        project_id: uuid.UUID | None = None,
    ) -> OrchestrationResult:
        plan = await self._create_plan(query)
        registry = ToolRegistry(self._session, user_id)
        tool_results: list[ToolResult] = []

        for step in plan:
            result = await registry.execute(
                step.tool,
                step.query,
                space_ids=space_ids,
                project_id=project_id,
            )
            tool_results.append(result)

        synthesis_context = "\n\n".join(
            f"### {r.tool}\n{r.output}" for r in tool_results if r.success
        )

        provider = llm_registry.get_with_fallback()
        final = await provider.complete(
            [{"role": "user", "content": f"Original request: {query}\n\nTool results:\n{synthesis_context}\n\nSynthesize a comprehensive response."}],
            system="You are MOBIUS. Synthesize tool results into a coherent, actionable response. Cite sources where available. Explain your reasoning.",
            temperature=0.5,
        )

        if tool_results:
            await registry.execute(
                ToolName.STORE_FINDING,
                query,
                content=final[:1500],
            )

        return OrchestrationResult(
            plan=plan,
            tool_results=tool_results,
            final_response=final,
            agents_used=["tool_orchestrator"],
        )

    async def _create_plan(self, query: str) -> list[PlanStep]:
        provider = llm_registry.get_with_fallback()
        try:
            response = await provider.complete(
                [{"role": "user", "content": query}],
                system=PLANNING_PROMPT,
                temperature=0.2,
            )
            match = re.search(r"\[[\s\S]*\]", response)
            if match:
                steps_data = json.loads(match.group())
                return [
                    PlanStep(
                        step=s.get("step", i + 1),
                        tool=ToolName(s["tool"]),
                        query=s.get("query", query),
                        reason=s.get("reason", ""),
                    )
                    for i, s in enumerate(steps_data)
                    if s.get("tool") in [t.value for t in ToolName]
                ]
        except Exception:
            pass

        return self._default_plan(query)

    @staticmethod
    def _default_plan(query: str) -> list[PlanStep]:
        q = query.lower()
        steps = [PlanStep(step=1, tool=ToolName.MEMORY_SEARCH, query=query, reason="Check user context")]
        if any(w in q for w in ["code", "repo", "file", "architecture", "mobius"]):
            steps.append(PlanStep(step=2, tool=ToolName.KNOWLEDGE_SEARCH, query=query, reason="Search knowledge base"))
        if any(w in q for w in ["latest", "current", "2024", "2025", "2026", "compare", "competitor", "market"]):
            steps.append(PlanStep(step=len(steps) + 1, tool=ToolName.WEB_SEARCH, query=query, reason="Web research"))
        if any(w in q for w in ["project", "task", "sprint", "milestone", "roadmap"]):
            steps.append(PlanStep(step=len(steps) + 1, tool=ToolName.PROJECT_SUMMARY, query=query, reason="Project data"))
        steps.append(PlanStep(step=len(steps) + 1, tool=ToolName.STORE_FINDING, query=query, reason="Persist insights"))
        return steps
