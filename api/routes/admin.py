"""Admin endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_admin
from api.models.admin import AdminStatsResponse
from database import get_database_stats
from knowledge_base import get_knowledge_base_stats
from analytics_service import (
    get_all_users_analytics,
    get_user_analytics,
    get_user_sessions,
    get_user_prompts,
    get_system_analytics
)


router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(current_user: dict = Depends(get_current_admin)) -> AdminStatsResponse:
    """Return system statistics."""
    return AdminStatsResponse(
        database=get_database_stats(),
        knowledge_base=get_knowledge_base_stats(),
    )


@router.get("/analytics")
def get_analytics(current_user: dict = Depends(get_current_admin)) -> dict:
    """Return overall system analytics."""
    return get_system_analytics()


@router.get("/users")
def list_all_users(current_user: dict = Depends(get_current_admin)) -> List[dict]:
    """Return all users with their analytics."""
    return get_all_users_analytics()


@router.get("/users/{user_id}")
def get_user_details(user_id: str, current_user: dict = Depends(get_current_admin)) -> dict:
    """Return detailed analytics for a specific user."""
    user_data = get_user_analytics(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return user_data


@router.get("/users/{user_id}/sessions")
def get_user_session_history(
    user_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin)
) -> List[dict]:
    """Return session history for a user."""
    return get_user_sessions(user_id, limit)


@router.get("/users/{user_id}/prompts")
def get_user_prompt_history(
    user_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin)
) -> List[dict]:
    """Return prompt history for a user."""
    return get_user_prompts(user_id, limit)
