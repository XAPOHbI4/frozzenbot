"""Order status history model for audit trail."""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel
from .order import OrderStatus


class StatusChangeReason(Enum):
    """Reasons for status changes."""
    AUTOMATIC = "automatic"          # Automated workflow transition
    MANUAL_ADMIN = "manual_admin"    # Changed by admin/manager
    PAYMENT_SUCCESS = "payment_success"  # Payment completed
    PAYMENT_FAILED = "payment_failed"    # Payment failed
    CUSTOMER_REQUEST = "customer_request"  # Customer requested change
    KITCHEN_READY = "kitchen_ready"      # Kitchen marked as ready
    DELIVERY_COMPLETED = "delivery_completed"  # Delivery completed
    TIMEOUT = "timeout"                  # Automatic timeout
    ERROR = "error"                      # System error
    REFUND_PROCESSED = "refund_processed"  # Refund was processed
    CANCELLED_BY_ADMIN = "cancelled_by_admin"  # Admin cancelled
    CANCELLED_BY_CUSTOMER = "cancelled_by_customer"  # Customer cancelled


class OrderStatusHistory(BaseModel):
    """Order status history for audit trail."""
    __tablename__ = "order_status_history"

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    # Status change details
    from_status = Column(String(20), nullable=True)  # Previous status (null for first record)
    to_status = Column(String(20), nullable=False)   # New status

    # Change metadata
    reason = Column(String(50), nullable=False, default=StatusChangeReason.MANUAL_ADMIN.value)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Additional context
    notes = Column(Text, nullable=True)
    system_message = Column(Text, nullable=True)

    # Metadata for automation and workflow
    workflow_data = Column(JSON, default=dict, nullable=False)
    duration_from_previous = Column(Integer, nullable=True, comment="Duration from previous status in minutes")

    # Integration context
    triggered_by_event = Column(String(100), nullable=True)  # e.g., "payment_webhook", "kitchen_notification"
    external_reference_id = Column(String(100), nullable=True)  # External system reference

    # IP and user agent for manual changes
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])

    def __str__(self) -> str:
        return f"OrderStatusHistory(order_id={self.order_id}, {self.from_status} -> {self.to_status})"

    @property
    def from_status_display(self) -> Optional[str]:
        """Get human-readable from status."""
        if not self.from_status:
            return None

        try:
            status = OrderStatus(self.from_status)
            return status.name.replace('_', ' ').title()
        except ValueError:
            return self.from_status

    @property
    def to_status_display(self) -> str:
        """Get human-readable to status."""
        try:
            status = OrderStatus(self.to_status)
            return status.name.replace('_', ' ').title()
        except ValueError:
            return self.to_status

    @property
    def reason_display(self) -> str:
        """Get human-readable reason."""
        reason_map = {
            StatusChangeReason.AUTOMATIC: "Автоматический переход",
            StatusChangeReason.MANUAL_ADMIN: "Изменено администратором",
            StatusChangeReason.PAYMENT_SUCCESS: "Оплата подтверждена",
            StatusChangeReason.PAYMENT_FAILED: "Ошибка оплаты",
            StatusChangeReason.CUSTOMER_REQUEST: "По запросу клиента",
            StatusChangeReason.KITCHEN_READY: "Готово на кухне",
            StatusChangeReason.DELIVERY_COMPLETED: "Доставка завершена",
            StatusChangeReason.TIMEOUT: "Превышено время ожидания",
            StatusChangeReason.ERROR: "Системная ошибка",
            StatusChangeReason.REFUND_PROCESSED: "Возврат обработан",
            StatusChangeReason.CANCELLED_BY_ADMIN: "Отменено администратором",
            StatusChangeReason.CANCELLED_BY_CUSTOMER: "Отменено клиентом"
        }

        try:
            reason_enum = StatusChangeReason(self.reason)
            return reason_map.get(reason_enum, self.reason)
        except ValueError:
            return self.reason

    @property
    def duration_display(self) -> Optional[str]:
        """Get human-readable duration from previous status."""
        if not self.duration_from_previous:
            return None

        minutes = self.duration_from_previous
        if minutes < 60:
            return f"{minutes} мин."
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} ч."
            return f"{hours} ч. {remaining_minutes} мин."
        else:  # More than 24 hours
            days = minutes // 1440
            remaining_hours = (minutes % 1440) // 60
            if remaining_hours == 0:
                return f"{days} д."
            return f"{days} д. {remaining_hours} ч."

    def get_workflow_data(self, key: str, default=None):
        """Get workflow data value."""
        return self.workflow_data.get(key, default)

    def set_workflow_data(self, key: str, value):
        """Set workflow data value."""
        if self.workflow_data is None:
            self.workflow_data = {}
        self.workflow_data[key] = value

    @classmethod
    def create_status_change(
        cls,
        order_id: int,
        from_status: Optional[str],
        to_status: str,
        reason: StatusChangeReason = StatusChangeReason.MANUAL_ADMIN,
        changed_by_user_id: Optional[int] = None,
        notes: Optional[str] = None,
        system_message: Optional[str] = None,
        workflow_data: Optional[Dict[str, Any]] = None,
        triggered_by_event: Optional[str] = None,
        external_reference_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> 'OrderStatusHistory':
        """
        Create a new status history record.

        Args:
            order_id: Order ID
            from_status: Previous status (None for first record)
            to_status: New status
            reason: Reason for change
            changed_by_user_id: User who made the change
            notes: Additional notes
            system_message: System-generated message
            workflow_data: Workflow metadata
            triggered_by_event: Event that triggered this change
            external_reference_id: External system reference
            ip_address: IP address of the user (for manual changes)
            user_agent: User agent (for manual changes)

        Returns:
            OrderStatusHistory instance
        """
        return cls(
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason.value if isinstance(reason, StatusChangeReason) else reason,
            changed_by_user_id=changed_by_user_id,
            notes=notes,
            system_message=system_message,
            workflow_data=workflow_data or {},
            triggered_by_event=triggered_by_event,
            external_reference_id=external_reference_id,
            ip_address=ip_address,
            user_agent=user_agent
        )