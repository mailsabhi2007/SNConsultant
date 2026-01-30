"""ServiceNow-specific tools for public documentation search."""

import os
import warnings
from typing import Optional
from dotenv import load_dotenv

# Suppress warnings from langchain_tavily about field name shadowing
# These are harmless warnings from the package itself
warnings.filterwarnings("ignore", message=".*Field name.*shadows an attribute in parent.*", category=UserWarning)

from langchain_tavily import TavilySearch  # type: ignore[import-untyped]

# Load environment variables
load_dotenv()

# Import config module (with fallback to defaults if import fails)
try:
    from config import get_search_domains
except ImportError:
    # Fallback if config module not available
    def get_search_domains():
        return ['docs.servicenow.com', 'community.servicenow.com', 'developer.servicenow.com']


def get_public_knowledge_tool(user_id: Optional[str] = None):
    """
    Create and return a TavilySearch tool configured for ServiceNow documentation search.

    Uses configuration from tavily_config.py to determine search parameters.
    Falls back to ServiceNow-specific defaults if no config is set.

    Args:
        user_id: Optional user ID to get user-specific configuration

    Returns:
        TavilySearch tool named 'consult_public_docs' configured based on admin settings
    """
    # Get API key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )

    # Try to import and use tavily_config
    try:
        from tavily_config import get_tavily_config
        config = get_tavily_config(user_id=user_id)

        # Use configured domains or fall back to ServiceNow defaults
        if config["included_domains"]:
            domains = config["included_domains"]
        else:
            # Default to ServiceNow domains if no included domains configured
            try:
                domains = get_search_domains()
            except Exception:
                domains = ['docs.servicenow.com', 'community.servicenow.com', 'developer.servicenow.com']

        excluded_domains = config.get("excluded_domains", [])
        search_depth = config.get("search_depth", "advanced")
        max_results = config.get("max_results", 5)
    except Exception:
        # Fallback to defaults if tavily_config import fails
        try:
            domains = get_search_domains()
        except Exception:
            domains = ['docs.servicenow.com', 'community.servicenow.com', 'developer.servicenow.com']
        excluded_domains = []
        search_depth = "advanced"
        max_results = 5

    # Build description with current domains
    domains_str = ', '.join(domains)

    # Prepare kwargs for TavilySearch
    tavily_kwargs = {
        "name": "consult_public_docs",
        "description": (
            "Search official ServiceNow documentation and community resources. "
            "WORKFLOW ORDER: Use this FIRST to establish the official ServiceNow standard before checking internal context. "
            f"Searches {domains_str}. "
            "Use this to find current ServiceNow documentation, error solutions, and standard processes. "
            "Always cite the URL in your response."
        ),
        "max_results": max_results,
        "search_depth": search_depth,
        "api_key": api_key
    }

    # Only add domain filters if configured
    if domains:
        tavily_kwargs["include_domains"] = domains
    if excluded_domains:
        tavily_kwargs["exclude_domains"] = excluded_domains

    # Instantiate TavilySearch with configuration
    tool = TavilySearch(**tavily_kwargs)

    return tool
