from fastapi import APIRouter

from app.api.routes import agents, auth, conversations, ideas, knowledge, memories, projects, research, search_dashboard, voice
from app.config import settings

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(conversations.router)
api_router.include_router(memories.router)
api_router.include_router(ideas.router)
api_router.include_router(search_dashboard.router)
api_router.include_router(voice.router)
api_router.include_router(knowledge.router)
api_router.include_router(agents.router)
api_router.include_router(research.router)
api_router.include_router(projects.router)


@api_router.get("/health")
async def health():
    db_status = "unknown"
    try:
        from sqlalchemy import text

        from app.infrastructure.database.session import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.app_version,
        "database": db_status,
        "features": [
            "knowledge_base", "rag", "agents", "orchestrator",
            "research", "tool_orchestrator", "project_management", "plugins",
        ],
    }


@api_router.get("/plugins")
async def list_plugins():
    from app.plugins.registry import PluginRegistry, register_builtin_plugins

    register_builtin_plugins()
    return {
        "plugins": [
            {"name": p.name, "version": p.version, "description": p.description, "source_type": p.source_type}
            for p in PluginRegistry.list_connectors()
        ]
    }
