"""Enhanced Order API endpoints with status management."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.models.order import Order, OrderItem, OrderStatus, OrderPriority
from app.models.order_status_history import StatusChangeReason
from app.models.product import Product
from app.models.user import User
from app.models.payment import PaymentMethod
from app.services.order import OrderService
from app.services.order_workflow import OrderWorkflow
from app.services.notification import NotificationService
from app.services.payment import PaymentService
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderUpdate,
    OrderStatusUpdateRequest, OrderPriorityUpdateRequest, OrderCancelRequest,
    BulkStatusUpdateRequest, BulkUpdateResponse,
    CourierAssignRequest, DeliveryScheduleRequest,
    OrderStatsResponse, DashboardResponse, OrderTimelineResponse,
    AutomationProcessingResponse, OrderTimelineEvent
)
from app.middleware.auth import require_manager_or_admin, get_current_user, api_rate_limit

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Create new order from cart."""
    try:
        # Validate minimum order amount
        if order_data.total_amount < 1500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Минимальная сумма заказа 1500₽. Текущая сумма: {order_data.total_amount}₽"
            )

        # Verify user exists
        user_result = await db.execute(
            select(User).where(User.telegram_id == order_data.telegram_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )

        # Create order
        order = Order(
            user_id=user.id,
            total_amount=order_data.total_amount,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            delivery_address=order_data.delivery_address,
            notes=order_data.notes,
            payment_method=order_data.payment_method
        )

        db.add(order)
        await db.flush()  # Get order.id for items

        # Create order items
        total_calculated = 0
        for item in order_data.items:
            # Get product to verify price
            product_result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = product_result.scalar_one_or_none()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Товар с ID {item.product_id} не найден"
                )

            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=product.price  # Use current product price
            )

            db.add(order_item)
            total_calculated += product.price * item.quantity

        # Verify total amount matches calculated
        if abs(total_calculated - order_data.total_amount) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Неверная сумма заказа. Ожидается: {total_calculated}₽, получено: {order_data.total_amount}₽"
            )

        await db.commit()
        await db.refresh(order)

        # Create payment for the order if payment method is not cash
        payment_id = None
        if order_data.payment_method and order_data.payment_method.lower() != "cash":
            try:
                payment_service = PaymentService(db)
                payment_method = PaymentMethod.TELEGRAM if order_data.payment_method.lower() in ["card", "telegram"] else PaymentMethod.CARD

                payment = await payment_service.create_payment(
                    order=order,
                    payment_method=payment_method,
                    metadata={"created_via": "api", "user_telegram_id": user.telegram_id}
                )
                payment_id = payment.id

                logger.info(f"Payment {payment.id} created for order {order.id}")

            except Exception as e:
                logger.error(f"Failed to create payment for order {order.id}: {e}")
                # Don't fail the order creation if payment creation fails
                pass

        # Load relationships for response and prepare notification data
        items_for_notification = []
        items_result = await db.execute(
            select(OrderItem, Product)
            .join(Product, OrderItem.product_id == Product.id)
            .where(OrderItem.order_id == order.id)
        )
        items_data = items_result.all()

        for order_item, product in items_data:
            items_for_notification.append({
                "product_name": product.name,
                "quantity": order_item.quantity,
                "formatted_price": order_item.formatted_price,
                "formatted_total": order_item.formatted_total
            })

        # Send notification to admin (fire-and-forget)
        import asyncio
        asyncio.create_task(
            NotificationService.notify_new_order(order, items_for_notification)
        )

        response_data = {
            "success": True,
            "message": "Заказ успешно создан",
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
                "created_at": order.created_at.isoformat()
            }
        }

        # Add payment info if payment was created
        if payment_id:
            response_data["payment"] = {
                "id": payment_id,
                "status": "pending",
                "amount": order.total_amount,
                "method": order_data.payment_method
            }
            response_data["message"] = "Заказ создан. Требуется оплата."

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания заказа: {str(e)}"
        )


@router.get("/{order_id}", response_model=Dict[str, Any])
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get order by ID."""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.is_deleted == False)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )

    # Check access permissions
    if current_user:
        from app.models.user import UserRole
        # Admins and managers can access all orders
        if current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            pass  # Full access
        # Users can only access their own orders
        elif current_user.role == UserRole.USER:
            if order.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You can only view your own orders."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    else:
        # Anonymous access not allowed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Load order items with product details
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
            "formatted_price": order_item.formatted_price,
            "formatted_total": order_item.formatted_total
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
            "items": items
        }
    }


@router.put("/{order_id}/status", response_model=Dict[str, Any])
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdateRequest,
    request: Request,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Update order status with enhanced workflow support."""
    try:
        service = OrderService(db)

        # Convert schema enum to model enum
        from app.models.order import OrderStatus as ModelOrderStatus
        from app.models.order_status_history import StatusChangeReason as ModelStatusChangeReason

        model_status = ModelOrderStatus(status_update.status.value)
        model_reason = ModelStatusChangeReason(status_update.reason.value) if status_update.reason else ModelStatusChangeReason.MANUAL_ADMIN

        updated_order = await service.update_order_status(
            order_id=order_id,
            new_status=model_status,
            db=db,
            changed_by_user_id=current_user.id,
            reason=model_reason,
            notes=status_update.notes
        )

        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )

        return {
            "success": True,
            "message": f"Статус заказа изменен на '{updated_order.status_display}'",
            "order": {
                "id": updated_order.id,
                "status": updated_order.status.value,
                "status_display": updated_order.status_display,
                "updated_at": updated_order.updated_at.isoformat()
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления статуса: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
async def get_orders(
    user_id: int = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Get orders with filtering."""
    # Check access permissions
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    from app.models.user import UserRole
    query = select(Order).where(Order.is_deleted == False)

    # Role-based filtering
    if current_user.role == UserRole.USER:
        # Regular users can only see their own orders
        query = query.where(Order.user_id == current_user.id)
        # Ignore user_id parameter for regular users
        user_id = None
    elif current_user.role in [UserRole.ADMIN, UserRole.MANAGER]:
        # Admins and managers can see all orders or filter by user_id
        if user_id:
            # Get user by telegram_id
            user_result = await db.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                query = query.where(Order.user_id == user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if status:
        try:
            order_status = OrderStatus(status)
            query = query.where(Order.status == order_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый статус: {status}"
            )

    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    orders = result.scalars().all()

    orders_data = []
    for order in orders:
        orders_data.append({
            "id": order.id,
            "status": order.status.value,
            "status_display": order.status_display,
            "total_amount": order.total_amount,
            "formatted_total": order.formatted_total,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "created_at": order.created_at.isoformat()
        })

    return {
        "success": True,
        "orders": orders_data,
        "count": len(orders_data)
    }


@router.get("/stats/summary", response_model=OrderStatsResponse)
async def get_order_stats(
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> OrderStatsResponse:
    """Get enhanced order statistics."""
    service = OrderService(db)
    stats = await service.get_orders_stats()
    return OrderStatsResponse(**stats)


# New enhanced endpoints for order status management

@router.get("/{order_id}/timeline", response_model=OrderTimelineResponse)
async def get_order_timeline(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> OrderTimelineResponse:
    """Get complete timeline of an order."""
    # Check if user has access to this order
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.is_deleted == False)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )

    # Check access permissions
    from app.models.user import UserRole
    if current_user.role == UserRole.USER:
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )

    service = OrderService(db)
    timeline = await service.get_order_timeline(order_id, db)

    return OrderTimelineResponse(
        order_id=order_id,
        timeline=[OrderTimelineEvent(**event) for event in timeline]
    )


@router.post("/bulk-status", response_model=BulkUpdateResponse)
async def bulk_update_order_status(
    bulk_request: BulkStatusUpdateRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> BulkUpdateResponse:
    """Bulk update order statuses."""
    try:
        service = OrderService(db)

        # Convert schema enums to model enums
        from app.models.order import OrderStatus as ModelOrderStatus
        from app.models.order_status_history import StatusChangeReason as ModelStatusChangeReason

        model_status = ModelOrderStatus(bulk_request.status.value)
        model_reason = ModelStatusChangeReason(bulk_request.reason.value) if bulk_request.reason else ModelStatusChangeReason.MANUAL_ADMIN

        results = await service.bulk_update_status(
            order_ids=bulk_request.order_ids,
            new_status=model_status,
            changed_by_user_id=current_user.id,
            reason=model_reason,
            notes=bulk_request.notes,
            db=db
        )

        return BulkUpdateResponse(**results)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка массового обновления: {str(e)}"
        )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_orders_dashboard(
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> DashboardResponse:
    """Get comprehensive dashboard data for admins."""
    try:
        service = OrderService(db)
        dashboard_data = await service.get_dashboard_data(db)
        return DashboardResponse(**dashboard_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения данных дашборда: {str(e)}"
        )


@router.get("/overdue", response_model=List[Dict[str, Any]])
async def get_overdue_orders(
    threshold_minutes: int = Query(60, ge=1, le=1440, description="Threshold in minutes"),
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """Get overdue orders."""
    try:
        service = OrderService(db)
        overdue_orders = await service.get_overdue_orders(threshold_minutes, db)

        return [
            {
                "id": order.id,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone,
                "total_amount": order.total_amount,
                "formatted_total": order.formatted_total,
                "status": order.status.value,
                "status_display": order.status_display,
                "priority": order.priority.value,
                "priority_display": order.priority_display,
                "created_at": order.created_at.isoformat(),
                "estimated_delivery_time": order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                "overdue_minutes": int((datetime.utcnow() - (order.estimated_delivery_time or order.created_at)).total_seconds() / 60)
            }
            for order in overdue_orders
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения просроченных заказов: {str(e)}"
        )


@router.post("/{order_id}/cancel", response_model=Dict[str, Any])
async def cancel_order(
    order_id: int,
    cancel_request: OrderCancelRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Cancel an order with optional refund."""
    try:
        service = OrderService(db)
        success = await service.cancel_order(
            order_id=order_id,
            db=db,
            cancelled_by_user_id=current_user.id,
            reason=cancel_request.reason,
            refund_amount=cancel_request.refund_amount
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось отменить заказ"
            )

        return {
            "success": True,
            "message": "Заказ успешно отменен",
            "order_id": order_id,
            "cancelled_by": current_user.id,
            "reason": cancel_request.reason,
            "refund_amount": cancel_request.refund_amount
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка отмены заказа: {str(e)}"
        )


@router.put("/{order_id}/priority", response_model=Dict[str, Any])
async def update_order_priority(
    order_id: int,
    priority_update: OrderPriorityUpdateRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Update order priority."""
    try:
        service = OrderService(db)

        # Convert schema enum to model enum
        from app.models.order import OrderPriority as ModelOrderPriority
        model_priority = ModelOrderPriority(priority_update.priority.value)

        updated_order = await service.update_order_priority(
            order_id=order_id,
            new_priority=model_priority,
            changed_by_user_id=current_user.id,
            reason=priority_update.reason,
            db=db
        )

        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )

        return {
            "success": True,
            "message": f"Приоритет заказа изменен на '{updated_order.priority_display}'",
            "order": {
                "id": updated_order.id,
                "priority": updated_order.priority.value,
                "priority_display": updated_order.priority_display,
                "updated_at": updated_order.updated_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления приоритета: {str(e)}"
        )


@router.put("/{order_id}/courier", response_model=Dict[str, Any])
async def assign_courier(
    order_id: int,
    courier_request: CourierAssignRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Assign courier to an order."""
    try:
        service = OrderService(db)
        updated_order = await service.assign_courier(
            order_id=order_id,
            courier_name=courier_request.courier_name,
            changed_by_user_id=current_user.id,
            db=db
        )

        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )

        return {
            "success": True,
            "message": f"Курьер '{courier_request.courier_name}' назначен на заказ",
            "order": {
                "id": updated_order.id,
                "courier_assigned": updated_order.courier_assigned,
                "updated_at": updated_order.updated_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка назначения курьера: {str(e)}"
        )


@router.put("/{order_id}/schedule", response_model=Dict[str, Any])
async def schedule_delivery(
    order_id: int,
    schedule_request: DeliveryScheduleRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """Schedule delivery for an order."""
    try:
        service = OrderService(db)
        updated_order = await service.schedule_delivery(
            order_id=order_id,
            scheduled_time=schedule_request.scheduled_time,
            changed_by_user_id=current_user.id,
            db=db
        )

        if not updated_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден"
            )

        return {
            "success": True,
            "message": f"Доставка запланирована на {schedule_request.scheduled_time.strftime('%d.%m.%Y %H:%M')}",
            "order": {
                "id": updated_order.id,
                "delivery_scheduled_at": updated_order.delivery_scheduled_at.isoformat() if updated_order.delivery_scheduled_at else None,
                "updated_at": updated_order.updated_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка планирования доставки: {str(e)}"
        )


@router.post("/automation/process", response_model=AutomationProcessingResponse)
async def process_automatic_transitions(
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
) -> AutomationProcessingResponse:
    """Process automatic status transitions."""
    try:
        service = OrderService(db)
        results = await service.process_automatic_transitions(db)
        return AutomationProcessingResponse(**results)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки автоматических переходов: {str(e)}"
        )