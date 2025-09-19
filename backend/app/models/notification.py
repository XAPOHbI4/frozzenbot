"""Notification models for tracking notification history."""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, Integer, BigInteger, ForeignKey, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class NotificationType(Enum):
    """Notification type enum."""
    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_PREPARING = "order_preparing"
    ORDER_READY = "order_ready"
    ORDER_COMPLETED = "order_completed"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    FEEDBACK_REQUEST = "feedback_request"
    ADMIN_NEW_ORDER = "admin_new_order"
    ADMIN_PAYMENT_FAILED = "admin_payment_failed"
    ADMIN_DAILY_STATS = "admin_daily_stats"


class NotificationStatus(Enum):
    """Notification status enum."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class NotificationTarget(Enum):
    """Notification target enum."""
    USER = "user"
    ADMIN = "admin"


class Notification(BaseModel):
    """Notification model for tracking notification history."""
    __tablename__ = "notifications"

    # Target information
    target_type = Column(SQLEnum(NotificationTarget), nullable=False)
    target_telegram_id = Column(BigInteger, nullable=False, index=True)

    # Notification details
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)

    # Content
    title = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)

    # Related entities
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Scheduling
    scheduled_at = Column('scheduled_at', nullable=True)
    sent_at = Column('sent_at', nullable=True)

    # Metadata
    notification_metadata = Column(JSON, nullable=True, comment="Additional notification metadata")
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Inline keyboard data for feedback
    inline_keyboard = Column(JSON, nullable=True, comment="Telegram inline keyboard markup")

    # Relationships
    order = relationship("Order", backref="notifications")
    user = relationship("User", backref="sent_notifications")

    def __str__(self) -> str:
        return f"Notification(id={self.id}, type={self.notification_type.value}, status={self.status.value})"

    @property
    def is_sent(self) -> bool:
        """Check if notification was sent."""
        return self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]

    @property
    def is_failed(self) -> bool:
        """Check if notification failed."""
        return self.status == NotificationStatus.FAILED

    @property
    def is_scheduled(self) -> bool:
        """Check if notification is scheduled."""
        return self.status == NotificationStatus.SCHEDULED and self.scheduled_at is not None

    @property
    def should_retry(self) -> bool:
        """Check if notification should be retried."""
        return self.status == NotificationStatus.FAILED and self.retry_count < 3


class NotificationTemplate(BaseModel):
    """Notification templates for different types."""
    __tablename__ = "notification_templates"

    notification_type = Column(SQLEnum(NotificationType), nullable=False, unique=True)
    target_type = Column(SQLEnum(NotificationTarget), nullable=False)

    # Template content
    title_template = Column(String(255), nullable=True)
    message_template = Column(Text, nullable=False)

    # Template configuration
    enabled = Column(Boolean, default=True, nullable=False)
    delay_minutes = Column(Integer, default=0, nullable=False, comment="Delay before sending in minutes")

    # Metadata
    description = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True, comment="Available template variables")

    def __str__(self) -> str:
        return f"NotificationTemplate(type={self.notification_type.value}, target={self.target_type.value})"


class FeedbackRating(BaseModel):
    """Customer feedback and ratings."""
    __tablename__ = "feedback_ratings"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Rating (1-5 stars)
    rating = Column(Integer, nullable=False)

    # Optional feedback text
    feedback_text = Column(Text, nullable=True)

    # Notification that requested this feedback
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)

    # Relationships
    order = relationship("Order", backref="feedback")
    user = relationship("User", backref="feedback_given")
    notification = relationship("Notification", backref="feedback_responses")

    def __str__(self) -> str:
        return f"FeedbackRating(order_id={self.order_id}, rating={self.rating})"

    @property
    def rating_emoji(self) -> str:
        """Get emoji representation of rating."""
        emoji_map = {
            1: "⭐",
            2: "⭐⭐",
            3: "⭐⭐⭐",
            4: "⭐⭐⭐⭐",
            5: "⭐⭐⭐⭐⭐"
        }
        return emoji_map.get(self.rating, "❓")

    @property
    def rating_text(self) -> str:
        """Get text representation of rating."""
        rating_map = {
            1: "Очень плохо",
            2: "Плохо",
            3: "Нормально",
            4: "Хорошо",
            5: "Отлично"
        }
        return rating_map.get(self.rating, "Неизвестно")