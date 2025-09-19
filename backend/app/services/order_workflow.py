"""Order workflow service for automation and status management."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus, OrderPriority
from app.models.order_status_history import OrderStatusHistory, StatusChangeReason
from app.models.user import User
from app.models.payment import Payment, PaymentStatus
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class OrderWorkflowError(Exception):
    """Order workflow specific error."""
    pass


class StatusTransitionError(OrderWorkflowError):
    """Invalid status transition error."""
    pass


class OrderWorkflow:
    """
    Order workflow engine for managing status transitions and automation.

    Handles:
    - Status transition validation
    - Automatic status transitions
    - Workflow automation rules
    - Order processing logic
    - Integration with payment and notification systems
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

        # Define valid status transitions
        self.valid_transitions: Dict[OrderStatus, Set[OrderStatus]] = {
            OrderStatus.PENDING: {
                OrderStatus.CONFIRMED, OrderStatus.CANCELLED, OrderStatus.FAILED
            },
            OrderStatus.CONFIRMED: {
                OrderStatus.PREPARING, OrderStatus.CANCELLED
            },
            OrderStatus.PREPARING: {
                OrderStatus.READY, OrderStatus.CANCELLED
            },
            OrderStatus.READY: {
                OrderStatus.COMPLETED, OrderStatus.CANCELLED
            },
            OrderStatus.COMPLETED: {
                OrderStatus.REFUNDED  # Only allow refund from completed
            },
            OrderStatus.CANCELLED: {
                OrderStatus.REFUNDED  # Allow refund from cancelled
            },
            OrderStatus.FAILED: {
                OrderStatus.PENDING,  # Allow retry
                OrderStatus.CANCELLED
            },
            OrderStatus.REFUNDED: set()  # Terminal state
        }

        # Automatic transition rules based on conditions
        self.auto_transition_rules = {
            # Auto-confirm VIP orders after payment
            OrderStatus.PENDING: self._check_auto_confirm_conditions,
            # Auto-transition to preparing after confirmation (with delay)
            OrderStatus.CONFIRMED: self._check_auto_preparing_conditions,
            # Auto-transition to completed for pickup orders when ready
            OrderStatus.READY: self._check_auto_complete_conditions,
        }

        # Default preparation times by priority (in minutes)
        self.default_preparation_times = {
            OrderPriority.VIP: 15,
            OrderPriority.HIGH: 25,
            OrderPriority.NORMAL: 35,
            OrderPriority.LOW: 45
        }

    async def transition_status(
        self,
        order: Order,
        new_status: OrderStatus,
        reason: StatusChangeReason = StatusChangeReason.MANUAL_ADMIN,
        changed_by_user_id: Optional[int] = None,
        notes: Optional[str] = None,
        system_message: Optional[str] = None,
        workflow_data: Optional[Dict[str, Any]] = None,
        validate: bool = True,
        auto_calculate_times: bool = True
    ) -> Tuple[Order, OrderStatusHistory]:
        """
        Transition order to new status with validation and audit logging.

        Args:
            order: Order to transition
            new_status: Target status
            reason: Reason for transition
            changed_by_user_id: User making the change
            notes: Additional notes
            system_message: System-generated message
            workflow_data: Workflow metadata
            validate: Whether to validate transition
            auto_calculate_times: Whether to auto-calculate timing fields

        Returns:
            Tuple of (updated_order, history_record)

        Raises:
            StatusTransitionError: If transition is invalid
        """
        old_status = order.status

        # Validate transition if requested
        if validate:
            self._validate_transition(old_status, new_status)

        # Calculate duration from previous status
        duration_from_previous = None
        if old_status != new_status:
            # Find the most recent status change
            last_history = await self._get_last_status_history(order.id)
            if last_history:
                duration = datetime.utcnow() - last_history.changed_at
                duration_from_previous = int(duration.total_seconds() / 60)

        # Update order status and timestamps
        order.status = new_status
        await self._update_status_timestamps(order, new_status, auto_calculate_times)

        # Create status history record
        history = OrderStatusHistory.create_status_change(
            order_id=order.id,
            from_status=old_status.value if old_status else None,
            to_status=new_status.value,
            reason=reason,
            changed_by_user_id=changed_by_user_id,
            notes=notes,
            system_message=system_message,
            workflow_data=workflow_data
        )
        history.duration_from_previous = duration_from_previous

        # Save changes
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(order)
        await self.db.refresh(history)

        # Send notifications
        await self._send_status_change_notifications(order, old_status, new_status)

        # Execute post-transition hooks
        await self._execute_post_transition_hooks(order, old_status, new_status, history)

        logger.info(f"Order {order.id} status changed from {old_status.value} to {new_status.value}")

        return order, history

    def _validate_transition(self, from_status: OrderStatus, to_status: OrderStatus) -> None:
        """Validate if status transition is allowed."""
        if from_status == to_status:
            return  # No change, always valid

        valid_targets = self.valid_transitions.get(from_status, set())
        if to_status not in valid_targets:
            raise StatusTransitionError(
                f"Invalid transition from {from_status.value} to {to_status.value}. "
                f"Valid transitions: {[s.value for s in valid_targets]}"
            )

    async def _update_status_timestamps(self, order: Order, status: OrderStatus, auto_calculate: bool) -> None:
        """Update status-specific timestamp fields."""
        now = datetime.utcnow()

        timestamp_fields = {
            OrderStatus.PENDING: 'status_pending_at',
            OrderStatus.CONFIRMED: 'status_confirmed_at',
            OrderStatus.PREPARING: 'status_preparing_at',
            OrderStatus.READY: 'status_ready_at',
            OrderStatus.COMPLETED: 'status_completed_at',
            OrderStatus.CANCELLED: 'status_cancelled_at',
        }

        field_name = timestamp_fields.get(status)
        if field_name:
            setattr(order, field_name, now)

        # Auto-calculate timing fields if requested
        if auto_calculate:
            await self._auto_calculate_timing_fields(order, status)

    async def _auto_calculate_timing_fields(self, order: Order, status: OrderStatus) -> None:
        """Auto-calculate timing and preparation fields based on status."""
        now = datetime.utcnow()

        if status == OrderStatus.CONFIRMED:
            # Set estimated preparation time if not set
            if not order.estimated_preparation_time:
                order.estimated_preparation_time = self.default_preparation_times.get(
                    order.priority, self.default_preparation_times[OrderPriority.NORMAL]
                )

            # Calculate estimated delivery time
            if order.estimated_preparation_time:
                prep_time = timedelta(minutes=order.estimated_preparation_time)
                order.estimated_delivery_time = now + prep_time

        elif status == OrderStatus.PREPARING:
            # Mark actual preparation start
            if not order.actual_preparation_start:
                order.actual_preparation_start = now

        elif status == OrderStatus.READY:
            # Mark actual preparation end and calculate duration
            if not order.actual_preparation_end:
                order.actual_preparation_end = now

            if order.actual_preparation_start and not order.preparation_duration:
                duration = now - order.actual_preparation_start
                order.preparation_duration = int(duration.total_seconds() / 60)

        elif status == OrderStatus.COMPLETED:
            # Calculate total duration
            if not order.total_duration:
                duration = now - order.created_at
                order.total_duration = int(duration.total_seconds() / 60)

            # Mark delivery completed
            if order.delivery_type == "delivery":
                order.delivery_completed_at = now

    async def _get_last_status_history(self, order_id: int) -> Optional[OrderStatusHistory]:
        """Get the most recent status history record for an order."""
        result = await self.db.execute(
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.changed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _send_status_change_notifications(
        self,
        order: Order,
        old_status: OrderStatus,
        new_status: OrderStatus
    ) -> None:
        """Send notifications for status changes."""
        try:
            if old_status != new_status:
                await self.notification_service.notify_order_status_change(order, old_status)
        except Exception as e:
            logger.error(f"Failed to send status change notifications for order {order.id}: {e}")

    async def _execute_post_transition_hooks(
        self,
        order: Order,
        old_status: OrderStatus,
        new_status: OrderStatus,
        history: OrderStatusHistory
    ) -> None:
        """Execute post-transition hooks and automation."""
        try:
            # Schedule automatic transitions if applicable
            await self._schedule_automatic_transitions(order, new_status)

            # Update workflow metadata
            await self._update_workflow_metadata(order, new_status, history)

            # Execute status-specific hooks
            if new_status == OrderStatus.CONFIRMED:
                await self._on_order_confirmed(order)
            elif new_status == OrderStatus.PREPARING:
                await self._on_order_preparing(order)
            elif new_status == OrderStatus.READY:
                await self._on_order_ready(order)
            elif new_status == OrderStatus.COMPLETED:
                await self._on_order_completed(order)
            elif new_status == OrderStatus.CANCELLED:
                await self._on_order_cancelled(order)

        except Exception as e:
            logger.error(f"Error in post-transition hooks for order {order.id}: {e}")

    async def _schedule_automatic_transitions(self, order: Order, current_status: OrderStatus) -> None:
        """Schedule automatic transitions based on current status."""
        # Mark order for automatic processing
        order.set_automation_flag('auto_transition_scheduled', True)
        order.set_workflow_metadata_value('last_auto_check', datetime.utcnow().isoformat())

    async def _update_workflow_metadata(
        self,
        order: Order,
        new_status: OrderStatus,
        history: OrderStatusHistory
    ) -> None:
        """Update workflow metadata after status change."""
        order.set_workflow_metadata_value(f'status_{new_status.value}_at', datetime.utcnow().isoformat())
        order.set_workflow_metadata_value('last_status_change_id', history.id)
        order.set_workflow_metadata_value('workflow_version', '1.0')

    # Status-specific hooks
    async def _on_order_confirmed(self, order: Order) -> None:
        """Hook executed when order is confirmed."""
        # Set automation flags for kitchen notification
        order.set_automation_flag('kitchen_notified', False)
        order.set_automation_flag('auto_preparing_eligible', True)

    async def _on_order_preparing(self, order: Order) -> None:
        """Hook executed when order starts preparing."""
        order.set_automation_flag('kitchen_notified', True)
        order.set_automation_flag('preparation_started', True)

    async def _on_order_ready(self, order: Order) -> None:
        """Hook executed when order is ready."""
        # For pickup orders, they can auto-complete when customer arrives
        if order.delivery_type == "pickup":
            order.set_automation_flag('auto_complete_eligible', True)

    async def _on_order_completed(self, order: Order) -> None:
        """Hook executed when order is completed."""
        order.set_automation_flag('workflow_completed', True)
        order.set_automation_flag('feedback_eligible', True)

    async def _on_order_cancelled(self, order: Order) -> None:
        """Hook executed when order is cancelled."""
        order.set_automation_flag('workflow_cancelled', True)
        order.set_automation_flag('refund_eligible', True)

    # Automatic transition condition checks
    async def _check_auto_confirm_conditions(self, order: Order) -> Optional[OrderStatus]:
        """Check if order should be auto-confirmed."""
        # Auto-confirm VIP orders with successful payment
        if order.priority == OrderPriority.VIP:
            payment = await self._get_order_payment(order.id)
            if payment and payment.status == PaymentStatus.SUCCESS:
                return OrderStatus.CONFIRMED

        # Auto-confirm cash orders for high priority
        if order.payment_method.lower() == "cash" and order.priority in [OrderPriority.HIGH, OrderPriority.VIP]:
            return OrderStatus.CONFIRMED

        return None

    async def _check_auto_preparing_conditions(self, order: Order) -> Optional[OrderStatus]:
        """Check if order should auto-transition to preparing."""
        # Auto-transition after 5 minutes for VIP orders
        if order.priority == OrderPriority.VIP and order.status_confirmed_at:
            time_since_confirm = datetime.utcnow() - order.status_confirmed_at
            if time_since_confirm >= timedelta(minutes=5):
                return OrderStatus.PREPARING

        return None

    async def _check_auto_complete_conditions(self, order: Order) -> Optional[OrderStatus]:
        """Check if order should auto-complete."""
        # For pickup orders, we don't auto-complete (require manual confirmation)
        # For delivery orders, we don't auto-complete (require delivery confirmation)
        return None

    async def _get_order_payment(self, order_id: int) -> Optional[Payment]:
        """Get payment for order."""
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id, Payment.is_deleted == False)
        )
        return result.scalar_one_or_none()

    # Bulk operations
    async def bulk_transition_orders(
        self,
        order_ids: List[int],
        new_status: OrderStatus,
        reason: StatusChangeReason = StatusChangeReason.MANUAL_ADMIN,
        changed_by_user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk transition multiple orders to a new status.

        Args:
            order_ids: List of order IDs to transition
            new_status: Target status
            reason: Reason for transition
            changed_by_user_id: User making the change
            notes: Additional notes

        Returns:
            Dictionary with success/failure counts and details
        """
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0,
            'success_count': 0,
            'failure_count': 0
        }

        for order_id in order_ids:
            results['total_processed'] += 1

            try:
                # Get order
                order_result = await self.db.execute(
                    select(Order)
                    .where(Order.id == order_id, Order.is_deleted == False)
                )
                order = order_result.scalar_one_or_none()

                if not order:
                    results['failed'].append({
                        'order_id': order_id,
                        'error': 'Order not found'
                    })
                    results['failure_count'] += 1
                    continue

                # Transition status
                updated_order, history = await self.transition_status(
                    order=order,
                    new_status=new_status,
                    reason=reason,
                    changed_by_user_id=changed_by_user_id,
                    notes=notes,
                    validate=True
                )

                results['successful'].append({
                    'order_id': order_id,
                    'old_status': history.from_status,
                    'new_status': history.to_status,
                    'history_id': history.id
                })
                results['success_count'] += 1

            except Exception as e:
                results['failed'].append({
                    'order_id': order_id,
                    'error': str(e)
                })
                results['failure_count'] += 1
                logger.error(f"Failed to transition order {order_id}: {e}")

        logger.info(
            f"Bulk status transition completed: {results['success_count']} successful, "
            f"{results['failure_count']} failed"
        )

        return results

    # Automation and monitoring
    async def process_automatic_transitions(self) -> Dict[str, Any]:
        """
        Process automatic transitions for eligible orders.

        Returns:
            Dictionary with processing results
        """
        results = {
            'processed_orders': 0,
            'transitions_made': 0,
            'errors': []
        }

        try:
            # Get orders eligible for automatic processing
            eligible_orders = await self._get_orders_for_auto_processing()

            for order in eligible_orders:
                results['processed_orders'] += 1

                try:
                    # Check transition rules for current status
                    rule_func = self.auto_transition_rules.get(order.status)
                    if rule_func:
                        target_status = await rule_func(order)
                        if target_status and target_status != order.status:
                            await self.transition_status(
                                order=order,
                                new_status=target_status,
                                reason=StatusChangeReason.AUTOMATIC,
                                validate=True
                            )
                            results['transitions_made'] += 1

                except Exception as e:
                    error_msg = f"Error processing order {order.id}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error in automatic transition processing: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        return results

    async def _get_orders_for_auto_processing(self) -> List[Order]:
        """Get orders eligible for automatic processing."""
        # Get active orders that haven't been processed recently
        result = await self.db.execute(
            select(Order)
            .where(
                and_(
                    Order.status.in_([
                        OrderStatus.PENDING,
                        OrderStatus.CONFIRMED,
                        OrderStatus.PREPARING,
                        OrderStatus.READY
                    ]),
                    Order.is_deleted == False,
                    or_(
                        Order.automation_flags.is_(None),
                        Order.automation_flags['auto_transition_scheduled'].astext.cast(
                            sqlalchemy.Boolean
                        ) == True
                    )
                )
            )
            .options(selectinload(Order.payment))
            .limit(100)  # Process in batches
        )
        return result.scalars().all()

    async def get_overdue_orders(self, threshold_minutes: int = 60) -> List[Order]:
        """Get orders that are overdue based on estimated completion time."""
        threshold_time = datetime.utcnow() - timedelta(minutes=threshold_minutes)

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(
                and_(
                    Order.status.in_([
                        OrderStatus.CONFIRMED,
                        OrderStatus.PREPARING,
                        OrderStatus.READY
                    ]),
                    Order.is_deleted == False,
                    or_(
                        Order.estimated_delivery_time < datetime.utcnow(),
                        Order.created_at < threshold_time
                    )
                )
            )
            .order_by(Order.created_at.asc())
        )
        return result.scalars().all()

    async def get_order_timeline(self, order_id: int) -> List[Dict[str, Any]]:
        """Get complete timeline of an order including status history."""
        # Get order
        order_result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.is_deleted == False)
        )
        order = order_result.scalar_one_or_none()

        if not order:
            return []

        # Get status history
        history_result = await self.db.execute(
            select(OrderStatusHistory)
            .options(selectinload(OrderStatusHistory.changed_by))
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.changed_at.asc())
        )
        history_records = history_result.scalars().all()

        timeline = []

        # Add creation event
        timeline.append({
            'timestamp': order.created_at,
            'event_type': 'order_created',
            'status': OrderStatus.PENDING.value,
            'description': 'Заказ создан',
            'user': None,
            'duration': None,
            'notes': None
        })

        # Add status history events
        for record in history_records:
            timeline.append({
                'timestamp': record.changed_at,
                'event_type': 'status_change',
                'status': record.to_status,
                'description': f'Статус изменен на "{record.to_status_display}"',
                'user': record.changed_by.username if record.changed_by else None,
                'duration': record.duration_display,
                'notes': record.notes,
                'reason': record.reason_display,
                'system_message': record.system_message
            })

        return timeline