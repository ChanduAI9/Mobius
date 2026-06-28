import pytest

from app.application.tools.tool_orchestrator import ToolOrchestrator


class TestToolOrchestrator:
    def test_needs_orchestration(self):
        orch = ToolOrchestrator(session=None)  # type: ignore
        assert orch.needs_tool_orchestration("Research and compare Redis vs Memcached with web sources")
        assert not orch.needs_tool_orchestration("Hello")

    def test_default_plan_includes_memory(self):
        orch = ToolOrchestrator(session=None)  # type: ignore
        plan = orch._default_plan("Compare FastAPI vs Flask for MOBIUS")
        tools = [s.tool.value for s in plan]
        assert "memory_search" in tools
        assert "knowledge_search" in tools or "web_search" in tools
