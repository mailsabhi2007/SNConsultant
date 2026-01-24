"""Conversation history management."""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from database import get_db_connection


def generate_conversation_title(user_message: str, assistant_response: str) -> str:
    """
    Generate a short, descriptive title for a conversation using LLM.

    Args:
        user_message: The first user message
        assistant_response: The assistant's response

    Returns:
        A short title (max 50 chars)
    """
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage
        from user_config import get_system_config

        # Get API key
        api_key = get_system_config("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # Fallback to simple extraction
            return _extract_simple_title(user_message)

        # Use a fast, cheap model for title generation
        model = ChatAnthropic(
            model="claude-3-5-haiku-20241022",
            api_key=api_key,
            temperature=0,
            max_tokens=50,
        )

        prompt = f"""Generate a very short title (max 5 words) for this conversation.
The title should capture the main topic. Return ONLY the title, no quotes or punctuation.

User asked: {user_message[:200]}

Examples of good titles:
- "Business Rule Best Practices"
- "Incident Table Schema"
- "Error Log Analysis"
- "ServiceNow API Integration"
- "Flow Designer Troubleshooting"
"""

        response = model.invoke([
            SystemMessage(content="You are a helpful assistant that generates very short, descriptive titles."),
            HumanMessage(content=prompt)
        ])

        title = response.content.strip().strip('"\'')
        # Ensure max length
        if len(title) > 50:
            title = title[:47] + "..."

        return title

    except Exception as e:
        # Fallback to simple extraction on any error
        print(f"Title generation failed: {e}")
        return _extract_simple_title(user_message)


def _extract_simple_title(user_message: str) -> str:
    """Extract a simple title from the user message as fallback."""
    # Take first sentence or first 50 chars
    message = user_message.strip()

    # Find first sentence end
    for end_char in ['.', '?', '!', '\n']:
        pos = message.find(end_char)
        if 0 < pos < 50:
            message = message[:pos]
            break

    # Truncate if still too long
    if len(message) > 50:
        message = message[:47] + "..."

    return message or "New Conversation"


def create_conversation(user_id: str, title: Optional[str] = None) -> int:
    """
    Create a new conversation.
    
    Args:
        user_id: User ID
        title: Optional conversation title
        
    Returns:
        conversation_id
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (user_id, title, started_at, last_activity, message_count)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
        """, (user_id, title))
        
        return cursor.lastrowid


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Add a message to a conversation.
    
    Args:
        conversation_id: Conversation ID
        role: Message role ('user', 'assistant', 'system', 'tool')
        content: Message content
        tool_calls: Optional tool calls (will be JSON-encoded)
        metadata: Optional metadata (will be JSON-encoded)
        
    Returns:
        message_id
    """
    tool_calls_str = json.dumps(tool_calls) if tool_calls else None
    metadata_str = json.dumps(metadata) if metadata else None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert message
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, tool_calls, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (conversation_id, role, content, tool_calls_str, metadata_str))
        
        message_id = cursor.lastrowid
        
        # Update conversation message count and last activity
        cursor.execute("""
            UPDATE conversations
            SET message_count = message_count + 1,
                last_activity = CURRENT_TIMESTAMP
            WHERE conversation_id = ?
        """, (conversation_id,))
        
        return message_id


def get_conversation(conversation_id: int, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get conversation details.
    
    Args:
        conversation_id: Conversation ID
        user_id: Optional user ID for security check
        
    Returns:
        Conversation dictionary or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT conversation_id, user_id, title, started_at, last_activity, message_count
                FROM conversations
                WHERE conversation_id = ? AND user_id = ?
            """, (conversation_id, user_id))
        else:
            cursor.execute("""
                SELECT conversation_id, user_id, title, started_at, last_activity, message_count
                FROM conversations
                WHERE conversation_id = ?
            """, (conversation_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'conversation_id': row[0],
            'user_id': row[1],
            'title': row[2],
            'started_at': row[3],
            'last_activity': row[4],
            'message_count': row[5]
        }


def get_conversation_messages(conversation_id: int) -> List[Dict[str, Any]]:
    """
    Get all messages for a conversation.
    
    Returns:
        List of message dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT message_id, role, content, tool_calls, metadata, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            tool_calls = json.loads(row[3]) if row[3] else None
            metadata = json.loads(row[4]) if row[4] else None
            
            messages.append({
                'message_id': row[0],
                'role': row[1],
                'content': row[2],
                'tool_calls': tool_calls,
                'metadata': metadata,
                'created_at': row[5]
            })
        
        return messages


def list_user_conversations(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List all conversations for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversation dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT conversation_id, title, started_at, last_activity, message_count
            FROM conversations
            WHERE user_id = ?
            ORDER BY last_activity DESC
            LIMIT ?
        """, (user_id, limit))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'conversation_id': row[0],
                'title': row[1],
                'started_at': row[2],
                'last_activity': row[3],
                'message_count': row[4]
            })
        
        return conversations


def update_conversation_title(conversation_id: int, title: str, user_id: Optional[str] = None) -> bool:
    """Update conversation title."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                UPDATE conversations
                SET title = ?
                WHERE conversation_id = ? AND user_id = ?
            """, (title, conversation_id, user_id))
        else:
            cursor.execute("""
                UPDATE conversations
                SET title = ?
                WHERE conversation_id = ?
            """, (title, conversation_id))
        
        return cursor.rowcount > 0


def delete_conversation(conversation_id: int, user_id: Optional[str] = None) -> bool:
    """Delete a conversation (cascade deletes messages)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                DELETE FROM conversations
                WHERE conversation_id = ? AND user_id = ?
            """, (conversation_id, user_id))
        else:
            cursor.execute("""
                DELETE FROM conversations
                WHERE conversation_id = ?
            """, (conversation_id,))
        
        return cursor.rowcount > 0


def search_conversations(user_id: str, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search conversations by title or message content.
    
    Args:
        user_id: User ID
        query: Search query
        limit: Maximum results
        
    Returns:
        List of matching conversations
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        
        # Search in titles and message content
        cursor.execute("""
            SELECT DISTINCT c.conversation_id, c.title, c.started_at, c.last_activity, c.message_count
            FROM conversations c
            LEFT JOIN messages m ON c.conversation_id = m.conversation_id
            WHERE c.user_id = ?
            AND (
                c.title LIKE ? OR
                m.content LIKE ?
            )
            ORDER BY c.last_activity DESC
            LIMIT ?
        """, (user_id, search_pattern, search_pattern, limit))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'conversation_id': row[0],
                'title': row[1],
                'started_at': row[2],
                'last_activity': row[3],
                'message_count': row[4]
            })
        
        return conversations
