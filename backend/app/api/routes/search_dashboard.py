import uuid

from fastapi import APIRouter, Depends, Query

from app.application.dashboard.dashboard_service import DashboardService
from app.application.search.search_service import SearchService
from app.dependencies import get_current_user_id, get_dashboard_service, get_search_service

router = APIRouter(tags=["search", "dashboard"])


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=1),
    types: str = Query("memories,ideas,conversations"),
    limit: int = Query(20, ge=1, le=50),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: SearchService = Depends(get_search_service),
):
    type_list = [t.strip() for t in types.split(",") if t.strip()]
    results = await service.search(user_id, q, types=type_list, limit=limit)
    return {"results": results}


@router.get("/dashboard")
async def get_dashboard(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_dashboard(user_id)
