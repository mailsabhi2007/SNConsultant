"""Admin endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

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
from tavily_config import (
    get_tavily_config,
    update_tavily_config,
    add_included_domain,
    remove_included_domain,
    add_excluded_domain,
    remove_excluded_domain,
    reset_tavily_config
)


class TavilyConfigUpdate(BaseModel):
    included_domains: Optional[List[str]] = None
    excluded_domains: Optional[List[str]] = None
    search_depth: Optional[str] = None
    max_results: Optional[int] = None


class DomainRequest(BaseModel):
    domain: str


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


# Tavily configuration endpoints
@router.get("/tavily-config")
def get_tavily_configuration(current_user: dict = Depends(get_current_admin)) -> dict:
    """Get global Tavily search configuration."""
    return get_tavily_config(user_id=None)


@router.put("/tavily-config")
def update_tavily_configuration(
    config: TavilyConfigUpdate,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Update global Tavily search configuration."""
    try:
        update_tavily_config(
            included_domains=config.included_domains,
            excluded_domains=config.excluded_domains,
            search_depth=config.search_depth,
            max_results=config.max_results,
            user_id=None
        )
        return {"status": "success", "config": get_tavily_config(user_id=None)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tavily-config/included-domains")
def add_included_domain_endpoint(
    request: DomainRequest,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Add a domain to the included domains list."""
    success = add_included_domain(request.domain, user_id=None)
    if success:
        return {"status": "success", "config": get_tavily_config(user_id=None)}
    return {"status": "already_exists", "config": get_tavily_config(user_id=None)}


@router.delete("/tavily-config/included-domains/{domain}")
def remove_included_domain_endpoint(
    domain: str,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Remove a domain from the included domains list."""
    success = remove_included_domain(domain, user_id=None)
    if success:
        return {"status": "success", "config": get_tavily_config(user_id=None)}
    raise HTTPException(status_code=404, detail="Domain not found")


@router.post("/tavily-config/excluded-domains")
def add_excluded_domain_endpoint(
    request: DomainRequest,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Add a domain to the excluded domains list."""
    success = add_excluded_domain(request.domain, user_id=None)
    if success:
        return {"status": "success", "config": get_tavily_config(user_id=None)}
    return {"status": "already_exists", "config": get_tavily_config(user_id=None)}


@router.delete("/tavily-config/excluded-domains/{domain}")
def remove_excluded_domain_endpoint(
    domain: str,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Remove a domain from the excluded domains list."""
    success = remove_excluded_domain(domain, user_id=None)
    if success:
        return {"status": "success", "config": get_tavily_config(user_id=None)}
    raise HTTPException(status_code=404, detail="Domain not found")


@router.post("/tavily-config/reset")
def reset_tavily_configuration(current_user: dict = Depends(get_current_admin)) -> dict:
    """Reset Tavily configuration to defaults."""
    reset_tavily_config(user_id=None)
    return {"status": "success", "config": get_tavily_config(user_id=None)}
