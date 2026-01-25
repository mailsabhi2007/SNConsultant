"""Database management for user profiles, history, cache, and configurations."""

import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager

# Database file path
DB_PATH = Path("./data/app.db")
DB_DIR = Path("./data")


def ensure_db_dir():
    """Ensure database directory exists."""
    DB_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    ensure_db_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database with all required tables."""
    ensure_db_dir()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # User configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_configs (
                config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                config_type TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, config_type, config_key)
            )
        """)
        
        # User documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chunk_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Learned preferences per user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_learned_preferences (
                preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preference_text TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Conversation history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
            )
        """)
        
        # Semantic cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                query_embedding BLOB,
                query_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                model_name TEXT,
                temperature REAL,
                metadata TEXT,
                hit_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Hallucination detection results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hallucination_checks (
                check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                judge_model TEXT NOT NULL,
                hallucination_score REAL NOT NULL,
                is_hallucination BOOLEAN,
                flagged_sections TEXT,
                suggested_corrections TEXT,
                judge_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
            )
        """)

        # User sessions for analytics tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                prompt_count INTEGER DEFAULT 0,
                duration_seconds INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_configs_user_type 
            ON user_configs(user_id, config_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user 
            ON conversations(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages(conversation_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_semantic_cache_user 
            ON semantic_cache(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires
            ON semantic_cache(expires_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user
            ON user_sessions(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_started
            ON user_sessions(started_at)
        """)

        conn.commit()
        print("Database initialized successfully")


def get_database_stats() -> Dict[str, Any]:
    """Get statistics about the database."""
    stats = {}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        # Count active users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        stats['active_users'] = cursor.fetchone()[0]
        
        # Count conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        stats['total_conversations'] = cursor.fetchone()[0]
        
        # Count messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = cursor.fetchone()[0]
        
        # Count cache entries
        cursor.execute("SELECT COUNT(*) FROM semantic_cache")
        stats['cache_entries'] = cursor.fetchone()[0]
        
        # Cache hit count
        cursor.execute("SELECT SUM(hit_count) FROM semantic_cache")
        result = cursor.fetchone()[0]
        stats['total_cache_hits'] = result if result else 0
        
        # Count hallucination checks
        cursor.execute("SELECT COUNT(*) FROM hallucination_checks")
        stats['hallucination_checks'] = cursor.fetchone()[0]
        
        # Count flagged hallucinations
        cursor.execute("SELECT COUNT(*) FROM hallucination_checks WHERE is_hallucination = 1")
        stats['flagged_hallucinations'] = cursor.fetchone()[0]

        # Count sessions
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        stats['total_sessions'] = cursor.fetchone()[0]

        # Average session duration
        cursor.execute("SELECT AVG(duration_seconds) FROM user_sessions WHERE duration_seconds > 0")
        result = cursor.fetchone()[0]
        stats['avg_session_duration'] = round(result, 2) if result else 0

        # Total prompts across all sessions
        cursor.execute("SELECT SUM(prompt_count) FROM user_sessions")
        result = cursor.fetchone()[0]
        stats['total_prompts'] = result if result else 0

    return stats


if __name__ == "__main__":
    # Initialize database on direct execution
    init_database()
    stats = get_database_stats()
    print("\nDatabase Statistics:")
    print(json.dumps(stats, indent=2))
