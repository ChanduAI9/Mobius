import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas import CreateConversationRequest, SendMessageRequest
from app.application.conversation.conversation_service import ConversationService
from app.application.ideas.idea_service import IdeaService
from app.dependencies import get_conversation_service, get_current_user_id, get_idea_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    project_id: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
):
    pid = uuid.UUID(project_id) if project_id else None
    items, total = await service.list_conversations(user_id, limit=limit, offset=offset, project_id=pid)
    return {"items": items, "total": total}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: CreateConversationRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
):
    pid = uuid.UUID(body.project_id) if body.project_id else None
    conv = await service.create(user_id, title=body.title, project_id=pid)
    return service._conv_dict(conv)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
):
    conv = await service.get_conversation(conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID,
    body: SendMessageRequest,
    agent: str | None = Query(None),
    space_ids: str | None = Query(None, description="Comma-separated space UUIDs"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
    idea_service: IdeaService = Depends(get_idea_service),
):
    sids = [uuid.UUID(s.strip()) for s in space_ids.split(",") if s.strip()] if space_ids else None
    try:
        user_msg, assistant_msg, agent_used = await service.send_message(
            conversation_id, user_id, body.content, body.attachments, agent=agent, space_ids=sids
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    idea_captured = None
    if idea_service.detect_idea_trigger(body.content):
        idea_content = idea_service.extract_idea_content(body.content)
        idea_captured = await idea_service.capture(user_id, idea_content, conversation_id=conversation_id)

    return {
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "agent_used": agent_used,
        "idea_captured": idea_captured,
    }
