"""Auth request/response models."""

from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    email: EmailStr = Field(..., description="Valid email address required")


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    is_superadmin: bool = False
