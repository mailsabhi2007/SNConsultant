"""User authentication and management."""

import bcrypt
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from database import get_db_connection


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_user(username: str, password: str, email: Optional[str] = None) -> str:
    """
    Create a new user.
    
    Args:
        username: Unique username
        password: Plain text password (will be hashed)
        email: Optional email address
        
    Returns:
        user_id: The created user's ID
        
    Raises:
        ValueError: If username already exists
    """
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise ValueError(f"Username '{username}' already exists")
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash, email, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, username, password_hash, email, datetime.now(), True))
        
        return user_id


def authenticate_user(username: str, password: str) -> Optional[str]:
    """
    Authenticate a user and return their user_id.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        user_id if authentication successful, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, password_hash FROM users 
            WHERE username = ? AND is_active = 1
        """, (username,))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        user_id, password_hash = result
        
        if verify_password(password, password_hash):
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE user_id = ?
            """, (datetime.now(), user_id))
            return user_id
        
        return None


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user information by user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, email, created_at, last_login, is_active
            FROM users WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'user_id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4],
            'is_active': bool(row[5])
        }


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user information by username."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, username, email, created_at, last_login, is_active
            FROM users WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'user_id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4],
            'is_active': bool(row[5])
        }


def update_user(user_id: str, email: Optional[str] = None, password: Optional[str] = None) -> bool:
    """
    Update user information.
    
    Args:
        user_id: User ID
        email: New email (optional)
        password: New password (optional, will be hashed)
        
    Returns:
        True if update successful, False if user not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            return False
        
        # Update email if provided
        if email is not None:
            cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, user_id))
        
        # Update password if provided
        if password is not None:
            password_hash = hash_password(password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (password_hash, user_id))
        
        return True


def deactivate_user(user_id: str) -> bool:
    """Deactivate a user account."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def activate_user(user_id: str) -> bool:
    """Activate a user account."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def list_users(active_only: bool = True) -> List[Dict[str, Any]]:
    """List all users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("""
                SELECT user_id, username, email, created_at, last_login, is_active
                FROM users WHERE is_active = 1
                ORDER BY created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT user_id, username, email, created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'created_at': row[3],
                'last_login': row[4],
                'is_active': bool(row[5])
            })
        
        return users
