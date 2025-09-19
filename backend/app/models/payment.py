"""Payment models."""

from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class PaymentStatus(Enum):
    """Payment status enum."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(Enum):
    """Payment method enum."""
    TELEGRAM = "telegram"
    CARD = "card"
    CASH = "cash"


class Payment(BaseModel):
    """Payment model."""
    __tablename__ = "payments"

    # Order relationship
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)

    # Payment details
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    amount = Column(Float, nullable=False, comment="Payment amount in rubles")
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.TELEGRAM, nullable=False)

    # Telegram Payments specific fields
    telegram_payment_charge_id = Column(String(255), nullable=True, comment="Telegram payment charge ID")
    provider_payment_charge_id = Column(String(255), nullable=True, comment="Provider payment charge ID")

    # Transaction details
    transaction_id = Column(String(255), nullable=True, comment="External transaction ID")
    provider_data = Column(JSON, nullable=True, comment="Provider specific data")

    # Error handling
    error_message = Column(Text, nullable=True, comment="Error message if payment failed")

    # Metadata
    payment_metadata = Column(JSON, nullable=True, comment="Additional payment metadata")

    # Relationships
    order = relationship("Order", back_populates="payment")

    def __str__(self) -> str:
        return f"Payment(id={self.id}, order_id={self.order_id}, status={self.status.value}, amount={self.amount})"

    @property
    def formatted_amount(self) -> str:
        """Get formatted payment amount."""
        return f"{int(self.amount)}₽"

    @property
    def status_display(self) -> str:
        """Get human-readable payment status."""
        status_map = {
            PaymentStatus.PENDING: "Ожидает оплаты",
            PaymentStatus.SUCCESS: "Оплачено",
            PaymentStatus.FAILED: "Ошибка оплаты",
            PaymentStatus.REFUNDED: "Возвращено"
        }
        return status_map.get(self.status, self.status.value)

    @property
    def method_display(self) -> str:
        """Get human-readable payment method."""
        method_map = {
            PaymentMethod.TELEGRAM: "Telegram Payments",
            PaymentMethod.CARD: "Банковская карта",
            PaymentMethod.CASH: "Наличные"
        }
        return method_map.get(self.payment_method, self.payment_method.value)

    def is_completed(self) -> bool:
        """Check if payment is completed successfully."""
        return self.status == PaymentStatus.SUCCESS

    def is_failed(self) -> bool:
        """Check if payment failed."""
        return self.status == PaymentStatus.FAILED

    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status == PaymentStatus.PENDING

    def can_refund(self) -> bool:
        """Check if payment can be refunded."""
        return self.status == PaymentStatus.SUCCESS and self.telegram_payment_charge_id is not None