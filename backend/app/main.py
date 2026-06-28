from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.ws import router as ws_router
from app.application.knowledge.watcher_service import source_watcher
from app.config import settings
from app.plugins.registry import register_builtin_plugins

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("mobius_starting", version=settings.app_version)
    register_builtin_plugins()
    await source_watcher.start()
    yield
    await source_watcher.stop()
    logger.info("mobius_shutting_down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="MOBIUS — Personal AI Operating System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": "/api/v1",
    }
