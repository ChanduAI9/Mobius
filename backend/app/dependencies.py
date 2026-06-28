import uuid
from collections import defaultdict
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.orchestrator import Orchestrator
from app.application.auth.auth_service import AuthService
from app.application.conversation.conversation_service import ConversationService
from app.application.dashboard.dashboard_service import DashboardService
from app.application.ideas.idea_service import IdeaService
from app.application.knowledge.knowledge_base_service import KnowledgeBaseService
from app.application.knowledge.rag_service import RAGService
from app.application.memory.memory_service import MemoryService
from app.application.projects.project_service import ProjectService
from app.application.research.research_service import ResearchService
from app.application.search.search_service import SearchService
from app.application.tools.tool_orchestrator import ToolOrchestrator
from app.application.voice.voice_service import VoiceService
from app.config import settings
from app.infrastructure.database.session import get_session
from app.infrastructure.security.jwt import decode_token

security = HTTPBearer()

_rate_limit_store: dict[str, list[datetime]] = defaultdict(list)


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return uuid.UUID(payload["sub"])


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


def get_memory_service(session: AsyncSession = Depends(get_db)) -> MemoryService:
    return MemoryService(session)


def get_rag_service(
    session: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service),
) -> RAGService:
    return RAGService(session, memory_service)


def get_research_service(
    session: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service),
) -> ResearchService:
    return ResearchService(session, memory_service)


def get_project_service(session: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(session)


def get_orchestrator(
    rag_service: RAGService = Depends(get_rag_service),
    memory_service: MemoryService = Depends(get_memory_service),
    research_service: ResearchService = Depends(get_research_service),
) -> Orchestrator:
    return Orchestrator(rag_service, memory_service, research_service)


def get_tool_orchestrator(session: AsyncSession = Depends(get_db)) -> ToolOrchestrator:
    return ToolOrchestrator(session)


def get_knowledge_service(
    session: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(session, memory_service)


def get_conversation_service(
    session: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service),
    orchestrator: Orchestrator = Depends(get_orchestrator),
    tool_orchestrator: ToolOrchestrator = Depends(get_tool_orchestrator),
) -> ConversationService:
    return ConversationService(session, memory_service, orchestrator, tool_orchestrator)


def get_idea_service(session: AsyncSession = Depends(get_db)) -> IdeaService:
    return IdeaService(session)


def get_search_service(
    session: AsyncSession = Depends(get_db),
    memory_service: MemoryService = Depends(get_memory_service),
) -> SearchService:
    return SearchService(session, memory_service)


def get_dashboard_service(session: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(session)


def get_voice_service() -> VoiceService:
    return VoiceService()


async def rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.now(UTC)
    window_start = now.timestamp() - settings.rate_limit_window_seconds

    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts.timestamp() > window_start
    ]

    if len(_rate_limit_store[client_ip]) >= settings.rate_limit_requests:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    _rate_limit_store[client_ip].append(now)
