import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.application.agents.orchestrator import Orchestrator
from app.dependencies import get_current_user_id, get_orchestrator

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentRunRequest(BaseModel):
    message: str = Field(min_length=1)
    agent: str | None = None
    space_ids: list[str] = []
    conversation_context: list[dict[str, str]] = []


class ClassifyRequest(BaseModel):
    message: str = Field(min_length=1)


@router.post("/classify")
async def classify_intent(
    body: ClassifyRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    agent = orchestrator.get_agent_for_message(body.message)
    return {"agent": agent, "message": body.message}


@router.post("/run")
async def run_agent(
    body: AgentRunRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    messages = [*body.conversation_context, {"role": "user", "content": body.message}]

    try:
        response = await orchestrator.process(
            user_id, messages, agent_override=body.agent, space_ids=space_ids
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return {
        "content": response.content,
        "agent": response.agent,
        "context_used": response.context_used,
    }


@router.post("/coding")
async def run_coding_agent(
    body: AgentRunRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    messages = [*body.conversation_context, {"role": "user", "content": body.message}]
    response = await orchestrator.process(user_id, messages, agent_override="coding", space_ids=space_ids)
    return {"content": response.content, "agent": response.agent, "context_used": response.context_used}


@router.post("/architecture")
async def run_architecture_agent(
    body: AgentRunRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    messages = [*body.conversation_context, {"role": "user", "content": body.message}]
    response = await orchestrator.process(user_id, messages, agent_override="architecture", space_ids=space_ids)
    return {"content": response.content, "agent": response.agent, "context_used": response.context_used}


@router.post("/research")
async def run_research_agent(
    body: AgentRunRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    messages = [*body.conversation_context, {"role": "user", "content": body.message}]
    response = await orchestrator.process(user_id, messages, agent_override="research", space_ids=space_ids)
    return {"content": response.content, "agent": response.agent, "context_used": response.context_used}
