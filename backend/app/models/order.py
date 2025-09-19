"""Order models with enhanced status management."""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Enum as SQLEnum, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class OrderStatus(Enum):
    """Enhanced order status enum with complete workflow."""
    PENDING = "pending"          # Ожидает подтверждения
    CONFIRMED = "confirmed"      # Подтвержден
    PREPARING = "preparing"      # Готовится
    READY = "ready"             # Готов к выдаче/доставке
    COMPLETED = "completed"      # Выполнен
    CANCELLED = "cancelled"      # Отменен
    REFUNDED = "refunded"       # Возврат средств
    FAILED = "failed"           # Неудачный


class OrderPriority(Enum):
    """Order priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    VIP = "vip"


class Order(BaseModel):
    """Enhanced order model with status management."""
    __tablename__ = "orders"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_amount = Column(Float, nullable=False)

    # Customer contact info
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    delivery_address = Column(Text, nullable=True)

    # Order details
    notes = Column(Text, nullable=True)
    payment_method = Column(String(50), default="card", nullable=False)

    # Enhanced fields for status management
    priority = Column(SQLEnum(OrderPriority), default=OrderPriority.NORMAL, nullable=False)
    estimated_preparation_time = Column(Integer, nullable=True, comment="Estimated preparation time in minutes")
    estimated_delivery_time = Column(DateTime, nullable=True)
    actual_preparation_start = Column(DateTime, nullable=True)
    actual_preparation_end = Column(DateTime, nullable=True)
    delivery_scheduled_at = Column(DateTime, nullable=True)
    delivery_completed_at = Column(DateTime, nullable=True)

    # Status timestamps
    status_pending_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_confirmed_at = Column(DateTime, nullable=True)
    status_preparing_at = Column(DateTime, nullable=True)
    status_ready_at = Column(DateTime, nullable=True)
    status_completed_at = Column(DateTime, nullable=True)
    status_cancelled_at = Column(DateTime, nullable=True)

    # Kitchen integration
    kitchen_notes = Column(Text, nullable=True)
    requires_special_handling = Column(Boolean, default=False)

    # Delivery details
    delivery_type = Column(String(20), default="delivery", nullable=False)  # delivery or pickup
    delivery_instructions = Column(Text, nullable=True)
    courier_assigned = Column(String(100), nullable=True)

    # Cancellation and refund
    cancellation_reason = Column(String(255), nullable=True)
    cancelled_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    refund_amount = Column(Float, nullable=True)
    refund_reason = Column(String(255), nullable=True)

    # Business metrics
    preparation_duration = Column(Integer, nullable=True, comment="Actual preparation time in minutes")
    total_duration = Column(Integer, nullable=True, comment="Total order completion time in minutes")

    # Metadata for automation
    automation_flags = Column(JSON, default=dict, nullable=False)
    workflow_metadata = Column(JSON, default=dict, nullable=False)

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_user_id])

    def __str__(self) -> str:
        return f"Order(id={self.id}, status={self.status.value}, total={self.total_amount})"

    @property
    def formatted_total(self) -> str:
        """Get formatted total amount."""
        return f"{int(self.total_amount)}₽"

    @property
    def status_display(self) -> str:
        """Get human-readable status."""
        status_map = {
            OrderStatus.PENDING: "Ожидает подтверждения",
            OrderStatus.CONFIRMED: "Подтвержден",
            OrderStatus.PREPARING: "Готовится",
            OrderStatus.READY: "Готов к выдаче",
            OrderStatus.COMPLETED: "Выполнен",
            OrderStatus.CANCELLED: "Отменен",
            OrderStatus.REFUNDED: "Возврат средств",
            OrderStatus.FAILED: "Ошибка обработки"
        }
        return status_map.get(self.status, self.status.value)

    @property
    def priority_display(self) -> str:
        """Get human-readable priority."""
        priority_map = {
            OrderPriority.LOW: "Низкий",
            OrderPriority.NORMAL: "Обычный",
            OrderPriority.HIGH: "Высокий",
            OrderPriority.VIP: "VIP"
        }
        return priority_map.get(self.priority, self.priority.value)

    @property
    def is_active(self) -> bool:
        """Check if order is active (not completed, cancelled, failed, or refunded)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]

    @property
    def is_completed_state(self) -> bool:
        """Check if order is in a final state."""
        return self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.FAILED, OrderStatus.REFUNDED]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING]

    @property
    def can_be_refunded(self) -> bool:
        """Check if order can be refunded."""
        return self.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]

    @property
    def delivery_type_display(self) -> str:
        """Get human-readable delivery type."""
        return "Доставка" if self.delivery_type == "delivery" else "Самовывоз"

    def get_status_timestamp(self, status: OrderStatus) -> Optional[datetime]:
        """Get timestamp for specific status."""
        timestamp_map = {
            OrderStatus.PENDING: self.status_pending_at,
            OrderStatus.CONFIRMED: self.status_confirmed_at,
            OrderStatus.PREPARING: self.status_preparing_at,
            OrderStatus.READY: self.status_ready_at,
            OrderStatus.COMPLETED: self.status_completed_at,
            OrderStatus.CANCELLED: self.status_cancelled_at,
        }
        return timestamp_map.get(status)

    def get_estimated_completion_time(self) -> Optional[datetime]:
        """Calculate estimated completion time based on preparation time."""
        if not self.estimated_preparation_time:
            return None

        base_time = self.status_confirmed_at or self.created_at
        return base_time + timedelta(minutes=self.estimated_preparation_time)

    def calculate_preparation_duration(self) -> Optional[int]:
        """Calculate actual preparation duration in minutes."""
        if not (self.actual_preparation_start and self.actual_preparation_end):
            return None

        delta = self.actual_preparation_end - self.actual_preparation_start
        return int(delta.total_seconds() / 60)

    def calculate_total_duration(self) -> Optional[int]:
        """Calculate total order duration from creation to completion in minutes."""
        if not self.status_completed_at:
            return None

        delta = self.status_completed_at - self.created_at
        return int(delta.total_seconds() / 60)

    def is_overdue(self) -> bool:
        """Check if order is overdue based on estimated completion time."""
        estimated = self.get_estimated_completion_time()
        if not estimated:
            return False

        return datetime.utcnow() > estimated and not self.is_completed_state

    def get_workflow_metadata_value(self, key: str, default=None):
        """Get value from workflow metadata."""
        return self.workflow_metadata.get(key, default)

    def set_workflow_metadata_value(self, key: str, value):
        """Set value in workflow metadata."""
        if self.workflow_metadata is None:
            self.workflow_metadata = {}
        self.workflow_metadata[key] = value

    def get_automation_flag(self, flag: str, default: bool = False) -> bool:
        """Get automation flag value."""
        return self.automation_flags.get(flag, default)

    def set_automation_flag(self, flag: str, value: bool):
        """Set automation flag value."""
        if self.automation_flags is None:
            self.automation_flags = {}
        self.automation_flags[flag] = value


class OrderItem(BaseModel):
    """Order item."""
    __tablename__ = "order_items"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False, comment="Price at the time of order")

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __str__(self) -> str:
        return f"OrderItem(product_id={self.product_id}, quantity={self.quantity}, price={self.price})"

    @property
    def total_price(self) -> float:
        """Calculate total price for this item."""
        return self.price * self.quantity

    @property
    def formatted_price(self) -> str:
        """Get formatted price."""
        return f"{int(self.price)}₽"

    @property
    def formatted_total(self) -> str:
        """Get formatted total price."""
        return f"{int(self.total_price)}₽"