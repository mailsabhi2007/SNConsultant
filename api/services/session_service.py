"""Session tracking service."""

from datetime import datetime, timedelta
from typing import Optional
from analytics_service import create_session, update_session, end_session
from database import get_db_connection


def get_or_create_session(user_id: str, session_id: Optional[str] = None) -> str:
    """Get existing active session or create a new one."""
    # If session_id provided, check if it's still active (within last 30 minutes)
    if session_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, last_activity
                FROM user_sessions
                WHERE session_id = ? AND user_id = ?
            """, (session_id, user_id))

            result = cursor.fetchone()
            if result:
                last_activity = datetime.fromisoformat(result[1]) if isinstance(result[1], str) else result[1]
                # If last activity was within 30 minutes, reuse session
                if datetime.now() - last_activity < timedelta(minutes=30):
                    return session_id
                else:
                    # Session expired, end it
                    end_session(session_id)

    # Create new session
    return create_session(user_id)


def track_prompt(session_id: str):
    """Track a prompt in the session."""
    update_session(session_id, increment_prompt=True)


def update_activity(session_id: str):
    """Update session last activity."""
    update_session(session_id, increment_prompt=False)
