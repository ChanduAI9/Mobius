import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import MilestoneModel, ProjectModel, SprintModel, TaskModel

KANBAN_COLUMNS = ["backlog", "todo", "in_progress", "review", "done"]


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_project(
        self, user_id: uuid.UUID, name: str, description: str | None = None
    ) -> dict:
        project = ProjectModel(user_id=user_id, name=name, description=description)
        self._session.add(project)
        await self._session.flush()
        return self._project_dict(project)

    async def list_projects(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[dict], int]:
        query = (
            select(ProjectModel)
            .where(ProjectModel.user_id == user_id)
            .order_by(ProjectModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        projects = result.scalars().all()
        total = (
            await self._session.execute(
                select(func.count()).select_from(ProjectModel).where(ProjectModel.user_id == user_id)
            )
        ).scalar() or 0

        items = []
        for p in projects:
            stats = await self._project_stats(p.id)
            items.append({**self._project_dict(p), **stats})
        return items, total

    async def get_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        project = await self._get_project(project_id, user_id)
        if not project:
            return None
        stats = await self._project_stats(project_id)
        sprints = await self.list_sprints(project_id, user_id)
        milestones = await self.list_milestones(project_id, user_id)
        return {
            **self._project_dict(project),
            **stats,
            "sprints": sprints,
            "milestones": milestones,
        }

    async def create_task(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        title: str,
        *,
        description: str | None = None,
        priority: str = "medium",
        kanban_column: str = "backlog",
        sprint_id: uuid.UUID | None = None,
        milestone_id: uuid.UUID | None = None,
        due_date: date | None = None,
    ) -> dict:
        await self._get_project(project_id, user_id)
        task = TaskModel(
            user_id=user_id,
            project_id=project_id,
            title=title,
            description=description,
            priority=priority,
            kanban_column=kanban_column,
            sprint_id=sprint_id,
            milestone_id=milestone_id,
            due_date=due_date,
        )
        self._session.add(task)
        await self._session.flush()
        return self._task_dict(task)

    async def update_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID, **updates
    ) -> dict | None:
        task = await self._get_task(task_id, user_id)
        if not task:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.now(UTC)
        await self._session.flush()
        return self._task_dict(task)

    async def list_tasks(
        self, project_id: uuid.UUID, user_id: uuid.UUID, sprint_id: uuid.UUID | None = None
    ) -> list[dict]:
        await self._get_project(project_id, user_id)
        query = select(TaskModel).where(TaskModel.project_id == project_id, TaskModel.user_id == user_id)
        if sprint_id:
            query = query.where(TaskModel.sprint_id == sprint_id)
        query = query.order_by(TaskModel.kanban_column, TaskModel.order_index, TaskModel.created_at)
        result = await self._session.execute(query)
        return [self._task_dict(t) for t in result.scalars().all()]

    async def get_kanban_board(self, project_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        tasks = await self.list_tasks(project_id, user_id)
        board = {col: [] for col in KANBAN_COLUMNS}
        for task in tasks:
            col = task["kanban_column"] if task["kanban_column"] in board else "backlog"
            board[col].append(task)
        return {"columns": KANBAN_COLUMNS, "board": board}

    async def move_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID, kanban_column: str, order_index: int = 0
    ) -> dict | None:
        if kanban_column not in KANBAN_COLUMNS:
            raise ValueError(f"Invalid column: {kanban_column}")
        return await self.update_task(task_id, user_id, kanban_column=kanban_column, order_index=order_index)

    async def create_sprint(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        name: str,
        *,
        goal: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        await self._get_project(project_id, user_id)
        sprint = SprintModel(
            user_id=user_id,
            project_id=project_id,
            name=name,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
        )
        self._session.add(sprint)
        await self._session.flush()
        return self._sprint_dict(sprint)

    async def list_sprints(self, project_id: uuid.UUID, user_id: uuid.UUID) -> list[dict]:
        result = await self._session.execute(
            select(SprintModel)
            .where(SprintModel.project_id == project_id, SprintModel.user_id == user_id)
            .order_by(SprintModel.start_date.desc())
        )
        return [self._sprint_dict(s) for s in result.scalars().all()]

    async def create_milestone(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        title: str,
        *,
        description: str | None = None,
        due_date: date | None = None,
        order_index: int = 0,
    ) -> dict:
        await self._get_project(project_id, user_id)
        milestone = MilestoneModel(
            user_id=user_id,
            project_id=project_id,
            title=title,
            description=description,
            due_date=due_date,
            order_index=order_index,
        )
        self._session.add(milestone)
        await self._session.flush()
        return self._milestone_dict(milestone)

    async def list_milestones(self, project_id: uuid.UUID, user_id: uuid.UUID) -> list[dict]:
        result = await self._session.execute(
            select(MilestoneModel)
            .where(MilestoneModel.project_id == project_id, MilestoneModel.user_id == user_id)
            .order_by(MilestoneModel.order_index, MilestoneModel.due_date)
        )
        return [self._milestone_dict(m) for m in result.scalars().all()]

    async def get_project_analytics(self, project_id: uuid.UUID, user_id: uuid.UUID) -> dict:
        await self._get_project(project_id, user_id)
        tasks_result = await self._session.execute(
            select(TaskModel.kanban_column, func.count())
            .where(TaskModel.project_id == project_id, TaskModel.user_id == user_id)
            .group_by(TaskModel.kanban_column)
        )
        by_column = {row[0]: row[1] for row in tasks_result.all()}
        total = sum(by_column.values())
        done = by_column.get("done", 0)
        milestones_result = await self._session.execute(
            select(MilestoneModel.status, func.count())
            .where(MilestoneModel.project_id == project_id)
            .group_by(MilestoneModel.status)
        )
        milestone_stats = {row[0]: row[1] for row in milestones_result.all()}

        return {
            "project_id": str(project_id),
            "tasks_total": total,
            "tasks_by_column": by_column,
            "completion_rate": round(done / total, 2) if total else 0,
            "milestones": milestone_stats,
            "recommendations": self._generate_recommendations(by_column, total, done),
        }

    async def get_recommendations(self, user_id: uuid.UUID) -> list[dict]:
        projects, _ = await self.list_projects(user_id, limit=10)
        recs = []
        for p in projects:
            if p.get("completion_rate", 0) < 0.5 and p.get("tasks_total", 0) > 3:
                recs.append({
                    "type": "project",
                    "message": f"Project '{p['name']}' is {int(p.get('completion_rate', 0)*100)}% complete with {p.get('tasks_total')} tasks.",
                    "action_url": f"/projects?id={p['id']}",
                })
            in_progress = p.get("tasks_by_column", {}).get("in_progress", 0)
            if in_progress > 5:
                recs.append({
                    "type": "focus",
                    "message": f"'{p['name']}' has {in_progress} tasks in progress — consider limiting WIP.",
                    "action_url": f"/projects?id={p['id']}",
                })
        return recs

    @staticmethod
    def _generate_recommendations(by_column: dict, total: int, done: int) -> list[str]:
        recs = []
        if total == 0:
            recs.append("Add tasks to start tracking progress.")
        if by_column.get("in_progress", 0) > 4:
            recs.append("High WIP detected — focus on completing in-progress tasks.")
        if total > 0 and done / total < 0.3:
            recs.append("Low completion rate — review blocked tasks in review column.")
        if by_column.get("backlog", 0) > 10:
            recs.append("Large backlog — prioritize and move items to todo.")
        return recs

    async def _get_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectModel | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id, ProjectModel.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")
        return project

    async def _get_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> TaskModel | None:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _project_stats(self, project_id: uuid.UUID) -> dict:
        task_counts = await self._session.execute(
            select(TaskModel.kanban_column, func.count())
            .where(TaskModel.project_id == project_id)
            .group_by(TaskModel.kanban_column)
        )
        by_column = {row[0]: row[1] for row in task_counts.all()}
        total = sum(by_column.values())
        done = by_column.get("done", 0)
        return {
            "tasks_total": total,
            "tasks_by_column": by_column,
            "completion_rate": round(done / total, 2) if total else 0,
        }

    @staticmethod
    def _project_dict(p: ProjectModel) -> dict:
        return {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }

    @staticmethod
    def _task_dict(t: TaskModel) -> dict:
        return {
            "id": str(t.id),
            "project_id": str(t.project_id) if t.project_id else None,
            "sprint_id": str(t.sprint_id) if t.sprint_id else None,
            "milestone_id": str(t.milestone_id) if t.milestone_id else None,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "kanban_column": t.kanban_column,
            "order_index": t.order_index,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat(),
        }

    @staticmethod
    def _sprint_dict(s: SprintModel) -> dict:
        return {
            "id": str(s.id),
            "name": s.name,
            "goal": s.goal,
            "status": s.status,
            "start_date": s.start_date.isoformat() if s.start_date else None,
            "end_date": s.end_date.isoformat() if s.end_date else None,
        }

    @staticmethod
    def _milestone_dict(m: MilestoneModel) -> dict:
        return {
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "status": m.status,
            "due_date": m.due_date.isoformat() if m.due_date else None,
            "order_index": m.order_index,
        }
