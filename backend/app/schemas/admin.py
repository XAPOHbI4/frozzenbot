"""Admin and analytics schemas."""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .product import ProductResponse
from .category import CategoryResponse
from .order import OrderResponse


class DashboardStats(BaseModel):
    """Dashboard statistics schema."""
    total_orders: int = Field(..., description="Total number of orders")
    total_revenue: float = Field(..., description="Total revenue amount")
    active_users: int = Field(..., description="Number of active users")
    pending_orders: int = Field(..., description="Number of pending orders")
    today_orders: int = Field(..., description="Today's orders count")
    today_revenue: float = Field(..., description="Today's revenue")
    popular_products: List['PopularProduct'] = Field(..., description="Top selling products")
    recent_orders: List[OrderResponse] = Field(..., description="Recent orders")

    class Config:
        schema_extra = {
            "example": {
                "total_orders": 1250,
                "total_revenue": 125000.0,
                "active_users": 450,
                "pending_orders": 5,
                "today_orders": 15,
                "today_revenue": 1500.0,
                "popular_products": [
                    {
                        "product": {
                            "id": 1,
                            "name": "Брокколи замороженная",
                            "price": 150.0,
                            "formatted_price": "150₽"
                        },
                        "orders_count": 25,
                        "total_revenue": 3750.0
                    }
                ],
                "recent_orders": []
            }
        }


class PopularProduct(BaseModel):
    """Popular product statistics."""
    product: ProductResponse = Field(..., description="Product information")
    orders_count: int = Field(..., description="Number of orders")
    total_revenue: float = Field(..., description="Total revenue from this product")

    class Config:
        from_attributes = True


class OrderAnalytics(BaseModel):
    """Order analytics schema."""
    period: str = Field(..., description="Analytics period")
    total_orders: int = Field(..., description="Total orders in period")
    total_revenue: float = Field(..., description="Total revenue in period")
    average_order_value: float = Field(..., description="Average order value")
    orders_by_status: Dict[str, int] = Field(..., description="Orders count by status")
    revenue_chart: List['ChartDataPoint'] = Field(..., description="Revenue chart data")
    orders_chart: List['OrderChartDataPoint'] = Field(..., description="Orders chart data")

    class Config:
        schema_extra = {
            "example": {
                "period": "month",
                "total_orders": 150,
                "total_revenue": 15000.0,
                "average_order_value": 100.0,
                "orders_by_status": {
                    "pending": 5,
                    "confirmed": 10,
                    "completed": 135
                },
                "revenue_chart": [
                    {
                        "date": "2024-01-01",
                        "revenue": 1500.0
                    }
                ],
                "orders_chart": [
                    {
                        "date": "2024-01-01",
                        "count": 15
                    }
                ]
            }
        }


class ChartDataPoint(BaseModel):
    """Chart data point for revenue."""
    date: date = Field(..., description="Date")
    revenue: float = Field(..., description="Revenue amount")


class OrderChartDataPoint(BaseModel):
    """Chart data point for orders."""
    date: date = Field(..., description="Date")
    count: int = Field(..., description="Orders count")


class ProductAnalytics(BaseModel):
    """Product analytics schema."""
    period: str = Field(..., description="Analytics period")
    top_products: List['TopProduct'] = Field(..., description="Top selling products")
    categories_performance: List['CategoryPerformance'] = Field(..., description="Category performance")
    inventory_status: 'InventoryStatus' = Field(..., description="Inventory status")

    class Config:
        schema_extra = {
            "example": {
                "period": "month",
                "top_products": [
                    {
                        "product": {
                            "id": 1,
                            "name": "Брокколи замороженная",
                            "price": 150.0
                        },
                        "orders_count": 25,
                        "revenue": 3750.0
                    }
                ],
                "categories_performance": [
                    {
                        "category": {
                            "id": 1,
                            "name": "Замороженные овощи"
                        },
                        "orders_count": 50,
                        "revenue": 7500.0
                    }
                ],
                "inventory_status": {
                    "total_products": 100,
                    "active_products": 95,
                    "out_of_stock": 5
                }
            }
        }


class TopProduct(BaseModel):
    """Top selling product."""
    product: ProductResponse = Field(..., description="Product information")
    orders_count: int = Field(..., description="Number of orders")
    revenue: float = Field(..., description="Revenue from this product")

    class Config:
        from_attributes = True


class CategoryPerformance(BaseModel):
    """Category performance statistics."""
    category: CategoryResponse = Field(..., description="Category information")
    orders_count: int = Field(..., description="Number of orders")
    revenue: float = Field(..., description="Revenue from this category")

    class Config:
        from_attributes = True


class InventoryStatus(BaseModel):
    """Inventory status statistics."""
    total_products: int = Field(..., description="Total number of products")
    active_products: int = Field(..., description="Number of active products")
    out_of_stock: int = Field(..., description="Number of out-of-stock products")

    class Config:
        schema_extra = {
            "example": {
                "total_products": 100,
                "active_products": 95,
                "out_of_stock": 5
            }
        }


# Update forward references
DashboardStats.model_rebuild()
OrderAnalytics.model_rebuild()
ProductAnalytics.model_rebuild()