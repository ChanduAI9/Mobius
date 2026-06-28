import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.application.research.research_service import ResearchService
from app.application.tools.tool_orchestrator import ToolOrchestrator
from app.dependencies import (
    get_current_user_id,
    get_research_service,
    get_tool_orchestrator,
)

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: str = "general"
    space_ids: list[str] = []
    store_findings: bool = True


class CompareRequest(BaseModel):
    technologies: list[str] = Field(min_length=2)
    space_ids: list[str] = []


class CompetitorRequest(BaseModel):
    target: str = Field(min_length=1)
    space_ids: list[str] = []


class PaperRequest(BaseModel):
    paper: str = Field(min_length=1)
    space_ids: list[str] = []


class SummarizeRequest(BaseModel):
    content: str = Field(min_length=1)
    title: str = "Document"


class ToolOrchestrateRequest(BaseModel):
    query: str = Field(min_length=1)
    space_ids: list[str] = []
    project_id: str | None = None


@router.post("")
async def research(
    body: ResearchRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ResearchService = Depends(get_research_service),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    try:
        finding = await service.research(
            user_id, body.query, mode=body.mode, space_ids=space_ids, store_findings=body.store_findings
        )
        return service.finding_to_dict(finding)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.post("/compare")
async def compare_technologies(
    body: CompareRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ResearchService = Depends(get_research_service),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    finding = await service.compare_technologies(user_id, body.technologies, space_ids=space_ids)
    return service.finding_to_dict(finding)


@router.post("/competitors")
async def analyze_competitors(
    body: CompetitorRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ResearchService = Depends(get_research_service),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    finding = await service.analyze_competitors(user_id, body.target, space_ids=space_ids)
    return service.finding_to_dict(finding)


@router.post("/paper")
async def analyze_paper(
    body: PaperRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ResearchService = Depends(get_research_service),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    finding = await service.analyze_paper(user_id, body.paper, space_ids=space_ids)
    return service.finding_to_dict(finding)


@router.post("/summarize")
async def summarize_document(
    body: SummarizeRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: ResearchService = Depends(get_research_service),
):
    finding = await service.summarize_document(user_id, body.content, title=body.title)
    return service.finding_to_dict(finding)


@router.post("/orchestrate")
async def tool_orchestrate(
    body: ToolOrchestrateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    orchestrator: ToolOrchestrator = Depends(get_tool_orchestrator),
):
    space_ids = [uuid.UUID(s) for s in body.space_ids] if body.space_ids else None
    project_id = uuid.UUID(body.project_id) if body.project_id else None
    result = await orchestrator.execute(user_id, body.query, space_ids=space_ids, project_id=project_id)
    return {
        "plan": [{"step": s.step, "tool": s.tool.value, "query": s.query, "reason": s.reason} for s in result.plan],
        "tool_results": [{"tool": r.tool, "success": r.success, "output": r.output[:1000]} for r in result.tool_results],
        "response": result.final_response,
        "agents_used": result.agents_used,
    }
