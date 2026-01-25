"""Analytics service for admin dashboard."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from database import get_db_connection


def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Get analytics for a specific user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get user basic info
        cursor.execute("""
            SELECT user_id, username, email, is_admin, created_at, last_login
            FROM users WHERE user_id = ?
        """, (user_id,))

        user_row = cursor.fetchone()
        if not user_row:
            return {}

        # Get session stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_sessions,
                SUM(prompt_count) as total_prompts,
                AVG(duration_seconds) as avg_duration,
                MAX(last_activity) as last_activity
            FROM user_sessions
            WHERE user_id = ?
        """, (user_id,))

        session_stats = cursor.fetchone()

        # Get conversation count
        cursor.execute("""
            SELECT COUNT(*) FROM conversations WHERE user_id = ?
        """, (user_id,))
        conversation_count = cursor.fetchone()[0]

        return {
            'user_id': user_row[0],
            'username': user_row[1],
            'email': user_row[2],
            'is_admin': bool(user_row[3]),
            'created_at': user_row[4],
            'last_login': user_row[5],
            'total_sessions': session_stats[0] or 0,
            'total_prompts': session_stats[1] or 0,
            'avg_session_duration': round(session_stats[2], 2) if session_stats[2] else 0,
            'last_activity': session_stats[3],
            'total_conversations': conversation_count
        }


def get_all_users_analytics() -> List[Dict[str, Any]]:
    """Get analytics for all users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                u.user_id,
                u.username,
                u.email,
                u.is_admin,
                u.created_at,
                u.last_login,
                COUNT(DISTINCT s.session_id) as total_sessions,
                COALESCE(SUM(s.prompt_count), 0) as total_prompts,
                COALESCE(AVG(s.duration_seconds), 0) as avg_duration,
                MAX(s.last_activity) as last_activity,
                COUNT(DISTINCT c.conversation_id) as total_conversations
            FROM users u
            LEFT JOIN user_sessions s ON u.user_id = s.user_id
            LEFT JOIN conversations c ON u.user_id = c.user_id
            GROUP BY u.user_id
            ORDER BY u.created_at DESC
        """)

        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'is_admin': bool(row[3]),
                'created_at': row[4],
                'last_login': row[5],
                'total_sessions': row[6],
                'total_prompts': row[7],
                'avg_session_duration': round(row[8], 2) if row[8] else 0,
                'last_activity': row[9],
                'total_conversations': row[10]
            })

        return users


def get_user_sessions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get session history for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                session_id,
                started_at,
                ended_at,
                last_activity,
                prompt_count,
                duration_seconds
            FROM user_sessions
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (user_id, limit))

        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'session_id': row[0],
                'started_at': row[1],
                'ended_at': row[2],
                'last_activity': row[3],
                'prompt_count': row[4],
                'duration_seconds': row[5]
            })

        return sessions


def get_user_prompts(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get prompt history for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                m.message_id,
                m.conversation_id,
                m.content,
                m.created_at,
                c.title
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.conversation_id
            WHERE c.user_id = ? AND m.role = 'user'
            ORDER BY m.created_at DESC
            LIMIT ?
        """, (user_id, limit))

        prompts = []
        for row in cursor.fetchall():
            prompts.append({
                'message_id': row[0],
                'conversation_id': row[1],
                'content': row[2],
                'created_at': row[3],
                'conversation_title': row[4]
            })

        return prompts


def get_system_analytics() -> Dict[str, Any]:
    """Get overall system analytics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        total_users = cursor.fetchone()[0]

        # Users active today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_sessions
            WHERE last_activity >= ?
        """, (today,))
        active_today = cursor.fetchone()[0]

        # Users active this week
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) FROM user_sessions
            WHERE last_activity >= ?
        """, (week_ago,))
        active_this_week = cursor.fetchone()[0]

        # Total sessions
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        total_sessions = cursor.fetchone()[0]

        # Total prompts
        cursor.execute("SELECT SUM(prompt_count) FROM user_sessions")
        result = cursor.fetchone()[0]
        total_prompts = result if result else 0

        # Average session duration
        cursor.execute("SELECT AVG(duration_seconds) FROM user_sessions WHERE duration_seconds > 0")
        result = cursor.fetchone()[0]
        avg_session_duration = round(result, 2) if result else 0

        # Total conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]

        # Recent signups (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE created_at >= ?
        """, (week_ago,))
        recent_signups = cursor.fetchone()[0]

        return {
            'total_users': total_users,
            'active_today': active_today,
            'active_this_week': active_this_week,
            'total_sessions': total_sessions,
            'total_prompts': total_prompts,
            'avg_session_duration': avg_session_duration,
            'total_conversations': total_conversations,
            'recent_signups': recent_signups
        }


def create_session(user_id: str) -> str:
    """Create a new session for a user."""
    import uuid
    session_id = str(uuid.uuid4())

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_sessions (session_id, user_id, started_at, last_activity)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_id, datetime.now(), datetime.now()))

    return session_id


def update_session(session_id: str, increment_prompt: bool = False):
    """Update session activity and optionally increment prompt count."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if increment_prompt:
            cursor.execute("""
                UPDATE user_sessions
                SET last_activity = ?,
                    prompt_count = prompt_count + 1
                WHERE session_id = ?
            """, (datetime.now(), session_id))
        else:
            cursor.execute("""
                UPDATE user_sessions
                SET last_activity = ?
                WHERE session_id = ?
            """, (datetime.now(), session_id))


def end_session(session_id: str):
    """Mark a session as ended and calculate duration."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get session start time
        cursor.execute("""
            SELECT started_at FROM user_sessions WHERE session_id = ?
        """, (session_id,))

        result = cursor.fetchone()
        if result:
            started_at = datetime.fromisoformat(result[0]) if isinstance(result[0], str) else result[0]
            ended_at = datetime.now()
            duration = int((ended_at - started_at).total_seconds())

            cursor.execute("""
                UPDATE user_sessions
                SET ended_at = ?, duration_seconds = ?
                WHERE session_id = ?
            """, (ended_at, duration, session_id))
