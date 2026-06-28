import json
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.knowledge.ingestion_service import IngestionService
from app.application.knowledge.knowledge_base_service import KnowledgeBaseService
from app.application.knowledge.rag_service import RAGService
from app.application.memory.memory_service import MemoryService
from app.domain.entities import MemoryTier
from app.domain.research import Citation, ResearchFinding, SearchResult
from app.infrastructure.ai.provider_registry import llm_registry
from app.infrastructure.research.web_search import WebSearchService


class ResearchService:
    def __init__(self, session: AsyncSession, memory_service: MemoryService) -> None:
        self._session = session
        self._memory = memory_service
        self._rag = RAGService(session, memory_service)
        self._web = WebSearchService()
        self._kb = KnowledgeBaseService(session, memory_service)

    async def research(
        self,
        user_id: uuid.UUID,
        query: str,
        *,
        mode: str = "general",
        space_ids: list[uuid.UUID] | None = None,
        store_findings: bool = True,
        max_web_results: int = 8,
    ) -> ResearchFinding:
        web_results = await self._web.search(query, max_results=max_web_results)
        kb_results = await self._rag.retrieve(
            user_id, query, space_ids=space_ids, limit=5, include_memories=True
        )

        citations = self._build_citations(web_results, kb_results)
        context = self._format_context(web_results, kb_results)

        system = self._system_prompt(mode)
        user_prompt = self._build_prompt(query, context, mode)

        provider = llm_registry.get_with_fallback()
        response = await provider.complete(
            [{"role": "user", "content": user_prompt}],
            system=system,
            temperature=0.4,
        )

        finding = ResearchFinding(
            title=query[:100],
            summary=response[:500],
            content=response,
            citations=citations,
            category=f"research_{mode}",
            tags=[mode, "research"],
        )

        if store_findings:
            await self._store_finding(user_id, finding, space_ids)

        return finding

    async def compare_technologies(
        self, user_id: uuid.UUID, technologies: list[str], *, space_ids: list[uuid.UUID] | None = None
    ) -> ResearchFinding:
        query = f"Compare {' vs '.join(technologies)}: features, performance, ecosystem, use cases, trade-offs"
        return await self.research(user_id, query, mode="technology_comparison", space_ids=space_ids)

    async def analyze_competitors(
        self, user_id: uuid.UUID, company_or_product: str, *, space_ids: list[uuid.UUID] | None = None
    ) -> ResearchFinding:
        query = f"Competitor analysis for {company_or_product}: market position, strengths, weaknesses, pricing, differentiation"
        return await self.research(user_id, query, mode="competitor_research", space_ids=space_ids)

    async def analyze_paper(
        self, user_id: uuid.UUID, paper_title_or_url: str, *, space_ids: list[uuid.UUID] | None = None
    ) -> ResearchFinding:
        query = f"Analyze research paper: {paper_title_or_url}. Key contributions, methodology, results, limitations, practical applications."
        return await self.research(user_id, query, mode="paper_analysis", space_ids=space_ids)

    async def summarize_document(
        self, user_id: uuid.UUID, content: str, *, title: str = "Document"
    ) -> ResearchFinding:
        provider = llm_registry.get_with_fallback()
        response = await provider.complete(
            [{"role": "user", "content": f"Summarize this document titled '{title}':\n\n{content[:8000]}"}],
            system="Provide: 1) Executive summary 2) Key points 3) Actionable insights. Be concise.",
            temperature=0.3,
        )
        finding = ResearchFinding(
            title=f"Summary: {title}",
            summary=response[:500],
            content=response,
            category="research_summary",
            tags=["summary"],
        )
        await self._store_finding(user_id, finding, None)
        return finding

    async def _store_finding(
        self,
        user_id: uuid.UUID,
        finding: ResearchFinding,
        space_ids: list[uuid.UUID] | None,
    ) -> None:
        citation_text = "\n".join(f"[{c.index}] {c.title} - {c.url}" for c in finding.citations)
        memory_content = f"{finding.summary}\n\nSources:\n{citation_text}" if citation_text else finding.summary

        await self._memory.create(
            user_id,
            memory_content,
            category=finding.category,
            tier=MemoryTier.SEMANTIC,
            importance=0.75,
            tags=finding.tags + ["auto_research"],
            summary=finding.title,
            source_type="research",
        )

        if space_ids:
            for space_id in space_ids[:1]:
                try:
                    filename = f"research_{finding.title[:50].replace(' ', '_')}.md"
                    content = f"# {finding.title}\n\n{finding.content}\n\n## Sources\n{citation_text}"
                    await self._kb.upload_document(
                        space_id, user_id, filename, content.encode("utf-8")
                    )
                except Exception:
                    pass

    @staticmethod
    def _build_citations(web: list[SearchResult], kb: list) -> list[Citation]:
        citations = []
        for i, r in enumerate(web, 1):
            citations.append(Citation(index=i, title=r.title, url=r.url, snippet=r.snippet))
        offset = len(citations)
        for j, kr in enumerate(kb, 1):
            citations.append(
                Citation(
                    index=offset + j,
                    title=kr.filename,
                    url=f"kb://{kr.file_path}",
                    snippet=kr.content[:200],
                )
            )
        return citations

    @staticmethod
    def _format_context(web: list[SearchResult], kb: list) -> str:
        parts = []
        if web:
            parts.append("## Web Sources")
            for i, r in enumerate(web, 1):
                parts.append(f"[{i}] **{r.title}** ({r.url})\n{r.snippet}")
        if kb:
            parts.append("## Knowledge Base")
            for kr in kb:
                parts.append(f"**{kr.filename}** ({kr.file_path})\n{kr.content[:400]}")
        return "\n\n".join(parts)

    @staticmethod
    def _system_prompt(mode: str) -> str:
        base = """You are MOBIUS Research Agent — a rigorous research analyst.

Rules:
- Cite sources using [1], [2] notation matching provided sources
- Distinguish facts from inference
- Present multiple perspectives when comparing
- Be honest about gaps in available information
- Structure responses clearly with headers
- Never fabricate sources or URLs"""
        modes = {
            "technology_comparison": "\nFocus: feature matrix, performance, ecosystem, learning curve, trade-offs, recommendation.",
            "competitor_research": "\nFocus: market position, product comparison, pricing, moat, threats, opportunities.",
            "paper_analysis": "\nFocus: problem, methodology, key results, limitations, citations, practical impact.",
            "general": "\nFocus: comprehensive answer with evidence-based conclusions.",
        }
        return base + modes.get(mode, modes["general"])

    @staticmethod
    def _build_prompt(query: str, context: str, mode: str) -> str:
        return f"""Research query ({mode}): {query}

Available sources:
{context}

Provide a thorough, well-cited research response. Use [N] citations for every major claim."""

    def finding_to_dict(self, finding: ResearchFinding) -> dict:
        return {
            "title": finding.title,
            "summary": finding.summary,
            "content": finding.content,
            "category": finding.category,
            "tags": finding.tags,
            "citations": [
                {"index": c.index, "title": c.title, "url": c.url, "snippet": c.snippet}
                for c in finding.citations
            ],
        }
