"""Enhanced order schemas with status management."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from .user import UserResponse
from .product import ProductResponse


class OrderStatus(str, Enum):
    """Enhanced order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class OrderPriority(str, Enum):
    """Order priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    VIP = "vip"


class StatusChangeReason(str, Enum):
    """Status change reason enumeration."""
    AUTOMATIC = "automatic"
    MANUAL_ADMIN = "manual_admin"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    CUSTOMER_REQUEST = "customer_request"
    KITCHEN_READY = "kitchen_ready"
    DELIVERY_COMPLETED = "delivery_completed"
    TIMEOUT = "timeout"
    ERROR = "error"
    REFUND_PROCESSED = "refund_processed"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"
    CANCELLED_BY_CUSTOMER = "cancelled_by_customer"


class OrderCreateRequest(BaseModel):
    """Order creation request schema."""
    telegram_id: int = Field(..., description="Telegram user ID")
    customer_name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    customer_phone: str = Field(..., min_length=10, max_length=20, description="Customer phone")
    delivery_address: Optional[str] = Field(None, max_length=500, description="Delivery address")
    notes: Optional[str] = Field(None, max_length=1000, description="Order notes")
    payment_method: str = Field("card", description="Payment method")

    @validator('telegram_id')
    def validate_telegram_id(cls, v):
        """Validate Telegram ID is positive."""
        if v <= 0:
            raise ValueError('Telegram ID must be positive')
        return v

    @validator('customer_phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if not v.startswith('+'):
            raise ValueError('Phone number must start with +')
        return v

    @validator('payment_method')
    def validate_payment_method(cls, v):
        """Validate payment method."""
        allowed_methods = ['card', 'cash', 'transfer']
        if v not in allowed_methods:
            raise ValueError(f'Payment method must be one of: {", ".join(allowed_methods)}')
        return v

    class Config:
        schema_extra = {
            "example": {
                "telegram_id": 123456789,
                "customer_name": "Иван Иванов",
                "customer_phone": "+7900123456",
                "delivery_address": "ул. Пушкина, д. 1, кв. 1",
                "notes": "Позвонить за 10 минут до доставки",
                "payment_method": "card"
            }
        }


class OrderStatusUpdateRequest(BaseModel):
    """Enhanced order status update request schema."""
    status: OrderStatus = Field(..., description="New order status")
    reason: Optional[StatusChangeReason] = Field(StatusChangeReason.MANUAL_ADMIN, description="Reason for status change")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "status": "confirmed",
                "reason": "manual_admin",
                "notes": "Подтверждено администратором"
            }
        }


class OrderPriorityUpdateRequest(BaseModel):
    """Order priority update request schema."""
    priority: OrderPriority = Field(..., description="New order priority")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for priority change")

    class Config:
        schema_extra = {
            "example": {
                "priority": "high",
                "reason": "VIP клиент"
            }
        }


class OrderCancelRequest(BaseModel):
    """Order cancellation request schema."""
    reason: Optional[str] = Field(None, max_length=500, description="Cancellation reason")
    refund_amount: Optional[float] = Field(None, gt=0, description="Refund amount")

    class Config:
        schema_extra = {
            "example": {
                "reason": "По запросу клиента",
                "refund_amount": 450.0
            }
        }


class BulkStatusUpdateRequest(BaseModel):
    """Bulk status update request schema."""
    order_ids: List[int] = Field(..., min_items=1, description="List of order IDs to update")
    status: OrderStatus = Field(..., description="New status for all orders")
    reason: Optional[StatusChangeReason] = Field(StatusChangeReason.MANUAL_ADMIN, description="Reason for status change")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "order_ids": [1, 2, 3],
                "status": "confirmed",
                "reason": "manual_admin",
                "notes": "Подтверждены групповой операцией"
            }
        }


class CourierAssignRequest(BaseModel):
    """Courier assignment request schema."""
    courier_name: str = Field(..., min_length=1, max_length=100, description="Courier name")

    class Config:
        schema_extra = {
            "example": {
                "courier_name": "Иван Петров"
            }
        }


class DeliveryScheduleRequest(BaseModel):
    """Delivery scheduling request schema."""
    scheduled_time: datetime = Field(..., description="Scheduled delivery time")

    @validator('scheduled_time')
    def validate_scheduled_time(cls, v):
        """Validate scheduled time is in the future."""
        if v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v

    class Config:
        schema_extra = {
            "example": {
                "scheduled_time": "2024-01-02T15:30:00Z"
            }
        }


class OrderItemResponse(BaseModel):
    """Order item response schema."""
    id: int = Field(..., description="Order item ID")
    order_id: int = Field(..., description="Order ID")
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., description="Item quantity")
    price: float = Field(..., description="Price at the time of order")
    formatted_price: str = Field(..., description="Formatted price")
    total_price: float = Field(..., description="Total price for this item")
    formatted_total: str = Field(..., description="Formatted total price")
    product: ProductResponse = Field(..., description="Product information")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "order_id": 1,
                "product_id": 1,
                "quantity": 2,
                "price": 150.0,
                "formatted_price": "150₽",
                "total_price": 300.0,
                "formatted_total": "300₽",
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
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            }
        }


class OrderStatusHistoryResponse(BaseModel):
    """Order status history response schema."""
    id: int = Field(..., description="History record ID")
    from_status: Optional[str] = Field(None, description="Previous status")
    to_status: str = Field(..., description="New status")
    reason: str = Field(..., description="Change reason")
    reason_display: str = Field(..., description="Human-readable reason")
    changed_at: datetime = Field(..., description="Change timestamp")
    changed_by_id: Optional[int] = Field(None, description="User who made the change")
    notes: Optional[str] = Field(None, description="Additional notes")
    system_message: Optional[str] = Field(None, description="System message")
    duration_from_previous: Optional[int] = Field(None, description="Duration from previous status in minutes")
    duration_display: Optional[str] = Field(None, description="Human-readable duration")

    class Config:
        from_attributes = True


class OrderTimelineEvent(BaseModel):
    """Order timeline event schema."""
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Event type")
    status: Optional[str] = Field(None, description="Status at this event")
    description: str = Field(..., description="Event description")
    user: Optional[str] = Field(None, description="User who triggered the event")
    duration: Optional[str] = Field(None, description="Duration since previous event")
    notes: Optional[str] = Field(None, description="Additional notes")
    reason: Optional[str] = Field(None, description="Reason for change")
    system_message: Optional[str] = Field(None, description="System message")

    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2024-01-01T10:00:00Z",
                "event_type": "status_change",
                "status": "confirmed",
                "description": "Статус изменен на \"Подтвержден\"",
                "user": "admin",
                "duration": "5 мин.",
                "notes": "Подтверждено администратором",
                "reason": "Изменено администратором"
            }
        }


class OrderResponse(BaseModel):
    """Enhanced order response schema."""
    id: int = Field(..., description="Order ID")
    user_id: int = Field(..., description="User ID")
    status: OrderStatus = Field(..., description="Order status")
    status_display: str = Field(..., description="Human-readable status")
    priority: OrderPriority = Field(..., description="Order priority")
    priority_display: str = Field(..., description="Human-readable priority")
    total_amount: float = Field(..., description="Total order amount")
    formatted_total: str = Field(..., description="Formatted total amount")
    customer_name: str = Field(..., description="Customer name")
    customer_phone: str = Field(..., description="Customer phone")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    delivery_type: str = Field(..., description="Delivery type")
    delivery_type_display: str = Field(..., description="Human-readable delivery type")
    notes: Optional[str] = Field(None, description="Order notes")
    payment_method: str = Field(..., description="Payment method")

    # Enhanced timing fields
    estimated_preparation_time: Optional[int] = Field(None, description="Estimated preparation time in minutes")
    estimated_delivery_time: Optional[datetime] = Field(None, description="Estimated delivery time")
    preparation_duration: Optional[int] = Field(None, description="Actual preparation duration in minutes")
    total_duration: Optional[int] = Field(None, description="Total order duration in minutes")

    # Status timestamps
    status_pending_at: Optional[datetime] = Field(None, description="Pending timestamp")
    status_confirmed_at: Optional[datetime] = Field(None, description="Confirmed timestamp")
    status_preparing_at: Optional[datetime] = Field(None, description="Preparing timestamp")
    status_ready_at: Optional[datetime] = Field(None, description="Ready timestamp")
    status_completed_at: Optional[datetime] = Field(None, description="Completed timestamp")
    status_cancelled_at: Optional[datetime] = Field(None, description="Cancelled timestamp")

    # Delivery details
    courier_assigned: Optional[str] = Field(None, description="Assigned courier")
    delivery_scheduled_at: Optional[datetime] = Field(None, description="Scheduled delivery time")
    delivery_completed_at: Optional[datetime] = Field(None, description="Actual delivery completion time")

    # Cancellation and refund
    cancellation_reason: Optional[str] = Field(None, description="Cancellation reason")
    cancelled_by_user_id: Optional[int] = Field(None, description="User who cancelled the order")
    refund_amount: Optional[float] = Field(None, description="Refund amount")
    refund_reason: Optional[str] = Field(None, description="Refund reason")

    # Computed properties
    is_active: bool = Field(..., description="Whether order is in active state")
    is_completed_state: bool = Field(..., description="Whether order is in final state")
    can_be_cancelled: bool = Field(..., description="Whether order can be cancelled")
    can_be_refunded: bool = Field(..., description="Whether order can be refunded")
    is_overdue: bool = Field(..., description="Whether order is overdue")

    # Relationships
    items: List[OrderItemResponse] = Field(..., description="Order items")
    user: UserResponse = Field(..., description="User information")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "status": "pending",
                "status_display": "Ожидает подтверждения",
                "total_amount": 450.0,
                "formatted_total": "450₽",
                "customer_name": "Иван Иванов",
                "customer_phone": "+7900123456",
                "delivery_address": "ул. Пушкина, д. 1, кв. 1",
                "notes": "Позвонить за 10 минут до доставки",
                "payment_method": "card",
                "items": [
                    {
                        "id": 1,
                        "order_id": 1,
                        "product_id": 1,
                        "quantity": 2,
                        "price": 150.0,
                        "formatted_price": "150₽",
                        "total_price": 300.0,
                        "formatted_total": "300₽",
                        "product": {
                            "id": 1,
                            "name": "Брокколи замороженная",
                            "price": 150.0,
                            "formatted_price": "150₽"
                        }
                    }
                ],
                "user": {
                    "id": 1,
                    "telegram_id": 123456789,
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_admin": False,
                    "is_active": True,
                    "full_name": "John Doe",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class OrderListResponse(BaseModel):
    """Paginated order list response schema."""
    items: List[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Current page number")
    pages: int = Field(..., description="Total number of pages")
    per_page: int = Field(..., description="Items per page")

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "status": "pending",
                        "status_display": "Ожидает подтверждения",
                        "total_amount": 450.0,
                        "formatted_total": "450₽",
                        "customer_name": "Иван Иванов",
                        "customer_phone": "+7900123456",
                        "delivery_address": "ул. Пушкина, д. 1, кв. 1",
                        "notes": "Позвонить за 10 минут до доставки",
                        "payment_method": "card",
                        "items": [],
                        "user": {
                            "id": 1,
                            "telegram_id": 123456789,
                            "first_name": "John",
                            "last_name": "Doe",
                            "full_name": "John Doe"
                        },
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "pages": 3,
                "per_page": 20
            }
        }


class BulkUpdateResponse(BaseModel):
    """Bulk update response schema."""
    successful: List[Dict[str, Any]] = Field(..., description="Successfully updated orders")
    failed: List[Dict[str, Any]] = Field(..., description="Failed updates")
    total_processed: int = Field(..., description="Total orders processed")
    success_count: int = Field(..., description="Number of successful updates")
    failure_count: int = Field(..., description="Number of failed updates")

    class Config:
        schema_extra = {
            "example": {
                "successful": [
                    {
                        "order_id": 1,
                        "old_status": "pending",
                        "new_status": "confirmed",
                        "history_id": 123
                    }
                ],
                "failed": [
                    {
                        "order_id": 2,
                        "error": "Invalid status transition"
                    }
                ],
                "total_processed": 2,
                "success_count": 1,
                "failure_count": 1
            }
        }


class OrderStatsResponse(BaseModel):
    """Order statistics response schema."""
    total: int = Field(..., description="Total orders")
    pending: int = Field(..., description="Pending orders")
    processing: int = Field(..., description="Processing orders")
    completed: int = Field(..., description="Completed orders")
    cancelled: int = Field(..., description="Cancelled orders")
    failed: int = Field(..., description="Failed orders")
    refunded: int = Field(..., description="Refunded orders")
    status_counts: Dict[str, int] = Field(..., description="Count by status")
    priority_counts: Dict[str, int] = Field(..., description="Count by priority")
    overdue_count: int = Field(..., description="Overdue orders count")
    today_orders: int = Field(..., description="Today's orders count")

    class Config:
        schema_extra = {
            "example": {
                "total": 150,
                "pending": 5,
                "processing": 12,
                "completed": 120,
                "cancelled": 8,
                "failed": 3,
                "refunded": 2,
                "status_counts": {
                    "pending": 5,
                    "confirmed": 4,
                    "preparing": 5,
                    "ready": 3,
                    "completed": 120,
                    "cancelled": 8,
                    "failed": 3,
                    "refunded": 2
                },
                "priority_counts": {
                    "low": 2,
                    "normal": 15,
                    "high": 8,
                    "vip": 3
                },
                "overdue_count": 2,
                "today_orders": 15
            }
        }


class DashboardResponse(BaseModel):
    """Dashboard response schema."""
    stats: OrderStatsResponse = Field(..., description="Order statistics")
    overdue_orders: List[Dict[str, Any]] = Field(..., description="Overdue orders")
    vip_orders: List[Dict[str, Any]] = Field(..., description="VIP orders")
    recent_orders: List[Dict[str, Any]] = Field(..., description="Recent orders")
    performance: Dict[str, Any] = Field(..., description="Performance metrics")

    class Config:
        schema_extra = {
            "example": {
                "stats": {
                    "total": 150,
                    "pending": 5,
                    "processing": 12,
                    "completed": 120
                },
                "overdue_orders": [
                    {
                        "id": 1,
                        "customer_name": "Иван Иванов",
                        "total_amount": 450.0,
                        "status": "preparing",
                        "created_at": "2024-01-01T10:00:00Z",
                        "priority": "normal"
                    }
                ],
                "vip_orders": [],
                "recent_orders": [],
                "performance": {
                    "avg_preparation_time_today": 32.5,
                    "overdue_count": 1,
                    "vip_count": 0
                }
            }
        }


class OrderTimelineResponse(BaseModel):
    """Order timeline response schema."""
    order_id: int = Field(..., description="Order ID")
    timeline: List[OrderTimelineEvent] = Field(..., description="Timeline events")

    class Config:
        schema_extra = {
            "example": {
                "order_id": 1,
                "timeline": [
                    {
                        "timestamp": "2024-01-01T10:00:00Z",
                        "event_type": "order_created",
                        "status": "pending",
                        "description": "Заказ создан",
                        "user": None,
                        "duration": None,
                        "notes": None
                    },
                    {
                        "timestamp": "2024-01-01T10:05:00Z",
                        "event_type": "status_change",
                        "status": "confirmed",
                        "description": "Статус изменен на \"Подтвержден\"",
                        "user": "admin",
                        "duration": "5 мин.",
                        "notes": "Подтверждено администратором",
                        "reason": "Изменено администратором"
                    }
                ]
            }
        }


class AutomationProcessingResponse(BaseModel):
    """Automation processing response schema."""
    processed_orders: int = Field(..., description="Number of orders processed")
    transitions_made: int = Field(..., description="Number of transitions made")
    errors: List[str] = Field(..., description="Processing errors")

    class Config:
        schema_extra = {
            "example": {
                "processed_orders": 25,
                "transitions_made": 3,
                "errors": []
            }
        }