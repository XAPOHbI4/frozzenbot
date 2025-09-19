"""Admin API endpoints."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_async_session
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.models.category import Category
from app.services.order import OrderService
from app.schemas.order import OrderResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.middleware.auth import require_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Admin authentication is now handled by require_admin_user dependency


@router.get("/orders", response_model=Dict[str, Any])
async def get_admin_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Number of orders to return"),
    offset: int = Query(0, description="Offset for pagination"),
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get all orders for admin with detailed information."""
    query = select(Order, User).join(User, Order.user_id == User.id).where(Order.is_deleted == False)

    if status:
        try:
            order_status = OrderStatus(status)
            query = query.where(Order.status == order_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый статус: {status}"
            )

    query = query.order_by(desc(Order.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    orders_data = result.all()

    orders = []
    for order, user in orders_data:
        # Get order items
        items_result = await db.execute(
            select(OrderItem, Product)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order.id)
        )
        items_data = items_result.all()

        items = []
        for order_item, product in items_data:
            items.append({
                "id": order_item.id,
                "product_id": product.id,
                "product_name": product.name,
                "quantity": order_item.quantity,
                "price": order_item.price,
                "total_price": order_item.total_price,
                "formatted_total": order_item.formatted_total
            })

        orders.append({
            "id": order.id,
            "status": order.status.value,
            "status_display": order.status_display,
            "total_amount": order.total_amount,
            "formatted_total": order.formatted_total,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "notes": order.notes,
            "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "items": items,
            "items_count": len(items)
        })

    return {
        "success": True,
        "orders": orders,
        "count": len(orders),
        "has_more": len(orders) == limit
    }


@router.get("/orders/{order_id}", response_model=Dict[str, Any])
async def get_admin_order_detail(
    order_id: int,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get detailed order information for admin."""
    result = await db.execute(
        select(Order, User)
        .join(User, Order.user_id == User.id)
        .where(Order.id == order_id, Order.is_deleted == False)
    )
    order_data = result.first()

    if not order_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )

    order, user = order_data

    # Get order items with product details
    items_result = await db.execute(
        select(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .where(OrderItem.order_id == order.id)
    )
    items_data = items_result.all()

    items = []
    for order_item, product in items_data:
        items.append({
            "id": order_item.id,
            "product_id": product.id,
            "product_name": product.name,
            "product_description": product.description,
            "quantity": order_item.quantity,
            "price": order_item.price,
            "current_product_price": product.price,  # Compare with order price
            "total_price": order_item.total_price,
            "formatted_price": order_item.formatted_price,
            "formatted_total": order_item.formatted_total,
            "price_changed": abs(order_item.price - product.price) > 0.01
        })

    return {
        "success": True,
        "order": {
            "id": order.id,
            "status": order.status.value,
            "status_display": order.status_display,
            "total_amount": order.total_amount,
            "formatted_total": order.formatted_total,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "notes": order.notes,
            "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_admin
            },
            "items": items,
            "items_count": len(items)
        }
    }


@router.get("/products", response_model=Dict[str, Any])
async def get_admin_products(
    include_inactive: bool = Query(False, description="Include inactive products"),
    admin_user: User = Depends(require_admin_user),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get all products for admin management."""
    query = select(Product, Category).outerjoin(Category, Product.category_id == Category.id)

    if not include_inactive:
        query = query.where(Product.is_active == True)

    if category_id:
        query = query.where(Product.category_id == category_id)

    query = query.where(Product.is_deleted == False).order_by(Product.name)

    result = await db.execute(query)
    products_data = result.all()

    products = []
    for product, category in products_data:
        products.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "formatted_price": product.formatted_price,
            "weight": product.weight,
            "is_active": product.is_active,
            "category": {
                "id": category.id if category else None,
                "name": category.name if category else None
            },
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat()
        })

    return {
        "success": True,
        "products": products,
        "count": len(products)
    }


@router.post("/products", response_model=Dict[str, Any])
async def create_admin_product(
    product_data: ProductCreate,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Create new product."""
    try:
        # Verify category exists if provided
        if product_data.category_id:
            category_result = await db.execute(
                select(Category).where(Category.id == product_data.category_id)
            )
            category = category_result.scalar_one_or_none()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Категория не найдена"
                )

        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            weight=product_data.weight,
            category_id=product_data.category_id,
            is_active=product_data.is_active
        )

        db.add(product)
        await db.commit()
        await db.refresh(product)

        return {
            "success": True,
            "message": "Товар успешно создан",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "formatted_price": product.formatted_price,
                "weight": product.weight,
                "is_active": product.is_active,
                "category_id": product.category_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания товара: {str(e)}"
        )


@router.put("/products/{product_id}", response_model=Dict[str, Any])
async def update_admin_product(
    product_id: int,
    admin_user: User = Depends(require_admin_user),
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Update product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_deleted == False)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    try:
        # Update fields
        if product_data.name is not None:
            product.name = product_data.name
        if product_data.description is not None:
            product.description = product_data.description
        if product_data.price is not None:
            product.price = product_data.price
        if product_data.weight is not None:
            product.weight = product_data.weight
        if product_data.category_id is not None:
            if product_data.category_id:
                # Verify category exists
                category_result = await db.execute(
                    select(Category).where(Category.id == product_data.category_id)
                )
                category = category_result.scalar_one_or_none()
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Категория не найдена"
                    )
            product.category_id = product_data.category_id
        if product_data.is_active is not None:
            product.is_active = product_data.is_active

        await db.commit()
        await db.refresh(product)

        return {
            "success": True,
            "message": "Товар успешно обновлен",
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "formatted_price": product.formatted_price,
                "weight": product.weight,
                "is_active": product.is_active,
                "category_id": product.category_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления товара: {str(e)}"
        )


@router.delete("/products/{product_id}", response_model=Dict[str, Any])
async def delete_admin_product(
    product_id: int,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Soft delete product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_deleted == False)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    try:
        product.is_deleted = True
        product.is_active = False  # Also deactivate

        await db.commit()

        return {
            "success": True,
            "message": f"Товар '{product.name}' успешно удален"
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления товара: {str(e)}"
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_admin_analytics(
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get admin analytics."""
    # Order statistics
    service = OrderService(db)
    order_stats = await service.get_orders_stats()

    # Revenue statistics
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount))
        .where(Order.status == OrderStatus.COMPLETED, Order.is_deleted == False)
    )
    total_revenue = revenue_result.scalar() or 0

    # Average order value
    avg_order_result = await db.execute(
        select(func.avg(Order.total_amount))
        .where(Order.is_deleted == False)
    )
    avg_order_value = avg_order_result.scalar() or 0

    # Total products
    products_result = await db.execute(
        select(func.count(Product.id))
        .where(Product.is_deleted == False)
    )
    total_products = products_result.scalar() or 0

    # Active products
    active_products_result = await db.execute(
        select(func.count(Product.id))
        .where(Product.is_deleted == False, Product.is_active == True)
    )
    active_products = active_products_result.scalar() or 0

    # Total users
    users_result = await db.execute(
        select(func.count(User.id))
        .where(User.is_deleted == False)
    )
    total_users = users_result.scalar() or 0

    return {
        "success": True,
        "analytics": {
            "orders": order_stats,
            "revenue": {
                "total": total_revenue,
                "formatted_total": f"{int(total_revenue)}₽",
                "average_order": avg_order_value,
                "formatted_average": f"{int(avg_order_value)}₽"
            },
            "products": {
                "total": total_products,
                "active": active_products,
                "inactive": total_products - active_products
            },
            "users": {
                "total": total_users
            }
        }
    }