"""Payment service for handling payment business logic."""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(
        self,
        order: Order,
        payment_method: PaymentMethod = PaymentMethod.TELEGRAM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """
        Create a new payment for an order.

        Args:
            order: Order to create payment for
            payment_method: Payment method
            metadata: Additional payment metadata

        Returns:
            Created payment instance
        """
        try:
            payment = Payment(
                order_id=order.id,
                amount=order.total_amount,
                payment_method=payment_method,
                payment_metadata=metadata or {}
            )

            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)

            logger.info(f"Payment created: {payment.id} for order {order.id}")
            return payment

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create payment for order {order.id}: {e}")
            raise

    async def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID with order details."""
        result = await self.db.execute(
            select(Payment)
            .options(selectinload(Payment.order))
            .where(Payment.id == payment_id, Payment.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_order_id(self, order_id: int) -> Optional[Payment]:
        """Get payment by order ID."""
        result = await self.db.execute(
            select(Payment)
            .options(selectinload(Payment.order))
            .where(Payment.order_id == order_id, Payment.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def update_payment_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        telegram_payment_charge_id: Optional[str] = None,
        provider_payment_charge_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        error_message: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """
        Update payment status and related data.

        Args:
            payment: Payment to update
            status: New payment status
            telegram_payment_charge_id: Telegram payment charge ID
            provider_payment_charge_id: Provider payment charge ID
            transaction_id: Transaction ID
            error_message: Error message if payment failed
            provider_data: Provider specific data

        Returns:
            Updated payment instance
        """
        try:
            # Update payment fields
            payment.status = status

            if telegram_payment_charge_id:
                payment.telegram_payment_charge_id = telegram_payment_charge_id

            if provider_payment_charge_id:
                payment.provider_payment_charge_id = provider_payment_charge_id

            if transaction_id:
                payment.transaction_id = transaction_id

            if error_message:
                payment.error_message = error_message

            if provider_data:
                payment.provider_data = provider_data

            await self.db.commit()
            await self.db.refresh(payment)

            # Update order status based on payment status
            await self._update_order_status_based_on_payment(payment)

            logger.info(f"Payment {payment.id} status updated to {status.value}")
            return payment

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update payment {payment.id} status: {e}")
            raise

    async def _update_order_status_based_on_payment(self, payment: Payment) -> None:
        """Update order status based on payment status."""
        try:
            # Load order if not already loaded
            if not payment.order:
                result = await self.db.execute(
                    select(Order).where(Order.id == payment.order_id)
                )
                order = result.scalar_one_or_none()
                if not order:
                    logger.error(f"Order {payment.order_id} not found")
                    return
            else:
                order = payment.order

            old_status = order.status

            if payment.status == PaymentStatus.SUCCESS:
                # Payment successful - confirm order if it's pending
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CONFIRMED
                    # Set confirmation timestamp
                    if hasattr(order, 'status_confirmed_at'):
                        order.status_confirmed_at = datetime.utcnow()
            elif payment.status == PaymentStatus.FAILED:
                # Payment failed - mark order as failed instead of cancelled for better tracking
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.FAILED
                    # Set failure timestamp if available
                    if hasattr(order, 'status_failed_at'):
                        order.status_failed_at = datetime.utcnow()

            # Save changes if status changed
            if order.status != old_status:
                await self.db.commit()
                await self.db.refresh(order)

                # Send notifications about status change
                await self._send_payment_notifications(payment, order, old_status)

                logger.info(
                    f"Order {order.id} status updated from {old_status.value} "
                    f"to {order.status.value} based on payment status"
                )

        except Exception as e:
            logger.error(f"Failed to update order status for payment {payment.id}: {e}")
            await self.db.rollback()

    async def _send_payment_notifications(
        self,
        payment: Payment,
        order: Order,
        old_order_status: OrderStatus
    ) -> None:
        """Send notifications based on payment status."""
        try:
            # Get user for notifications
            user_result = await self.db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {order.user_id} not found for notifications")
                return

            # Use new notification service
            notification_service = NotificationService(self.db)

            # Send notifications based on payment status
            if payment.status == PaymentStatus.SUCCESS:
                # Notify user about successful payment
                payment_data = {
                    "payment_id": payment.id,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method.value,
                    "telegram_payment_charge_id": payment.telegram_payment_charge_id,
                    "provider_payment_charge_id": payment.provider_payment_charge_id
                }
                await notification_service.notify_payment_success(order, payment_data)

                # Also notify about order status change if it changed
                if order.status != old_order_status:
                    await notification_service.notify_order_status_change(order, old_order_status)

            elif payment.status == PaymentStatus.FAILED:
                # Notify user and admin about payment failure
                error_msg = payment.error_message or "Неизвестная ошибка"
                await notification_service.notify_payment_failed(order, error_msg)

        except Exception as e:
            logger.error(f"Failed to send payment notifications for payment {payment.id}: {e}")

    async def process_successful_payment(
        self,
        order_id: int,
        payment_id: int,
        telegram_payment_charge_id: str,
        provider_payment_charge_id: str,
        provider_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process successful payment from Telegram.

        Args:
            order_id: Order ID
            payment_id: Payment ID
            telegram_payment_charge_id: Telegram payment charge ID
            provider_payment_charge_id: Provider payment charge ID
            provider_data: Provider specific data

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            payment = await self.get_payment_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return False

            if payment.order_id != order_id:
                logger.error(f"Payment {payment_id} does not belong to order {order_id}")
                return False

            if payment.status != PaymentStatus.PENDING:
                logger.warning(f"Payment {payment_id} is not pending, current status: {payment.status}")
                return False

            # Update payment as successful
            await self.update_payment_status(
                payment=payment,
                status=PaymentStatus.SUCCESS,
                telegram_payment_charge_id=telegram_payment_charge_id,
                provider_payment_charge_id=provider_payment_charge_id,
                provider_data=provider_data
            )

            logger.info(f"Payment {payment_id} processed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to process successful payment {payment_id}: {e}")
            return False

    async def process_failed_payment(
        self,
        payment_id: int,
        error_message: str
    ) -> bool:
        """
        Process failed payment.

        Args:
            payment_id: Payment ID
            error_message: Error message

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            payment = await self.get_payment_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return False

            if payment.status != PaymentStatus.PENDING:
                logger.warning(f"Payment {payment_id} is not pending, current status: {payment.status}")
                return False

            # Update payment as failed
            await self.update_payment_status(
                payment=payment,
                status=PaymentStatus.FAILED,
                error_message=error_message
            )

            logger.info(f"Payment {payment_id} marked as failed: {error_message}")
            return True

        except Exception as e:
            logger.error(f"Failed to process failed payment {payment_id}: {e}")
            return False

    async def process_refund(
        self,
        order_id: int,
        refund_amount: float,
        refund_reason: Optional[str] = None,
        processed_by_user_id: Optional[int] = None
    ) -> bool:
        """
        Process refund for an order.

        Args:
            order_id: Order ID to refund
            refund_amount: Amount to refund
            refund_reason: Reason for refund
            processed_by_user_id: User who processed the refund

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Get order
            order_result = await self.db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = order_result.scalar_one_or_none()

            if not order:
                logger.error(f"Order {order_id} not found for refund")
                return False

            # Validate refund amount
            if refund_amount > order.total_amount:
                logger.error(f"Refund amount {refund_amount} exceeds order total {order.total_amount}")
                return False

            # Get payment for this order
            payment = await self.get_payment_by_order_id(order_id)

            if payment and payment.status != PaymentStatus.SUCCESS:
                logger.warning(f"Cannot refund order {order_id} - payment status: {payment.status}")
                return False

            # Update order with refund information
            old_status = order.status
            order.status = OrderStatus.REFUNDED
            order.refund_amount = refund_amount
            order.refund_reason = refund_reason

            # Create status history for refund
            from app.models.order_status_history import OrderStatusHistory, StatusChangeReason

            history = OrderStatusHistory.create_status_change(
                order_id=order.id,
                from_status=old_status.value,
                to_status=OrderStatus.REFUNDED.value,
                reason=StatusChangeReason.REFUND_PROCESSED,
                changed_by_user_id=processed_by_user_id,
                notes=f"Возврат {refund_amount}₽. {refund_reason or ''}",
                system_message=f"Refund processed: {refund_amount}"
            )

            self.db.add(history)
            await self.db.commit()
            await self.db.refresh(order)

            # Send refund notification
            await self._send_payment_notifications(payment, order, old_status)

            logger.info(f"Refund processed for order {order_id}: {refund_amount}₽")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to process refund for order {order_id}: {e}")
            return False