"""Tavily AI search configuration management."""

from typing import List, Dict, Any, Optional
from database import get_db_connection
import json


def get_tavily_config(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Tavily search configuration.

    Args:
        user_id: If provided, get user-specific config, otherwise get global config

    Returns:
        Dictionary with included_domains, excluded_domains, and search_depth
    """
    config_type = "tavily_search"
    target_user_id = user_id if user_id else "global"

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get included domains
        cursor.execute("""
            SELECT config_value FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (target_user_id, config_type, "included_domains"))

        result = cursor.fetchone()
        included_domains = json.loads(result[0]) if result and result[0] else []

        # Get excluded domains
        cursor.execute("""
            SELECT config_value FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (target_user_id, config_type, "excluded_domains"))

        result = cursor.fetchone()
        excluded_domains = json.loads(result[0]) if result and result[0] else []

        # Get search depth
        cursor.execute("""
            SELECT config_value FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (target_user_id, config_type, "search_depth"))

        result = cursor.fetchone()
        search_depth = result[0] if result and result[0] else "basic"

        # Get max results
        cursor.execute("""
            SELECT config_value FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (target_user_id, config_type, "max_results"))

        result = cursor.fetchone()
        max_results = int(result[0]) if result and result[0] else 5

        return {
            "included_domains": included_domains,
            "excluded_domains": excluded_domains,
            "search_depth": search_depth,
            "max_results": max_results,
            "is_user_specific": user_id is not None
        }


def update_tavily_config(
    included_domains: Optional[List[str]] = None,
    excluded_domains: Optional[List[str]] = None,
    search_depth: Optional[str] = None,
    max_results: Optional[int] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Update Tavily search configuration.

    Args:
        included_domains: List of domains to include in search
        excluded_domains: List of domains to exclude from search
        search_depth: Search depth ("basic" or "advanced")
        max_results: Maximum number of results to return (1-20)
        user_id: If provided, update user-specific config, otherwise update global

    Returns:
        True if successful
    """
    config_type = "tavily_search"
    target_user_id = user_id if user_id else "global"

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Update included domains
        if included_domains is not None:
            cursor.execute("""
                INSERT INTO user_configs (user_id, config_type, config_key, config_value, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, config_type, config_key)
                DO UPDATE SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            """, (target_user_id, config_type, "included_domains",
                  json.dumps(included_domains), json.dumps(included_domains)))

        # Update excluded domains
        if excluded_domains is not None:
            cursor.execute("""
                INSERT INTO user_configs (user_id, config_type, config_key, config_value, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, config_type, config_key)
                DO UPDATE SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            """, (target_user_id, config_type, "excluded_domains",
                  json.dumps(excluded_domains), json.dumps(excluded_domains)))

        # Update search depth
        if search_depth is not None:
            if search_depth not in ["basic", "advanced"]:
                raise ValueError("search_depth must be 'basic' or 'advanced'")

            cursor.execute("""
                INSERT INTO user_configs (user_id, config_type, config_key, config_value, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, config_type, config_key)
                DO UPDATE SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            """, (target_user_id, config_type, "search_depth",
                  search_depth, search_depth))

        # Update max results
        if max_results is not None:
            if not 1 <= max_results <= 20:
                raise ValueError("max_results must be between 1 and 20")

            cursor.execute("""
                INSERT INTO user_configs (user_id, config_type, config_key, config_value, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, config_type, config_key)
                DO UPDATE SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            """, (target_user_id, config_type, "max_results",
                  str(max_results), str(max_results)))

        conn.commit()
        return True


def add_included_domain(domain: str, user_id: Optional[str] = None) -> bool:
    """Add a domain to the included domains list."""
    config = get_tavily_config(user_id)
    included_domains = config["included_domains"]

    if domain not in included_domains:
        included_domains.append(domain)
        return update_tavily_config(included_domains=included_domains, user_id=user_id)

    return False


def remove_included_domain(domain: str, user_id: Optional[str] = None) -> bool:
    """Remove a domain from the included domains list."""
    config = get_tavily_config(user_id)
    included_domains = config["included_domains"]

    if domain in included_domains:
        included_domains.remove(domain)
        return update_tavily_config(included_domains=included_domains, user_id=user_id)

    return False


def add_excluded_domain(domain: str, user_id: Optional[str] = None) -> bool:
    """Add a domain to the excluded domains list."""
    config = get_tavily_config(user_id)
    excluded_domains = config["excluded_domains"]

    if domain not in excluded_domains:
        excluded_domains.append(domain)
        return update_tavily_config(excluded_domains=excluded_domains, user_id=user_id)

    return False


def remove_excluded_domain(domain: str, user_id: Optional[str] = None) -> bool:
    """Remove a domain from the excluded domains list."""
    config = get_tavily_config(user_id)
    excluded_domains = config["excluded_domains"]

    if domain in excluded_domains:
        excluded_domains.remove(domain)
        return update_tavily_config(excluded_domains=excluded_domains, user_id=user_id)

    return False


def reset_tavily_config(user_id: Optional[str] = None) -> bool:
    """Reset Tavily configuration to defaults."""
    return update_tavily_config(
        included_domains=[],
        excluded_domains=[],
        search_depth="basic",
        max_results=5,
        user_id=user_id
    )


def get_tavily_search_kwargs(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Tavily search kwargs for use with TavilySearchResults tool.

    Args:
        user_id: User ID to get user-specific config, or None for global

    Returns:
        Dictionary with kwargs for TavilySearchResults
    """
    config = get_tavily_config(user_id)

    kwargs = {
        "max_results": config["max_results"],
    }

    if config["included_domains"]:
        kwargs["include_domains"] = config["included_domains"]

    if config["excluded_domains"]:
        kwargs["exclude_domains"] = config["excluded_domains"]

    # Note: search_depth is a parameter for the search() method, not initialization
    # Store it separately for use when calling search

    return kwargs
