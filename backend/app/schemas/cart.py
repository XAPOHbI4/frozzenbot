"""Cart schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from .product import ProductResponse


class CartItemCreateRequest(BaseModel):
    """Cart item creation request schema."""
    telegram_id: int = Field(..., description="Telegram user ID")
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Item quantity")

    @validator('telegram_id')
    def validate_telegram_id(cls, v):
        """Validate Telegram ID is positive."""
        if v <= 0:
            raise ValueError('Telegram ID must be positive')
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate quantity is reasonable."""
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 99:
            raise ValueError('Quantity cannot exceed 99')
        return v

    class Config:
        schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "product_id": 1,
                "quantity": 2
            }
        }


class CartItemUpdateRequest(BaseModel):
    """Cart item update request schema."""
    quantity: int = Field(..., gt=0, description="New item quantity")

    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate quantity is reasonable."""
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 99:
            raise ValueError('Quantity cannot exceed 99')
        return v

    class Config:
        schema_extra = {
            "example": {
                "quantity": 3
            }
        }


class CartItemResponse(BaseModel):
    """Cart item response schema."""
    id: int = Field(..., description="Cart item ID")
    cart_id: int = Field(..., description="Cart ID")
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., description="Item quantity")
    product: ProductResponse = Field(..., description="Product information")
    total_price: float = Field(..., description="Total price for this item")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "cart_id": 1,
                "product_id": 1,
                "quantity": 2,
                "product": {
                    "id": 1,
                    "name": "Брокколи замороженная",
                    "description": "Свежая замороженная брокколи",
                    "price": 150.0,
                    "formatted_price": "150₽",
                    "image_url": "https://example.com/broccoli.jpg",
                    "is_active": True,
                    "in_stock": True,
                    "weight": 500,
                    "formatted_weight": "500г",
                    "sort_order": 0,
                    "category_id": 1,
                    "category": {
                        "id": 1,
                        "name": "Замороженные овощи",
                        "description": "Свежие замороженные овощи",
                        "image_url": "https://example.com/vegetables.jpg",
                        "is_active": True,
                        "sort_order": 0,
                        "products_count": 15,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "total_price": 300.0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class CartResponse(BaseModel):
    """Cart response schema."""
    id: int = Field(..., description="Cart ID")
    user_id: int = Field(..., description="User ID")
    items: list[CartItemResponse] = Field(..., description="Cart items")
    total_amount: float = Field(..., description="Total cart amount")
    total_items: int = Field(..., description="Total number of items")
    expires_at: Optional[datetime] = Field(None, description="Cart expiration time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "items": [
                    {
                        "id": 1,
                        "cart_id": 1,
                        "product_id": 1,
                        "quantity": 2,
                        "product": {
                            "id": 1,
                            "name": "Брокколи замороженная",
                            "price": 150.0,
                            "formatted_price": "150₽"
                        },
                        "total_price": 300.0,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total_amount": 450.0,
                "total_items": 3,
                "expires_at": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class EmptyCartResponse(BaseModel):
    """Empty cart response schema."""
    items: list = Field(default_factory=list, description="Empty cart items")
    total_amount: float = Field(0.0, description="Total cart amount")
    total_items: int = Field(0, description="Total number of items")

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total_amount": 0.0,
                "total_items": 0
            }
        }