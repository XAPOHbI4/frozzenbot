"""Authentication schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from .user import UserResponse


class LoginRequest(BaseModel):
    """Admin login request schema."""
    username: str = Field(..., min_length=3, max_length=50, description="Admin username")
    password: str = Field(..., min_length=6, max_length=100, description="Admin password")

    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class LoginResponse(TokenResponse):
    """Login response with user information."""
    refresh_token: str = Field(..., description="JWT refresh token")
    user: UserResponse = Field(..., description="User information")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": 1,
                    "telegram_id": 123456789,
                    "username": "admin",
                    "first_name": "Admin",
                    "last_name": "User",
                    "phone": None,
                    "is_admin": True,
                    "is_active": True,
                    "full_name": "Admin User",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            }
        }


class RefreshRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class TelegramInitData(BaseModel):
    """Telegram WebApp initData schema."""
    init_data: str = Field(..., description="Telegram WebApp initData string")

    @validator('init_data')
    def validate_init_data(cls, v):
        """Validate initData format."""
        if not v or len(v) < 10:
            raise ValueError('Invalid initData format')
        return v

    class Config:
        schema_extra = {
            "example": {
                "init_data": "query_id=AAH...&user=%7B%22id%22%3A123456789..."
            }
        }


class PasswordValidationResponse(BaseModel):
    """Password validation response schema."""
    valid: bool = Field(..., description="Whether password is valid")
    strength: str = Field(..., description="Password strength: weak, medium, strong")
    score: int = Field(..., description="Password strength score")
    errors: list = Field(default_factory=list, description="List of validation errors")

    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "strength": "strong",
                "score": 5,
                "errors": []
            }
        }


class AuthStatusResponse(BaseModel):
    """Authentication status response schema."""
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[UserResponse] = Field(None, description="User information if authenticated")
    permissions: list = Field(default_factory=list, description="User permissions")
    expires_at: Optional[str] = Field(None, description="Token expiration time")

    class Config:
        schema_extra = {
            "example": {
                "authenticated": True,
                "user": {
                    "id": 1,
                    "telegram_id": 123456789,
                    "username": "admin",
                    "first_name": "Admin",
                    "role": "admin"
                },
                "permissions": ["*"],
                "expires_at": "2024-01-01T01:30:00Z"
            }
        }