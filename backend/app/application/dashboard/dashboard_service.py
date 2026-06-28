from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ConversationModel, IdeaModel, MemoryModel, TaskModel


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_dashboard(self, user_id: uuid.UUID) -> dict:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        conversations_today = (
            await self._session.execute(
                select(func.count())
                .select_from(ConversationModel)
                .where(ConversationModel.user_id == user_id, ConversationModel.updated_at >= today_start)
            )
        ).scalar() or 0

        memories_total = (
            await self._session.execute(
                select(func.count()).select_from(MemoryModel).where(MemoryModel.user_id == user_id)
            )
        ).scalar() or 0

        ideas_total = (
            await self._session.execute(
                select(func.count()).select_from(IdeaModel).where(IdeaModel.user_id == user_id)
            )
        ).scalar() or 0

        recent_memories = await self._get_recent_memories(user_id)
        recent_ideas = await self._get_recent_ideas(user_id)
        upcoming_tasks = await self._get_upcoming_tasks(user_id)
        focus = await self._get_focus(user_id)
        recommendations = await self._get_recommendations(user_id)

        return {
            "focus": focus,
            "recent_memories": recent_memories,
            "recent_ideas": recent_ideas,
            "upcoming_tasks": upcoming_tasks,
            "recommendations": recommendations,
            "stats": {
                "conversations_today": conversations_today,
                "memories_total": memories_total,
                "ideas_total": ideas_total,
            },
        }

    async def _get_recent_memories(self, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
        result = await self._session.execute(
            select(MemoryModel)
            .where(MemoryModel.user_id == user_id)
            .order_by(MemoryModel.importance.desc(), MemoryModel.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(m.id),
                "content": m.content[:150],
                "category": m.category,
                "tier": m.tier,
                "importance": m.importance,
                "created_at": m.created_at.isoformat(),
            }
            for m in result.scalars().all()
        ]

    async def _get_recent_ideas(self, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
        result = await self._session.execute(
            select(IdeaModel)
            .where(IdeaModel.user_id == user_id)
            .order_by(IdeaModel.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(i.id),
                "summary": i.summary or i.raw_input[:100],
                "status": i.status,
                "created_at": i.created_at.isoformat(),
            }
            for i in result.scalars().all()
        ]

    async def _get_upcoming_tasks(self, user_id: uuid.UUID, limit: int = 5) -> list[dict]:
        result = await self._session.execute(
            select(TaskModel)
            .join(IdeaModel, TaskModel.idea_id == IdeaModel.id, isouter=True)
            .where(
                TaskModel.status == "pending",
                (IdeaModel.user_id == user_id) | (TaskModel.idea_id.is_(None)),
            )
            .order_by(TaskModel.priority.desc(), TaskModel.created_at)
            .limit(limit)
        )
        return [
            {
                "id": str(t.id),
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in result.scalars().all()
        ]

    async def _get_focus(self, user_id: uuid.UUID) -> dict:
        four_days_ago = datetime.now(UTC) - timedelta(days=4)
        stale_conv = await self._session.execute(
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id, ConversationModel.updated_at < four_days_ago)
            .order_by(ConversationModel.updated_at.desc())
            .limit(1)
        )
        conv = stale_conv.scalar_one_or_none()
        if conv:
            return {
                "title": f"Continue: {conv.title}",
                "reason": f"Last touched {(datetime.now(UTC) - conv.updated_at).days} days ago",
                "action_url": f"/chat?conversation={conv.id}",
            }

        pending_idea = await self._session.execute(
            select(IdeaModel)
            .where(IdeaModel.user_id == user_id, IdeaModel.status == "new")
            .order_by(IdeaModel.created_at.desc())
            .limit(1)
        )
        idea = pending_idea.scalar_one_or_none()
        if idea:
            return {
                "title": f"Review idea: {idea.summary or idea.raw_input[:50]}",
                "reason": "New idea awaiting your review",
                "action_url": f"/ideas?id={idea.id}",
            }

        return {
            "title": "Start a conversation with MOBIUS",
            "reason": "Your intelligent partner is ready to help",
            "action_url": "/chat",
        }

    async def _get_recommendations(self, user_id: uuid.UUID) -> list[dict]:
        recommendations = []
        four_days_ago = datetime.now(UTC) - timedelta(days=4)

        stale_count = (
            await self._session.execute(
                select(func.count())
                .select_from(ConversationModel)
                .where(ConversationModel.user_id == user_id, ConversationModel.updated_at < four_days_ago)
            )
        ).scalar() or 0
        if stale_count > 0:
            recommendations.append({
                "type": "proactive",
                "message": f"You have {stale_count} conversation(s) untouched for 4+ days.",
                "action_url": "/chat",
            })

        new_ideas = (
            await self._session.execute(
                select(func.count())
                .select_from(IdeaModel)
                .where(IdeaModel.user_id == user_id, IdeaModel.status == "new")
            )
        ).scalar() or 0
        if new_ideas > 0:
            recommendations.append({
                "type": "proactive",
                "message": f"{new_ideas} idea(s) awaiting review.",
                "action_url": "/ideas",
            })

        return recommendations
