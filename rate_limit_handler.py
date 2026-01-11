"""Helper functions for handling API rate limits and displaying cooldown times."""

import re
from typing import Optional, Tuple
from datetime import datetime, timedelta


def extract_rate_limit_info(error_message: str, error_obj: Optional[Exception] = None) -> Optional[Tuple[str, int]]:
    """
    Extract rate limit information from error messages or exception objects.
    
    Args:
        error_message: The error message string
        error_obj: Optional exception object that might contain response headers
        
    Returns:
        Tuple of (api_name, cooldown_seconds) if rate limit detected, None otherwise
    """
    error_lower = error_message.lower()
    
    # Check for rate limit indicators
    rate_limit_patterns = [
        (r'rate.?limit', 'API'),
        (r'429', 'API'),
        (r'too many requests', 'API'),
        (r'quota exceeded', 'API'),
        (r'rate limit exceeded', 'API'),
    ]
    
    for pattern, api_name in rate_limit_patterns:
        if re.search(pattern, error_lower):
            # Try to extract retry-after or cooldown time
            cooldown_seconds = extract_cooldown_time(error_message, error_obj)
            return (api_name, cooldown_seconds)
    
    # Check for specific API rate limits
    if 'anthropic' in error_lower or 'claude' in error_lower:
        cooldown_seconds = extract_cooldown_time(error_message, error_obj)
        if cooldown_seconds:
            return ('Anthropic API', cooldown_seconds)
    
    if 'tavily' in error_lower:
        cooldown_seconds = extract_cooldown_time(error_message, error_obj)
        if cooldown_seconds:
            return ('Tavily API', cooldown_seconds)
    
    if 'openai' in error_lower:
        cooldown_seconds = extract_cooldown_time(error_message, error_obj)
        if cooldown_seconds:
            return ('OpenAI API', cooldown_seconds)
    
    return None


def extract_cooldown_time(error_message: str, error_obj: Optional[Exception] = None) -> int:
    """
    Extract cooldown time in seconds from error message or response headers.
    
    Args:
        error_message: The error message string
        error_obj: Optional exception object that might contain response headers
        
    Returns:
        Cooldown time in seconds, or 60 (default) if not found
    """
    # Try to extract from Retry-After header if available
    if error_obj and hasattr(error_obj, 'response'):
        response = getattr(error_obj, 'response', None)
        if response and hasattr(response, 'headers'):
            headers = response.headers
            retry_after = headers.get('Retry-After') or headers.get('retry-after')
            if retry_after:
                try:
                    return int(retry_after)
                except (ValueError, TypeError):
                    pass
    
    # Try to extract from error message
    # Pattern: "retry after X seconds" or "wait X seconds" or "X seconds"
    patterns = [
        r'retry[_\s]+after[_\s]+(\d+)[_\s]*(?:second|sec|s)',
        r'wait[_\s]+(\d+)[_\s]*(?:second|sec|s)',
        r'(\d+)[_\s]*(?:second|sec|s)[_\s]+(?:cooldown|wait|retry)',
        r'cooldown[_\s]+(?:of[_\s]+)?(\d+)[_\s]*(?:second|sec|s)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_message, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    # Default cooldown if not specified
    return 60


def format_cooldown_message(api_name: str, cooldown_seconds: int) -> str:
    """
    Format a user-friendly cooldown message.
    
    Args:
        api_name: Name of the API that hit rate limit
        cooldown_seconds: Number of seconds to wait
        
    Returns:
        Formatted message string
    """
    if cooldown_seconds < 60:
        time_str = f"{cooldown_seconds} seconds"
    elif cooldown_seconds < 3600:
        minutes = cooldown_seconds // 60
        seconds = cooldown_seconds % 60
        if seconds > 0:
            time_str = f"{minutes} minutes {seconds} seconds"
        else:
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        hours = cooldown_seconds // 3600
        minutes = (cooldown_seconds % 3600) // 60
        if minutes > 0:
            time_str = f"{hours} hour{'s' if hours > 1 else ''} {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            time_str = f"{hours} hour{'s' if hours > 1 else ''}"
    
    return f"⏱️ **Rate Limit Reached**\n\n{api_name} has reached its rate limit. Please wait **{time_str}** before trying again."


def get_rate_limit_info_from_exception(e: Exception) -> Optional[Tuple[str, int]]:
    """
    Extract rate limit info from an exception object.
    
    Args:
        e: Exception object that might contain rate limit information
        
    Returns:
        Tuple of (api_name, cooldown_seconds) if rate limit detected, None otherwise
    """
    error_message = str(e)
    
    # Check if it's an HTTP error with status 429
    if hasattr(e, 'response'):
        response = getattr(e, 'response', None)
        if response:
            status_code = getattr(response, 'status_code', None)
            if status_code == 429:
                # Try to get API name from URL or headers
                api_name = "API"
                if hasattr(response, 'url'):
                    url = str(response.url)
                    if 'anthropic' in url.lower() or 'claude' in url.lower():
                        api_name = "Anthropic API"
                    elif 'tavily' in url.lower():
                        api_name = "Tavily API"
                    elif 'openai' in url.lower():
                        api_name = "OpenAI API"
                
                cooldown_seconds = extract_cooldown_time(error_message, e)
                return (api_name, cooldown_seconds)
    
    # Fallback to message parsing
    return extract_rate_limit_info(error_message, e)
