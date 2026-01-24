"""Agent service wrapper for API."""

from typing import Optional, Dict, Any

from agent import get_agent


async def send_message(message: str, user_id: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
    """Send message to agent and return result."""
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
