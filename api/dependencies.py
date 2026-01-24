"""FastAPI dependencies for authentication and authorization."""

from fastapi import HTTPException, Request, status

from api.services.auth_service import verify_access_token


def get_current_user(request: Request) -> dict:
    """Get current user from access token cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = verify_access_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user


def get_current_admin(request: Request) -> dict:
    """Ensure the current user is an admin."""
    user = get_current_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
