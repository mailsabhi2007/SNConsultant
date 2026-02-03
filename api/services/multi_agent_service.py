"""Multi-agent service wrapper for API."""
from typing import Optional, Dict, Any
from multi_agent.graph import MultiAgentOrchestrator
from database import get_db_connection
from langchain_core.messages import AIMessage


async def send_multi_agent_message(
    message: str,
    user_id: str,
    conversation_id: Optional[int] = None
) -> Dict[str, Any]:
    """Send message to multi-agent orchestrator and return result.

    Args:
        message: User message
        user_id: User ID
        conversation_id: Optional conversation ID for history tracking

    Returns:
        Dictionary with response and metadata
    """
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator(user_id=user_id)

    # Invoke multi-agent system
    result = await orchestrator.invoke(message=message, conversation_id=conversation_id)

    # Extract response text
    response_text = result.get("response", "")

    # Save handoff records to database
    handoff_history = result.get("handoff_history", [])
    if handoff_history and conversation_id:
        _save_handoff_records(conversation_id, handoff_history)

    return {
        "response": response_text,
        "conversation_id": result.get("conversation_id"),
        "is_cached": result.get("is_cached", False),
        "similarity": result.get("similarity"),
        "judge_result": None,  # TODO: Add judge evaluation for multi-agent
        "current_agent": result.get("current_agent"),
        "handoff_count": len(handoff_history)
    }


def _save_handoff_records(conversation_id: int, handoff_history: list) -> None:
    """Save handoff records to database for analytics.

    Args:
        conversation_id: Conversation ID
        handoff_history: List of handoff records
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        for handoff in handoff_history:
            cursor.execute("""
                INSERT INTO agent_handoffs (
                    conversation_id,
                    from_agent,
                    to_agent,
                    reason,
                    context_summary,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                handoff.get("from_agent"),
                handoff.get("to_agent"),
                handoff.get("reason"),
                handoff.get("context_summary"),
                handoff.get("timestamp")
            ))


def get_handoff_analytics(days: int = 30) -> Dict[str, Any]:
    """Get analytics on agent handoffs.

    Args:
        days: Number of days to look back

    Returns:
        Dictionary with analytics data
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total handoffs
        cursor.execute("""
            SELECT COUNT(*) FROM agent_handoffs
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))
        total_handoffs = cursor.fetchone()[0]

        # Handoffs by path
        cursor.execute("""
            SELECT from_agent, to_agent, COUNT(*) as count
            FROM agent_handoffs
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY from_agent, to_agent
            ORDER BY count DESC
        """, (days,))
        handoff_paths = [
            {"from": row[0], "to": row[1], "count": row[2]}
            for row in cursor.fetchall()
        ]

        # Conversations with handoffs
        cursor.execute("""
            SELECT COUNT(DISTINCT conversation_id)
            FROM agent_handoffs
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))
        conversations_with_handoffs = cursor.fetchone()[0]

        # Total conversations (from messages table)
        cursor.execute("""
            SELECT COUNT(DISTINCT conversation_id)
            FROM messages
            WHERE created_at >= datetime('now', '-' || ? || ' days')
        """, (days,))
        total_conversations = cursor.fetchone()[0]

        # Calculate handoff rate
        handoff_rate = (conversations_with_handoffs / total_conversations * 100) if total_conversations > 0 else 0

        return {
            "total_handoffs": total_handoffs,
            "handoff_paths": handoff_paths,
            "conversations_with_handoffs": conversations_with_handoffs,
            "total_conversations": total_conversations,
            "handoff_rate_percentage": round(handoff_rate, 2),
            "days": days
        }
