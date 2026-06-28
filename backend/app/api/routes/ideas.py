import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas import CaptureIdeaRequest, CreateIdeaRequest, UpdateIdeaRequest
from app.application.ideas.idea_service import IdeaService
from app.dependencies import get_current_user_id, get_idea_service

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("")
async def list_ideas(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    items, total = await service.list_ideas(user_id, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_idea(
    body: CreateIdeaRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    pid = uuid.UUID(body.project_id) if body.project_id else None
    return await service.capture(user_id, body.raw_input, project_id=pid)


@router.post("/capture", status_code=status.HTTP_201_CREATED)
async def capture_idea(
    body: CaptureIdeaRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    raw = service.extract_idea_content(body.content) if service.detect_idea_trigger(body.content) else body.content
    pid = uuid.UUID(body.project_id) if body.project_id else None
    cid = uuid.UUID(body.conversation_id) if body.conversation_id else None
    return await service.capture(user_id, raw, project_id=pid, conversation_id=cid)


@router.get("/{idea_id}")
async def get_idea(
    idea_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    idea = await service.get_idea(idea_id, user_id)
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")
    return idea


@router.patch("/{idea_id}")
async def update_idea(
    idea_id: uuid.UUID,
    body: UpdateIdeaRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    idea = await service.update_idea(idea_id, user_id, **body.model_dump(exclude_none=True))
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")
    return idea
