"""Category schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class CategoryCreateRequest(BaseModel):
    """Category creation request schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    image_url: Optional[str] = Field(None, max_length=500, description="Category image URL")
    is_active: bool = Field(True, description="Category active status")
    sort_order: int = Field(0, description="Sort order")

    @validator('image_url')
    def validate_image_url(cls, v):
        """Validate image URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Image URL must start with http:// or https://')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Замороженные овощи",
                "description": "Свежие замороженные овощи высокого качества",
                "image_url": "https://example.com/vegetables.jpg",
                "is_active": True,
                "sort_order": 0
            }
        }


class CategoryUpdateRequest(BaseModel):
    """Category update request schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, max_length=1000, description="Category description")
    image_url: Optional[str] = Field(None, max_length=500, description="Category image URL")
    is_active: Optional[bool] = Field(None, description="Category active status")
    sort_order: Optional[int] = Field(None, description="Sort order")

    @validator('image_url')
    def validate_image_url(cls, v):
        """Validate image URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Image URL must start with http:// or https://')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Замороженные овощи",
                "description": "Свежие замороженные овощи высокого качества",
                "image_url": "https://example.com/vegetables.jpg",
                "is_active": True,
                "sort_order": 1
            }
        }


class CategoryResponse(BaseModel):
    """Category response schema."""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    image_url: Optional[str] = Field(None, description="Category image URL")
    is_active: bool = Field(..., description="Category active status")
    sort_order: int = Field(..., description="Sort order")
    products_count: int = Field(..., description="Number of products in category")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Замороженные овощи",
                "description": "Свежие замороженные овощи высокого качества",
                "image_url": "https://example.com/vegetables.jpg",
                "is_active": True,
                "sort_order": 0,
                "products_count": 15,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class CategoryListResponse(BaseModel):
    """Category list response schema."""
    items: list[CategoryResponse] = Field(..., description="List of categories")

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "Замороженные овощи",
                        "description": "Свежие замороженные овощи высокого качества",
                        "image_url": "https://example.com/vegetables.jpg",
                        "is_active": True,
                        "sort_order": 0,
                        "products_count": 15,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }