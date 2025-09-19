"""Enhanced order service with workflow integration."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.models.order import Order, OrderStatus, OrderItem, OrderPriority
from app.models.order_status_history import OrderStatusHistory, StatusChangeReason
from app.models.user import User
from app.services.notification import NotificationService
from app.services.order_workflow import OrderWorkflow

logger = logging.getLogger(__name__)


class OrderService:
    """Enhanced order service with workflow management."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        if db:
            self.workflow = OrderWorkflow(db)
            self.notification_service = NotificationService(db)
        else:
            self.workflow = None
            self.notification_service = None

    async def get_orders_stats(self) -> Dict[str, Any]:
        """Get enhanced orders statistics."""
        async with get_async_session() as db:
            # Total orders
            total_result = await db.execute(
                select(func.count(Order.id)).where(Order.is_deleted == False)
            )
            total = total_result.scalar() or 0

            # Status counts
            status_counts = {}
            for status in OrderStatus:
                count_result = await db.execute(
                    select(func.count(Order.id)).where(
                        Order.status == status,
                        Order.is_deleted == False
                    )
                )
                status_counts[status.value] = count_result.scalar() or 0

            # Processing orders (confirmed + preparing + ready)
            processing = status_counts.get('confirmed', 0) + \
                        status_counts.get('preparing', 0) + \
                        status_counts.get('ready', 0)

            # Priority counts
            priority_result = await db.execute(
                select(Order.priority, func.count(Order.id))
                .where(Order.is_deleted == False, Order.is_active == True)
                .group_by(Order.priority)
            )
            priority_counts = {priority.value: count for priority, count in priority_result.all()}

            # Overdue orders count
            overdue_result = await db.execute(
                select(func.count(Order.id)).where(
                    and_(
                        Order.is_deleted == False,
                        Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]),
                        Order.estimated_delivery_time < datetime.utcnow()
                    )
                )
            )
            overdue_count = overdue_result.scalar() or 0

            # Today's orders
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())

            today_result = await db.execute(
                select(func.count(Order.id)).where(
                    and_(
                        Order.is_deleted == False,
                        Order.created_at >= today_start,
                        Order.created_at <= today_end
                    )
                )
            )
            today_orders = today_result.scalar() or 0

            return {
                'total': total,
                'pending': status_counts.get('pending', 0),
                'processing': processing,
                'completed': status_counts.get('completed', 0),
                'cancelled': status_counts.get('cancelled', 0),
                'failed': status_counts.get('failed', 0),
                'refunded': status_counts.get('refunded', 0),
                'status_counts': status_counts,
                'priority_counts': priority_counts,
                'overdue_count': overdue_count,
                'today_orders': today_orders
            }

    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Get user orders."""
        async with get_async_session() as db:
            result = await db.execute(
                select(Order)
                .where(
                    Order.user_id == user_id,
                    Order.is_deleted == False
                )
                .order_by(Order.created_at.desc())
            )
            return result.scalars().all()

    async def create_order(
        self,
        user_id: int,
        customer_name: str,
        customer_phone: str,
        delivery_address: Optional[str],
        notes: Optional[str],
        payment_method: str,
        items: List[Dict],
        total_amount: float,
        db: AsyncSession
    ) -> Order:
        """Create a new order with notifications."""
        try:
            # Create order
            order = Order(
                user_id=user_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                delivery_address=delivery_address,
                notes=notes,
                payment_method=payment_method,
                total_amount=total_amount,
                status=OrderStatus.PENDING
            )

            db.add(order)
            await db.flush()  # Get order ID

            # Add order items
            for item_data in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    price=item_data['price']
                )
                db.add(order_item)

            await db.commit()
            await db.refresh(order)

            # Send notifications
            notification_service = NotificationService(db)
            await notification_service.notify_order_created(order)

            logger.info(f"Order {order.id} created successfully")
            return order

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating order: {e}")
            raise

    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        db: AsyncSession,
        changed_by_user_id: Optional[int] = None,
        reason: StatusChangeReason = StatusChangeReason.MANUAL_ADMIN,
        notes: Optional[str] = None,
        notify: bool = True
    ) -> Optional[Order]:
        """Update order status using workflow engine."""
        try:
            # Get order
            result = await db.execute(
                select(Order).where(
                    Order.id == order_id,
                    Order.is_deleted == False
                )
            )
            order = result.scalar_one_or_none()

            if not order:
                logger.warning(f"Order {order_id} not found")
                return None

            # Use workflow engine for status transition
            workflow = OrderWorkflow(db)
            updated_order, history = await workflow.transition_status(
                order=order,
                new_status=new_status,
                reason=reason,
                changed_by_user_id=changed_by_user_id,
                notes=notes,
                validate=True
            )

            logger.info(f"Order {order_id} status updated via workflow: {history.from_status} -> {history.to_status}")
            return updated_order

        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {e}")
            raise

    async def get_order_by_id(self, order_id: int, db: AsyncSession) -> Optional[Order]:
        """Get order by ID with related data."""
        try:
            result = await db.execute(
                select(Order)
                .options(
                    selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(Order.user),
                    selectinload(Order.payment)
                )
                .where(
                    Order.id == order_id,
                    Order.is_deleted == False
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None

    async def cancel_order(
        self,
        order_id: int,
        db: AsyncSession,
        cancelled_by_user_id: Optional[int] = None,
        reason: Optional[str] = None,
        refund_amount: Optional[float] = None
    ) -> bool:
        """Cancel an order with enhanced workflow support."""
        try:
            # Get order first
            result = await db.execute(
                select(Order).where(Order.id == order_id, Order.is_deleted == False)
            )
            order = result.scalar_one_or_none()

            if not order:
                logger.warning(f"Order {order_id} not found")
                return False

            # Check if order can be cancelled
            if not order.can_be_cancelled:
                logger.warning(f"Order {order_id} cannot be cancelled in current status: {order.status.value}")
                return False

            # Update cancellation fields
            order.cancelled_by_user_id = cancelled_by_user_id
            order.cancellation_reason = reason
            if refund_amount:
                order.refund_amount = refund_amount

            # Use workflow to transition status
            workflow = OrderWorkflow(db)
            reason_enum = StatusChangeReason.CANCELLED_BY_CUSTOMER if cancelled_by_user_id else StatusChangeReason.CANCELLED_BY_ADMIN

            updated_order, history = await workflow.transition_status(
                order=order,
                new_status=OrderStatus.CANCELLED,
                reason=reason_enum,
                changed_by_user_id=cancelled_by_user_id,
                notes=f"Причина отмены: {reason}" if reason else None,
                validate=True
            )

            logger.info(f"Order {order_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def get_active_orders(self, db: AsyncSession) -> List[Order]:
        """Get all active orders (not completed or cancelled)."""
        try:
            result = await db.execute(
                select(Order)
                .options(
                    selectinload(Order.items).selectinload(OrderItem.product),
                    selectinload(Order.user)
                )
                .where(
                    Order.status.in_([
                        OrderStatus.PENDING,
                        OrderStatus.CONFIRMED,
                        OrderStatus.PREPARING,
                        OrderStatus.READY
                    ]),
                    Order.is_deleted == False
                )
                .order_by(Order.created_at.desc())
            )
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting active orders: {e}")
            return []

    async def get_orders_by_status(
        self,
        status: OrderStatus,
        db: AsyncSession,
        limit: Optional[int] = None
    ) -> List[Order]:
        """Get orders by status."""
        try:
            query = select(Order).options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.user)
            ).where(
                Order.status == status,
                Order.is_deleted == False
            ).order_by(Order.created_at.desc())

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting orders by status {status.value}: {e}")
            return []

    # Enhanced methods for workflow management
    async def get_order_timeline(self, order_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get complete timeline of an order."""
        try:
            workflow = OrderWorkflow(db)
            return await workflow.get_order_timeline(order_id)
        except Exception as e:
            logger.error(f"Error getting order timeline {order_id}: {e}")
            return []

    async def bulk_update_status(
        self,
        order_ids: List[int],
        new_status: OrderStatus,
        changed_by_user_id: Optional[int] = None,
        reason: StatusChangeReason = StatusChangeReason.MANUAL_ADMIN,
        notes: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Bulk update multiple orders status."""
        try:
            session = db or await get_async_session().__anext__()
            workflow = OrderWorkflow(session)

            results = await workflow.bulk_transition_orders(
                order_ids=order_ids,
                new_status=new_status,
                reason=reason,
                changed_by_user_id=changed_by_user_id,
                notes=notes
            )

            return results

        except Exception as e:
            logger.error(f"Error in bulk status update: {e}")
            return {
                'successful': [],
                'failed': [{'error': str(e)}],
                'total_processed': 0,
                'success_count': 0,
                'failure_count': 1
            }

    async def get_overdue_orders(
        self,
        threshold_minutes: int = 60,
        db: Optional[AsyncSession] = None
    ) -> List[Order]:
        """Get overdue orders."""
        try:
            session = db or await get_async_session().__anext__()
            workflow = OrderWorkflow(session)
            return await workflow.get_overdue_orders(threshold_minutes)
        except Exception as e:
            logger.error(f"Error getting overdue orders: {e}")
            return []

    async def process_automatic_transitions(
        self,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Process automatic status transitions."""
        try:
            session = db or await get_async_session().__anext__()
            workflow = OrderWorkflow(session)
            return await workflow.process_automatic_transitions()
        except Exception as e:
            logger.error(f"Error processing automatic transitions: {e}")
            return {
                'processed_orders': 0,
                'transitions_made': 0,
                'errors': [str(e)]
            }

    async def get_orders_by_priority(
        self,
        priority: OrderPriority,
        db: AsyncSession,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Order]:
        """Get orders by priority level."""
        try:
            query = select(Order).options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.user)
            ).where(
                Order.priority == priority,
                Order.is_deleted == False
            )

            if active_only:
                query = query.where(Order.is_active == True)

            query = query.order_by(Order.created_at.desc())

            if limit:
                query = query.limit(limit)

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting orders by priority {priority.value}: {e}")
            return []

    async def update_order_priority(
        self,
        order_id: int,
        new_priority: OrderPriority,
        changed_by_user_id: Optional[int] = None,
        reason: Optional[str] = None,
        db: AsyncSession
    ) -> Optional[Order]:
        """Update order priority."""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id, Order.is_deleted == False)
            )
            order = result.scalar_one_or_none()

            if not order:
                logger.warning(f"Order {order_id} not found")
                return None

            old_priority = order.priority
            order.priority = new_priority

            # Create status history record for priority change
            history = OrderStatusHistory.create_status_change(
                order_id=order.id,
                from_status=order.status.value,
                to_status=order.status.value,
                reason=StatusChangeReason.MANUAL_ADMIN,
                changed_by_user_id=changed_by_user_id,
                notes=f"Приоритет изменен с {old_priority.value} на {new_priority.value}. {reason or ''}",
                system_message=f"Priority changed from {old_priority.value} to {new_priority.value}"
            )

            db.add(history)
            await db.commit()
            await db.refresh(order)

            logger.info(f"Order {order_id} priority updated from {old_priority.value} to {new_priority.value}")
            return order

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating order {order_id} priority: {e}")
            raise

    async def assign_courier(
        self,
        order_id: int,
        courier_name: str,
        changed_by_user_id: Optional[int] = None,
        db: AsyncSession
    ) -> Optional[Order]:
        """Assign courier to an order."""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id, Order.is_deleted == False)
            )
            order = result.scalar_one_or_none()

            if not order:
                logger.warning(f"Order {order_id} not found")
                return None

            if order.delivery_type != "delivery":
                logger.warning(f"Order {order_id} is not a delivery order")
                return None

            old_courier = order.courier_assigned
            order.courier_assigned = courier_name

            # Create history record
            history = OrderStatusHistory.create_status_change(
                order_id=order.id,
                from_status=order.status.value,
                to_status=order.status.value,
                reason=StatusChangeReason.MANUAL_ADMIN,
                changed_by_user_id=changed_by_user_id,
                notes=f"Курьер назначен: {courier_name}" + (f" (был: {old_courier})" if old_courier else ""),
                system_message=f"Courier assigned: {courier_name}"
            )

            db.add(history)
            await db.commit()
            await db.refresh(order)

            logger.info(f"Courier {courier_name} assigned to order {order_id}")
            return order

        except Exception as e:
            await db.rollback()
            logger.error(f"Error assigning courier to order {order_id}: {e}")
            raise

    async def schedule_delivery(
        self,
        order_id: int,
        scheduled_time: datetime,
        changed_by_user_id: Optional[int] = None,
        db: AsyncSession
    ) -> Optional[Order]:
        """Schedule delivery for an order."""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id, Order.is_deleted == False)
            )
            order = result.scalar_one_or_none()

            if not order:
                logger.warning(f"Order {order_id} not found")
                return None

            order.delivery_scheduled_at = scheduled_time

            # Create history record
            history = OrderStatusHistory.create_status_change(
                order_id=order.id,
                from_status=order.status.value,
                to_status=order.status.value,
                reason=StatusChangeReason.MANUAL_ADMIN,
                changed_by_user_id=changed_by_user_id,
                notes=f"Доставка запланирована на {scheduled_time.strftime('%d.%m.%Y %H:%M')}",
                system_message=f"Delivery scheduled for {scheduled_time.isoformat()}"
            )

            db.add(history)
            await db.commit()
            await db.refresh(order)

            logger.info(f"Delivery scheduled for order {order_id} at {scheduled_time}")
            return order

        except Exception as e:
            await db.rollback()
            logger.error(f"Error scheduling delivery for order {order_id}: {e}")
            raise

    async def get_dashboard_data(self, db: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive dashboard data for admin interface."""
        try:
            # Basic stats
            stats = await self.get_orders_stats()

            # Overdue orders
            overdue_orders = await self.get_overdue_orders(db=db)

            # VIP orders
            vip_orders = await self.get_orders_by_priority(
                priority=OrderPriority.VIP,
                db=db,
                active_only=True,
                limit=10
            )

            # Recent orders
            recent_result = await db.execute(
                select(Order)
                .options(selectinload(Order.user))
                .where(Order.is_deleted == False)
                .order_by(Order.created_at.desc())
                .limit(20)
            )
            recent_orders = recent_result.scalars().all()

            # Performance metrics
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            avg_prep_time_result = await db.execute(
                select(func.avg(Order.preparation_duration))
                .where(
                    and_(
                        Order.is_deleted == False,
                        Order.preparation_duration.isnot(None),
                        Order.created_at >= today_start
                    )
                )
            )
            avg_prep_time = avg_prep_time_result.scalar() or 0

            return {
                'stats': stats,
                'overdue_orders': [
                    {
                        'id': order.id,
                        'customer_name': order.customer_name,
                        'total_amount': order.total_amount,
                        'status': order.status.value,
                        'created_at': order.created_at.isoformat(),
                        'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                        'priority': order.priority.value
                    }
                    for order in overdue_orders[:10]  # Limit to 10 for dashboard
                ],
                'vip_orders': [
                    {
                        'id': order.id,
                        'customer_name': order.customer_name,
                        'total_amount': order.total_amount,
                        'status': order.status.value,
                        'created_at': order.created_at.isoformat(),
                    }
                    for order in vip_orders
                ],
                'recent_orders': [
                    {
                        'id': order.id,
                        'customer_name': order.customer_name,
                        'total_amount': order.total_amount,
                        'status': order.status.value,
                        'status_display': order.status_display,
                        'created_at': order.created_at.isoformat(),
                        'priority': order.priority.value
                    }
                    for order in recent_orders
                ],
                'performance': {
                    'avg_preparation_time_today': round(avg_prep_time, 1) if avg_prep_time else 0,
                    'overdue_count': len(overdue_orders),
                    'vip_count': len(vip_orders)
                }
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                'stats': {},
                'overdue_orders': [],
                'vip_orders': [],
                'recent_orders': [],
                'performance': {},
                'error': str(e)
            }