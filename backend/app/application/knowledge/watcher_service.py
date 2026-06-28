import asyncio
import structlog

from app.config import settings
from app.infrastructure.database.session import async_session_factory

logger = structlog.get_logger()


class SourceWatcher:
    """Background poller for file change detection on knowledge sources."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("source_watcher_started", interval=settings.watcher_poll_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("source_watcher_stopped")

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._check_all_sources()
            except Exception as e:
                logger.error("watcher_poll_error", error=str(e))
            await asyncio.sleep(settings.watcher_poll_interval_seconds)

    async def _check_all_sources(self) -> None:
        from app.application.knowledge.ingestion_service import IngestionService
        from app.infrastructure.database.repositories.document_repository import DocumentRepository

        async with async_session_factory() as session:
            repo = DocumentRepository(session)
            sources = await repo.list_watchable_sources()
            ingestion = IngestionService(session)

            for source in sources:
                try:
                    changed = await ingestion.check_source_changes(source.id, source.user_id)
                    if changed:
                        logger.info("source_reindexed", source_id=str(source.id), name=source.name)
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.error("source_watch_error", source_id=str(source.id), error=str(e))


source_watcher = SourceWatcher()
