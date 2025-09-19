"""User schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class UserCreateRequest(BaseModel):
    """User creation request schema."""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, max_length=255, description="Telegram username")
    first_name: str = Field(..., min_length=1, max_length=255, description="First name")
    last_name: Optional[str] = Field(None, max_length=255, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    @validator('telegram_id')
    def validate_telegram_id(cls, v):
        """Validate Telegram ID is positive."""
        if v <= 0:
            raise ValueError('Telegram ID must be positive')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.startswith('+'):
            raise ValueError('Phone number must start with +')
        return v

    class Config:
        schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890"
            }
        }


class UserUpdateRequest(BaseModel):
    """User update request schema."""
    username: Optional[str] = Field(None, max_length=255, description="Telegram username")
    first_name: Optional[str] = Field(None, min_length=1, max_length=255, description="First name")
    last_name: Optional[str] = Field(None, max_length=255, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    is_active: Optional[bool] = Field(None, description="User active status")

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not v.startswith('+'):
            raise ValueError('Phone number must start with +')
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe_new",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "is_active": True
            }
        }


class UserResponse(BaseModel):
    """User response schema."""
    id: int = Field(..., description="User ID")
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: str = Field(..., description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone: Optional[str] = Field(None, description="Phone number")
    is_admin: bool = Field(..., description="Admin status")
    is_active: bool = Field(..., description="Active status")
    full_name: str = Field(..., description="Full name (computed)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "telegram_id": 123456789,
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "is_admin": False,
                "is_active": True,
                "full_name": "John Doe",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class UserListResponse(BaseModel):
    """Paginated user list response schema."""
    items: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    per_page: int = Field(..., description="Items per page")

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "telegram_id": 123456789,
                        "username": "johndoe",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone": "+1234567890",
                        "is_admin": False,
                        "is_active": True,
                        "full_name": "John Doe",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "pages": 1,
                "per_page": 20
            }
        }