"""Admin endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_admin, get_current_superadmin
from api.models.admin import AdminStatsResponse
from database import get_database_stats, get_db_connection
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
from user_config import (
    set_multi_agent_override,
    is_multi_agent_enabled,
    set_multi_agent_rollout_percentage,
    get_system_config
)
from api.services.multi_agent_service import get_handoff_analytics
from database import (
    get_agent_prompt,
    set_agent_prompt,
    reset_agent_prompt,
    get_all_agent_prompts,
    get_multi_agent_config,
    set_multi_agent_config,
    get_all_multi_agent_configs
)


class TavilyConfigUpdate(BaseModel):
    included_domains: Optional[List[str]] = None
    excluded_domains: Optional[List[str]] = None
    search_depth: Optional[str] = None
    max_results: Optional[int] = None


class DomainRequest(BaseModel):
    domain: str


class MultiAgentUserToggle(BaseModel):
    enabled: bool


class MultiAgentRollout(BaseModel):
    percentage: int


class AgentPromptUpdate(BaseModel):
    system_prompt: str


class MultiAgentConfigUpdate(BaseModel):
    config_value: str
    config_type: str = 'string'
    description: Optional[str] = None


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


# Multi-Agent Management Endpoints (Admin)

@router.get("/multi-agent/analytics")
def get_multi_agent_analytics(
    days: int = 30,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Get multi-agent system analytics."""
    return get_handoff_analytics(days=days)


@router.get("/multi-agent/rollout")
def get_multi_agent_rollout(current_user: dict = Depends(get_current_admin)) -> dict:
    """Get current multi-agent rollout percentage."""
    percentage = get_system_config('multi_agent_rollout_percentage', 0)
    return {
        "rollout_percentage": percentage,
        "status": "active" if percentage > 0 else "disabled"
    }


@router.put("/multi-agent/rollout")
def update_multi_agent_rollout(
    payload: MultiAgentRollout,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Update multi-agent rollout percentage."""
    if payload.percentage < 0 or payload.percentage > 100:
        raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")

    set_multi_agent_rollout_percentage(payload.percentage)
    return {
        "status": "success",
        "rollout_percentage": payload.percentage,
        "message": f"Multi-agent rollout set to {payload.percentage}%"
    }


@router.get("/multi-agent/users")
def get_multi_agent_users(current_user: dict = Depends(get_current_admin)) -> dict:
    """Get all users with their multi-agent status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.username, u.email, u.is_admin, u.is_superadmin, u.is_active,
                   uc.config_value as multi_agent_override
            FROM users u
            LEFT JOIN user_configs uc ON u.user_id = uc.user_id
                AND uc.config_type = 'features'
                AND uc.config_key = 'multi_agent_enabled'
            ORDER BY u.username
        """)

        users = []
        for row in cursor.fetchall():
            user_id = row[0]
            override = row[6]

            # Determine multi-agent status
            if override is not None:
                # User has explicit override
                multi_agent_status = override.lower() in ('true', '1')
                status_source = 'override'
            else:
                # Use system rollout
                multi_agent_status = is_multi_agent_enabled(user_id)
                status_source = 'rollout'

            users.append({
                'user_id': user_id,
                'username': row[1],
                'email': row[2],
                'is_admin': bool(row[3]),
                'is_superadmin': bool(row[4]),
                'is_active': bool(row[5]),
                'multi_agent_enabled': multi_agent_status,
                'multi_agent_source': status_source
            })

        return {
            "users": users,
            "total_count": len(users)
        }


@router.put("/multi-agent/users/{user_id}")
def toggle_multi_agent_for_user(
    user_id: str,
    payload: MultiAgentUserToggle,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Enable or disable multi-agent for a specific user."""
    # Verify user exists
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    set_multi_agent_override(user_id, payload.enabled)

    return {
        "status": "success",
        "user_id": user_id,
        "username": user[0],
        "multi_agent_enabled": payload.enabled,
        "message": f"Multi-agent {'enabled' if payload.enabled else 'disabled'} for user {user[0]}"
    }


@router.delete("/multi-agent/users/{user_id}/override")
def remove_multi_agent_override(
    user_id: str,
    current_user: dict = Depends(get_current_admin)
) -> dict:
    """Remove multi-agent override for a user (reverts to system rollout)."""
    from user_config import delete_user_config

    success = delete_user_config(user_id, 'features', 'multi_agent_enabled')

    if not success:
        raise HTTPException(status_code=404, detail="No override found for user")

    # Check new status based on rollout
    new_status = is_multi_agent_enabled(user_id)

    return {
        "status": "success",
        "user_id": user_id,
        "multi_agent_enabled": new_status,
        "multi_agent_source": "rollout",
        "message": "User override removed, now using system rollout percentage"
    }


# Superadmin-only endpoints

@router.get("/multi-agent/prompts")
def get_all_prompts(current_user: dict = Depends(get_current_superadmin)) -> dict:
    """Get all agent prompts (superadmin only)."""
    prompts = get_all_agent_prompts()

    # Add default prompts for agents that don't have custom ones
    agent_names = ['consultant', 'solution_architect', 'implementation', 'orchestrator']
    existing_agents = {p['agent_name'] for p in prompts}

    for agent_name in agent_names:
        if agent_name not in existing_agents:
            prompts.append({
                'agent_name': agent_name,
                'system_prompt': None,
                'is_active': False,
                'updated_at': None,
                'updated_by': None
            })

    return {"prompts": prompts}


@router.get("/multi-agent/prompts/{agent_name}")
def get_agent_prompt_endpoint(
    agent_name: str,
    current_user: dict = Depends(get_current_superadmin)
) -> dict:
    """Get system prompt for a specific agent (superadmin only)."""
    if agent_name not in ['consultant', 'solution_architect', 'implementation', 'orchestrator']:
        raise HTTPException(status_code=400, detail="Invalid agent name")

    custom_prompt = get_agent_prompt(agent_name)

    # Get default prompt from agent file
    default_prompt = _get_default_prompt(agent_name)

    return {
        "agent_name": agent_name,
        "custom_prompt": custom_prompt,
        "is_using_custom": custom_prompt is not None,
        "default_prompt": default_prompt
    }


@router.put("/multi-agent/prompts/{agent_name}")
def update_agent_prompt(
    agent_name: str,
    payload: AgentPromptUpdate,
    current_user: dict = Depends(get_current_superadmin)
) -> dict:
    """Update system prompt for an agent (superadmin only)."""
    if agent_name not in ['consultant', 'solution_architect', 'implementation', 'orchestrator']:
        raise HTTPException(status_code=400, detail="Invalid agent name")

    if not payload.system_prompt or len(payload.system_prompt) < 10:
        raise HTTPException(status_code=400, detail="System prompt too short")

    set_agent_prompt(agent_name, payload.system_prompt, current_user['user_id'])

    return {
        "status": "success",
        "agent_name": agent_name,
        "message": f"System prompt updated for {agent_name} agent"
    }


@router.post("/multi-agent/prompts/{agent_name}/reset")
def reset_agent_prompt_endpoint(
    agent_name: str,
    current_user: dict = Depends(get_current_superadmin)
) -> dict:
    """Reset agent prompt to default (superadmin only)."""
    if agent_name not in ['consultant', 'solution_architect', 'implementation', 'orchestrator']:
        raise HTTPException(status_code=400, detail="Invalid agent name")

    reset_agent_prompt(agent_name)

    return {
        "status": "success",
        "agent_name": agent_name,
        "message": f"System prompt reset to default for {agent_name} agent"
    }


@router.get("/multi-agent/config")
def get_all_configs(current_user: dict = Depends(get_current_superadmin)) -> dict:
    """Get all multi-agent configurations (superadmin only)."""
    configs = get_all_multi_agent_configs()
    return {"configs": configs}


@router.put("/multi-agent/config/{config_key}")
def update_config(
    config_key: str,
    payload: MultiAgentConfigUpdate,
    current_user: dict = Depends(get_current_superadmin)
) -> dict:
    """Update multi-agent configuration (superadmin only)."""
    set_multi_agent_config(
        config_key,
        payload.config_value,
        payload.config_type,
        payload.description,
        current_user['user_id']
    )

    return {
        "status": "success",
        "config_key": config_key,
        "message": f"Configuration '{config_key}' updated"
    }


def _get_default_prompt(agent_name: str) -> str:
    """Get default system prompt for an agent."""
    if agent_name == 'consultant':
        from multi_agent.agents.consultant import CONSULTANT_SYSTEM_PROMPT
        return CONSULTANT_SYSTEM_PROMPT
    elif agent_name == 'solution_architect':
        from multi_agent.agents.solution_architect import SOLUTION_ARCHITECT_SYSTEM_PROMPT
        return SOLUTION_ARCHITECT_SYSTEM_PROMPT
    elif agent_name == 'implementation':
        from multi_agent.agents.implementation import IMPLEMENTATION_SYSTEM_PROMPT
        return IMPLEMENTATION_SYSTEM_PROMPT
    elif agent_name == 'orchestrator':
        from multi_agent.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
        return ORCHESTRATOR_SYSTEM_PROMPT
    else:
        return ""
