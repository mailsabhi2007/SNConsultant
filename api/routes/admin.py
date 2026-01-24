"""Admin endpoints."""

from fastapi import APIRouter, Depends

from api.dependencies import get_current_admin
from api.models.admin import AdminStatsResponse
from database import get_database_stats
from knowledge_base import get_knowledge_base_stats


router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(current_user: dict = Depends(get_current_admin)) -> AdminStatsResponse:
    """Return system statistics."""
    return AdminStatsResponse(
        database=get_database_stats(),
        knowledge_base=get_knowledge_base_stats(),
    )
