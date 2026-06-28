import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.application.agents.orchestrator import Orchestrator
from app.application.knowledge.knowledge_base_service import KnowledgeBaseService
from app.config import settings
from app.dependencies import (
    get_current_user_id,
    get_knowledge_service,
    get_orchestrator,
)
from pydantic import BaseModel, Field

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class CreateSpaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    project_id: str | None = None


class AddLocalSourceRequest(BaseModel):
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    watch_enabled: bool = True


class AddGitHubSourceRequest(BaseModel):
    name: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    branch: str = "main"
    path: str = ""
    watch_enabled: bool = True


class AddNotionSourceRequest(BaseModel):
    name: str = Field(min_length=1)
    token: str | None = None
    database_id: str | None = None
    page_ids: list[str] = []
    watch_enabled: bool = True


class AddGDriveSourceRequest(BaseModel):
    name: str = Field(min_length=1)
    access_token: str | None = None
    folder_id: str = "root"
    watch_enabled: bool = True


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    space_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


@router.get("/spaces")
async def list_spaces(
    project_id: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    pid = uuid.UUID(project_id) if project_id else None
    return {"items": await service.list_spaces(user_id, project_id=pid)}


@router.post("/spaces", status_code=status.HTTP_201_CREATED)
async def create_space(
    body: CreateSpaceRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    pid = uuid.UUID(body.project_id) if body.project_id else None
    return await service.create_space(user_id, body.name, body.description, pid)


@router.get("/spaces/{space_id}")
async def get_space(
    space_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    space = await service.get_space(space_id, user_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return space


@router.post("/spaces/{space_id}/sources/local", status_code=status.HTTP_201_CREATED)
async def add_local_source(
    space_id: uuid.UUID,
    body: AddLocalSourceRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    try:
        return await service.add_local_source(space_id, user_id, body.name, body.path, body.watch_enabled)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/spaces/{space_id}/sources/github", status_code=status.HTTP_201_CREATED)
async def add_github_source(
    space_id: uuid.UUID,
    body: AddGitHubSourceRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    try:
        return await service.add_github_source(
            space_id, user_id, body.name, body.repo, body.branch, body.path, body.watch_enabled
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/spaces/{space_id}/sources/notion", status_code=status.HTTP_201_CREATED)
async def add_notion_source(
    space_id: uuid.UUID,
    body: AddNotionSourceRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    try:
        return await service.add_notion_source(
            space_id, user_id, body.name, token=body.token,
            database_id=body.database_id, page_ids=body.page_ids or None,
            watch_enabled=body.watch_enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/spaces/{space_id}/sources/gdrive", status_code=status.HTTP_201_CREATED)
async def add_gdrive_source(
    space_id: uuid.UUID,
    body: AddGDriveSourceRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    try:
        return await service.add_gdrive_source(
            space_id, user_id, body.name, access_token=body.access_token,
            folder_id=body.folder_id, watch_enabled=body.watch_enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/sources/{source_id}/ingest")
async def ingest_source(
    source_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    try:
        return await service.trigger_ingestion(source_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/ingestion/{job_id}")
async def get_ingestion_job(
    job_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    job = await service.get_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/spaces/{space_id}/upload")
async def upload_document(
    space_id: uuid.UUID,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    data = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.max_upload_size_mb}MB")
    try:
        return await service.upload_document(space_id, user_id, file.filename or "upload", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/spaces/{space_id}/documents")
async def list_documents(
    space_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    try:
        return {"items": await service.list_documents(space_id, user_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/search")
async def search_knowledge(
    body: KnowledgeSearchRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: KnowledgeBaseService = Depends(get_knowledge_service),
):
    space_id = uuid.UUID(body.space_id) if body.space_id else None
    results = await service.search(user_id, body.query, space_id=space_id, limit=body.limit)
    return {"results": results}
