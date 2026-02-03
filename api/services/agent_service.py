"""Agent service wrapper for API."""

from typing import Optional, Dict, Any

from agent import get_agent
from user_config import is_multi_agent_enabled


async def send_message(message: str, user_id: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    """Send message to agent and return result.

    Routes to multi-agent system if enabled for user, otherwise uses legacy single agent.

    Args:
        message: User message
        user_id: User ID
        conversation_id: Optional conversation ID

    Returns:
        Dictionary with response and metadata
    """
    # Check if multi-agent is enabled for this user
    if is_multi_agent_enabled(user_id):
        # Route to multi-agent system
        from api.services.multi_agent_service import send_multi_agent_message
        return await send_multi_agent_message(message, user_id, conversation_id)
    else:
        # Use legacy single agent
        agent = get_agent(user_id=user_id)
        result = await agent.invoke(message=message, conversation_id=conversation_id)
        response_text = ""
        if result.get("messages"):
            last_message = result["messages"][-1]
            response_text = getattr(last_message, "content", "") or ""

        return {
            "response": response_text,
            "conversation_id": result.get("conversation_id"),
            "is_cached": bool(result.get("is_cached", False)),
            "judge_result": result.get("judge_result"),
        }
