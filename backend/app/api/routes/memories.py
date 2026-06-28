import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas import CreateMemoryRequest, MemorySearchRequest, UpdateMemoryRequest
from app.application.memory.memory_service import MemoryService
from app.dependencies import get_current_user_id, get_memory_service
from app.domain.entities import MemoryTier

router = APIRouter(prefix="/memories", tags=["memories"])


def _memory_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "user_id": str(m.user_id),
        "project_id": str(m.project_id) if m.project_id else None,
        "tier": m.tier.value,
        "category": m.category,
        "content": m.content,
        "summary": m.summary,
        "importance": m.importance,
        "tags": m.tags,
        "source_type": m.source_type,
        "source_id": str(m.source_id) if m.source_id else None,
        "metadata": m.metadata,
        "created_at": m.created_at.isoformat(),
        "updated_at": m.updated_at.isoformat(),
    }


@router.get("")
async def list_memories(
    tier: str | None = None,
    category: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    memory_tier = MemoryTier(tier) if tier else None
    items, total = await service.list_memories(
        user_id, tier=memory_tier, category=category, limit=limit, offset=offset
    )
    return {"items": [_memory_to_dict(m) for m in items], "total": total}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    body: CreateMemoryRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    pid = uuid.UUID(body.project_id) if body.project_id else None
    memory = await service.create(
        user_id,
        body.content,
        category=body.category,
        tier=MemoryTier(body.tier),
        importance=body.importance,
        tags=body.tags,
        project_id=pid,
        summary=body.summary,
    )
    return _memory_to_dict(memory)


@router.get("/{memory_id}")
async def get_memory(
    memory_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    memory = await service.get(memory_id, user_id)
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return _memory_to_dict(memory)


@router.patch("/{memory_id}")
async def update_memory(
    memory_id: uuid.UUID,
    body: UpdateMemoryRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    updates = body.model_dump(exclude_none=True)
    if "tier" in updates:
        updates["tier"] = MemoryTier(updates["tier"])
    memory = await service.update(memory_id, user_id, **updates)
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return _memory_to_dict(memory)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    deleted = await service.delete(memory_id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")


@router.post("/search")
async def search_memories(
    body: MemorySearchRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    tiers = [MemoryTier(t) for t in body.tiers] if body.tiers else None
    results = await service.search(
        user_id, body.query, limit=body.limit, tiers=tiers, min_importance=body.min_importance
    )
    return {
        "results": [
            {"memory": _memory_to_dict(entity), "score": round(score, 4)}
            for entity, score in results
        ]
    }
