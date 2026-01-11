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


def get_public_knowledge_tool():
    """
    Create and return a TavilySearch tool configured for ServiceNow documentation search.
    
    Returns:
        TavilySearch tool named 'consult_public_docs' configured to search
        only official ServiceNow domains with advanced search depth.
    """
    # Get API key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )
    
    # Get search domains from config (with fallback to defaults)
    try:
        domains = get_search_domains()
    except Exception:
        # Fallback to default domains if config fails
        domains = ['docs.servicenow.com', 'community.servicenow.com', 'developer.servicenow.com']
    
    # Build description with current domains
    domains_str = ', '.join(domains)
    
    # Instantiate TavilySearch with ServiceNow domain restrictions
    tool = TavilySearch(
        name="consult_public_docs",
        description=(
            "Search official ServiceNow documentation and community resources. "
            "WORKFLOW ORDER: Use this FIRST to establish the official ServiceNow standard before checking internal context. "
            f"Searches {domains_str}. "
            "Use this to find current ServiceNow documentation, error solutions, and standard processes. "
            "Always cite the URL in your response."
        ),
        max_results=5,
        include_domains=domains,
        search_depth='advanced',
        api_key=api_key
    )
    
    return tool
