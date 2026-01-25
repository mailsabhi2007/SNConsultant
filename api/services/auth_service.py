"""Authentication helpers for FastAPI."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError

from database import get_db_connection
from user_manager import authenticate_user, create_user, get_user, get_user_by_username


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _get_secret_key() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret
    # Fallback to a deterministic but overridable value for local dev
    return "change-me-in-env"


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT and return user data."""
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            return None
        user = get_user(user_id)
        if not user:
            return None
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user.get("email"),
            "is_admin": bool(payload.get("is_admin", False)),
        }
    except JWTError:
        return None


def register_user(username: str, password: str, email: Optional[str] = None) -> str:
    """Create a new user and return user_id."""
    return create_user(username=username, password=password, email=email)


def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate and return user payload."""
    user_id = authenticate_user(username, password)
    if not user_id:
        return None
    user = get_user(user_id)
    if not user:
        return None

    # Check if this should be an admin (first user or username-based)
    is_admin = user.get("is_admin", False) or is_admin_user(user["user_id"], user["username"])

    # Update is_admin in database if it changed
    if is_admin and not user.get("is_admin", False):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user.get("email"),
        "is_admin": is_admin,
    }


def is_admin_user(user_id: str, username: str) -> bool:
    """Determine if user should have admin access."""
    if username.lower() in {"admin", "superadmin"}:
        return True

    # First user created gets admin privileges
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users ORDER BY created_at ASC LIMIT 1")
        row = cursor.fetchone()
        if row and row[0] == user_id:
            return True

    return False


def get_user_by_name(username: str) -> Optional[Dict[str, Any]]:
    """Helper to lookup user by username."""
    return get_user_by_username(username)
