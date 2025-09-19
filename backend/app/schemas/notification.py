"""Notification schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator


class NotificationType(str, Enum):
    """Notification type enumeration."""
    USER = "user"
    BROADCAST = "broadcast"


class ParseMode(str, Enum):
    """Telegram parse mode enumeration."""
    HTML = "HTML"
    MARKDOWN = "Markdown"


class NotificationRequest(BaseModel):
    """Notification request schema."""
    type: NotificationType = Field(..., description="Notification type")
    telegram_id: Optional[int] = Field(None, description="Telegram user ID (required for user type)")
    message: str = Field(..., min_length=1, max_length=4000, description="Notification message")
    parse_mode: Optional[ParseMode] = Field(None, description="Message parse mode")

    @validator('telegram_id')
    def validate_telegram_id(cls, v, values):
        """Validate telegram_id is provided for user notifications."""
        if values.get('type') == NotificationType.USER and not v:
            raise ValueError('telegram_id is required for user notifications')
        if v is not None and v <= 0:
            raise ValueError('telegram_id must be positive')
        return v

    @validator('message')
    def validate_message(cls, v):
        """Validate message content."""
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "type": "user",
                "telegram_id": 123456789,
                "message": "Ваш заказ готов к выдаче!",
                "parse_mode": "HTML"
            }
        }


class BroadcastNotificationRequest(BaseModel):
    """Broadcast notification request schema."""
    type: NotificationType = Field(NotificationType.BROADCAST, description="Notification type")
    message: str = Field(..., min_length=1, max_length=4000, description="Broadcast message")
    parse_mode: Optional[ParseMode] = Field(None, description="Message parse mode")
    target_users: Optional[str] = Field(None, description="Target user group (all, active, admin)")

    @validator('message')
    def validate_message(cls, v):
        """Validate message content."""
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

    @validator('target_users')
    def validate_target_users(cls, v):
        """Validate target users."""
        if v is not None:
            allowed_targets = ['all', 'active', 'admin']
            if v not in allowed_targets:
                raise ValueError(f'target_users must be one of: {", ".join(allowed_targets)}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "type": "broadcast",
                "message": "Новинки в каталоге! Скидка 10% на все замороженные овощи!",
                "parse_mode": "HTML",
                "target_users": "active"
            }
        }


class NotificationResponse(BaseModel):
    """Notification response schema."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    sent_count: Optional[int] = Field(None, description="Number of notifications sent (for broadcast)")
    failed_count: Optional[int] = Field(None, description="Number of failed sends (for broadcast)")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Notification sent successfully",
                "sent_count": 150,
                "failed_count": 0
            }
        }


class NotificationStatus(BaseModel):
    """Notification delivery status."""
    notification_id: str = Field(..., description="Notification ID")
    status: str = Field(..., description="Delivery status")
    telegram_id: Optional[int] = Field(None, description="Target Telegram user ID")
    message: str = Field(..., description="Notification message")
    sent_at: Optional[str] = Field(None, description="Send timestamp")
    delivered_at: Optional[str] = Field(None, description="Delivery timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        schema_extra = {
            "example": {
                "notification_id": "notif_123456",
                "status": "delivered",
                "telegram_id": 123456789,
                "message": "Ваш заказ готов к выдаче!",
                "sent_at": "2024-01-01T12:00:00Z",
                "delivered_at": "2024-01-01T12:00:01Z",
                "error_message": None
            }
        }