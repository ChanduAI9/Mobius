import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.application.projects.project_service import ProjectService
from app.dependencies import get_current_user_id, get_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    priority: str = "medium"
    kanban_column: str = "backlog"
    sprint_id: str | None = None
    milestone_id: str | None = None
    due_date: date | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    kanban_column: str | None = None
    order_index: int | None = None
    priority: str | None = None
    sprint_id: str | None = None
    milestone_id: str | None = None


class MoveTaskRequest(BaseModel):
    kanban_column: str
    order_index: int = 0


class CreateSprintRequest(BaseModel):
    name: str = Field(min_length=1)
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CreateMilestoneRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    due_date: date | None = None
    order_index: int = 0


@router.get("")
async def list_projects(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    items, total = await service.list_projects(user_id, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    body: CreateProjectRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    return await service.create_project(user_id, body.name, body.description)


@router.get("/recommendations")
async def project_recommendations(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    return {"recommendations": await service.get_recommendations(user_id)}


@router.get("/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    project = await service.get_project(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/analytics")
async def project_analytics(
    project_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    try:
        return await service.get_project_analytics(project_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{project_id}/kanban")
async def kanban_board(
    project_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    try:
        return await service.get_kanban_board(project_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{project_id}/tasks")
async def list_tasks(
    project_id: uuid.UUID,
    sprint_id: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    sid = uuid.UUID(sprint_id) if sprint_id else None
    try:
        return {"items": await service.list_tasks(project_id, user_id, sprint_id=sid)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: uuid.UUID,
    body: CreateTaskRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    try:
        return await service.create_task(
            user_id,
            project_id,
            body.title,
            description=body.description,
            priority=body.priority,
            kanban_column=body.kanban_column,
            sprint_id=uuid.UUID(body.sprint_id) if body.sprint_id else None,
            milestone_id=uuid.UUID(body.milestone_id) if body.milestone_id else None,
            due_date=body.due_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: uuid.UUID,
    body: UpdateTaskRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    updates = body.model_dump(exclude_none=True)
    if "sprint_id" in updates and updates["sprint_id"]:
        updates["sprint_id"] = uuid.UUID(updates["sprint_id"])
    if "milestone_id" in updates and updates["milestone_id"]:
        updates["milestone_id"] = uuid.UUID(updates["milestone_id"])
    task = await service.update_task(task_id, user_id, **updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/move")
async def move_task(
    task_id: uuid.UUID,
    body: MoveTaskRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    try:
        task = await service.move_task(task_id, user_id, body.kanban_column, body.order_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{project_id}/sprints", status_code=status.HTTP_201_CREATED)
async def create_sprint(
    project_id: uuid.UUID,
    body: CreateSprintRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    try:
        return await service.create_sprint(
            user_id, project_id, body.name, goal=body.goal,
            start_date=body.start_date, end_date=body.end_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{project_id}/milestones", status_code=status.HTTP_201_CREATED)
async def create_milestone(
    project_id: uuid.UUID,
    body: CreateMilestoneRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ProjectService = Depends(get_project_service),
):
    try:
        return await service.create_milestone(
            user_id, project_id, body.title,
            description=body.description, due_date=body.due_date, order_index=body.order_index,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
