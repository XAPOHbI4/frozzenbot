"""Payment schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CARD = "card"
    CASH = "cash"
    TRANSFER = "transfer"
    CRYPTO = "crypto"


class PaymentWebhookRequest(BaseModel):
    """Payment webhook request schema."""
    order_id: int = Field(..., gt=0, description="Order ID")
    status: PaymentStatus = Field(..., description="Payment status")
    amount: float = Field(..., gt=0, description="Payment amount")
    transaction_id: Optional[str] = Field(None, max_length=255, description="Transaction ID")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('amount')
    def validate_amount(cls, v):
        """Validate payment amount."""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 1000000:
            raise ValueError('Amount seems too high')
        return round(v, 2)

    class Config:
        schema_extra = {
            "example": {
                "order_id": 1,
                "status": "success",
                "amount": 450.0,
                "transaction_id": "txn_123456789",
                "payment_method": "card",
                "metadata": {
                    "provider": "stripe",
                    "card_last4": "1234",
                    "card_brand": "visa"
                }
            }
        }


class PaymentCreateRequest(BaseModel):
    """Payment creation request schema."""
    order_id: int = Field(..., gt=0, description="Order ID")
    amount: float = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    return_url: Optional[str] = Field(None, description="Return URL after payment")
    cancel_url: Optional[str] = Field(None, description="Cancel URL")

    @validator('amount')
    def validate_amount(cls, v):
        """Validate payment amount."""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 1000000:
            raise ValueError('Amount seems too high')
        return round(v, 2)

    @validator('return_url', 'cancel_url')
    def validate_urls(cls, v):
        """Validate URLs format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    class Config:
        schema_extra = {
            "example": {
                "order_id": 1,
                "amount": 450.0,
                "payment_method": "card",
                "return_url": "https://example.com/payment/success",
                "cancel_url": "https://example.com/payment/cancel"
            }
        }


class PaymentResponse(BaseModel):
    """Payment response schema."""
    id: str = Field(..., description="Payment ID")
    order_id: int = Field(..., description="Order ID")
    status: PaymentStatus = Field(..., description="Payment status")
    amount: float = Field(..., description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    payment_url: Optional[str] = Field(None, description="Payment URL for redirect")
    expires_at: Optional[datetime] = Field(None, description="Payment expiration time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "pay_123456789",
                "order_id": 1,
                "status": "pending",
                "amount": 450.0,
                "payment_method": "card",
                "transaction_id": None,
                "payment_url": "https://payment.provider.com/pay/123456789",
                "expires_at": "2024-01-01T13:00:00Z",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class PaymentStatusResponse(BaseModel):
    """Payment status response schema."""
    order_id: int = Field(..., description="Order ID")
    status: PaymentStatus = Field(..., description="Payment status")
    amount: float = Field(..., description="Payment amount")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    payment_method: str = Field(..., description="Payment method display name")
    created_at: str = Field(..., description="Payment creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last status update timestamp (ISO format)")
    paid_at: Optional[str] = Field(None, description="Payment completion timestamp (ISO format)")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "order_id": 1,
                "status": "success",
                "amount": 450.0,
                "transaction_id": "txn_123456789",
                "payment_method": "card",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:05:00Z",
                "paid_at": "2024-01-01T12:05:00Z"
            }
        }


class RefundRequest(BaseModel):
    """Refund request schema."""
    payment_id: str = Field(..., description="Payment ID to refund")
    amount: Optional[float] = Field(None, gt=0, description="Refund amount (partial refund)")
    reason: Optional[str] = Field(None, max_length=500, description="Refund reason")

    @validator('amount')
    def validate_amount(cls, v):
        """Validate refund amount."""
        if v is not None:
            if v <= 0:
                raise ValueError('Refund amount must be greater than 0')
            return round(v, 2)
        return v

    class Config:
        schema_extra = {
            "example": {
                "payment_id": "pay_123456789",
                "amount": 450.0,
                "reason": "Customer cancellation"
            }
        }


class RefundResponse(BaseModel):
    """Refund response schema."""
    id: str = Field(..., description="Refund ID")
    payment_id: str = Field(..., description="Original payment ID")
    order_id: int = Field(..., description="Order ID")
    status: str = Field(..., description="Refund status")
    amount: float = Field(..., description="Refund amount")
    reason: Optional[str] = Field(None, description="Refund reason")
    refund_id: Optional[str] = Field(None, description="Provider refund ID")
    created_at: datetime = Field(..., description="Refund creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Refund processing timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "ref_123456789",
                "payment_id": "pay_123456789",
                "order_id": 1,
                "status": "processed",
                "amount": 450.0,
                "reason": "Customer cancellation",
                "refund_id": "re_abcdef123",
                "created_at": "2024-01-01T14:00:00Z",
                "processed_at": "2024-01-01T14:05:00Z"
            }
        }