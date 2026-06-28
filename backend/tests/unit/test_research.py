from app.domain.research import Citation, ResearchFinding, SearchResult
from app.application.agents.orchestrator import Orchestrator
from app.plugins.registry import PluginRegistry, register_builtin_plugins


class TestResearchDomain:
    def test_search_result_defaults(self):
        r = SearchResult(title="Test", url="https://example.com", snippet="Hello")
        assert r.source == "web"

    def test_research_finding_citations(self):
        finding = ResearchFinding(
            title="Redis vs Memcached",
            summary="Comparison",
            content="Full analysis",
            citations=[Citation(index=1, title="Doc", url="https://x.com", snippet="...")],
            tags=["comparison"],
        )
        assert len(finding.citations) == 1
        assert finding.category == "research"


class TestResearchIntent:
    def setup_method(self):
        self.orchestrator = Orchestrator(rag_service=None, memory_service=None, research_service=None)  # type: ignore

    def test_classifies_research_queries(self):
        assert self.orchestrator.classify_intent("Compare Redis vs Memcached for caching") == "research"

    def test_classifies_competitor_research(self):
        assert self.orchestrator.classify_intent("Research competitor pricing for SaaS tools") == "research"

    def test_classifies_paper_analysis(self):
        assert self.orchestrator.classify_intent("Summarize the attention is all you need paper") == "research"


class TestPluginRegistry:
    def test_builtin_plugins_registered(self):
        registry = PluginRegistry()
        register_builtin_plugins()
        plugins = registry.list_connectors()
        types = {p.source_type for p in plugins}
        assert "notion" in types
        assert "google_drive" in types
