import pytest

from app.application.agents.orchestrator import Orchestrator
from app.domain.knowledge import AgentType


class TestOrchestratorIntent:
    def setup_method(self):
        self.orchestrator = Orchestrator(rag_service=None, memory_service=None, research_service=None)  # type: ignore

    @pytest.mark.parametrize(
        "message,expected",
        [
            ("Review my microservices architecture for scalability", AgentType.ARCHITECTURE),
            ("Generate a mermaid diagram for the auth flow", AgentType.ARCHITECTURE),
            ("What are the trade-offs between Redis and Memcached?", AgentType.ARCHITECTURE),
            ("Write a FastAPI endpoint for user authentication", AgentType.CODING),
            ("Fix this bug in my Python code", AgentType.CODING),
            ("How do I implement JWT refresh tokens?", AgentType.CODING),
            ("Summarize the documentation about RAG", AgentType.RESEARCH),
            ("Hello, how are you today?", AgentType.CONVERSATION),
        ],
    )
    def test_classify_intent(self, message, expected):
        assert self.orchestrator.classify_intent(message) == expected

    def test_agent_override(self):
        assert self.orchestrator.classify_intent("hello", agent_override="coding") == AgentType.CODING
