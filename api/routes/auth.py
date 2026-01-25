"""Authentication endpoints."""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Response, status, Depends, Request

from api.dependencies import get_current_user
from api.models.auth import LoginRequest, RegisterRequest, UserResponse
from api.services.auth_service import (
    create_access_token,
    login_user,
    register_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from analytics_service import end_session


router = APIRouter()


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response) -> UserResponse:
    """Authenticate user and set cookie."""
    user = login_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        {"user_id": user["user_id"], "username": user["username"], "is_admin": user["is_admin"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return UserResponse(**user)


@router.post("/register", response_model=UserResponse)
def register(payload: RegisterRequest) -> UserResponse:
    """Create a new user."""
    try:
        user_id = register_user(payload.username, payload.password, payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UserResponse(user_id=user_id, username=payload.username, email=payload.email, is_admin=False)


@router.post("/logout")
def logout(request: Request, response: Response) -> dict:
    """Clear access token cookie and end session."""
    # End the session if exists
    session_id = request.cookies.get("session_id")
    if session_id:
        try:
            end_session(session_id)
        except:
            pass  # Session might not exist, that's okay

    response.delete_cookie("access_token")
    response.delete_cookie("session_id")
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """Return current user."""
    return UserResponse(**current_user)
