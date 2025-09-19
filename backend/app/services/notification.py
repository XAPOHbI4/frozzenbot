"""Enhanced notification service for Telegram bot with comprehensive order notifications."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.bot.bot import bot
from app.config import settings
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.models.notification import (
    Notification, NotificationTemplate, FeedbackRating,
    NotificationType, NotificationStatus, NotificationTarget
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Enhanced service for sending Telegram notifications with comprehensive tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Core notification methods
    async def send_notification(
        self,
        telegram_id: int,
        message: str,
        notification_type: NotificationType,
        target_type: NotificationTarget = NotificationTarget.USER,
        order_id: Optional[int] = None,
        user_id: Optional[int] = None,
        title: Optional[str] = None,
        inline_keyboard: Optional[Dict[str, Any]] = None,
        schedule_for: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Notification]:
        """Send notification and track it in database."""
        try:
            # Create notification record
            notification = Notification(
                target_type=target_type,
                target_telegram_id=telegram_id,
                notification_type=notification_type,
                title=title,
                message=message,
                order_id=order_id,
                user_id=user_id,
                scheduled_at=schedule_for,
                inline_keyboard=inline_keyboard,
                notification_metadata=metadata or {},
                status=NotificationStatus.SCHEDULED if schedule_for else NotificationStatus.PENDING
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            # Send immediately if not scheduled
            if not schedule_for:
                await self._send_telegram_message(notification)

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            await self.db.rollback()
            return None

    async def _send_telegram_message(self, notification: Notification) -> bool:
        """Send actual Telegram message."""
        try:
            # Prepare inline keyboard if provided
            reply_markup = None
            if notification.inline_keyboard:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup()
                for row in notification.inline_keyboard.get('inline_keyboard', []):
                    keyboard_row = []
                    for button in row:
                        keyboard_row.append(
                            InlineKeyboardButton(
                                text=button['text'],
                                callback_data=button.get('callback_data')
                            )
                        )
                    keyboard.row(*keyboard_row)
                reply_markup = keyboard

            # Send message
            message_result = await bot.send_message(
                chat_id=notification.target_telegram_id,
                text=notification.message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            await self.db.commit()

            logger.info(f"Notification {notification.id} sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending notification {notification.id}: {e}")

            # Update notification with error
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            notification.retry_count += 1
            await self.db.commit()

            return False

    # Order notification methods
    async def notify_order_created(self, order: Order) -> bool:
        """Notify user and admin about new order."""
        try:
            # Get user for customer notification
            user_result = await self.db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {order.user_id} not found for order {order.id}")
                return False

            # Notify customer
            customer_message = f"""
📦 <b>Заказ #{order.id} создан!</b>

Спасибо за ваш заказ! Мы получили его и вскоре обработаем.

💰 <b>Сумма:</b> {order.formatted_total}
📞 <b>Контакт:</b> {order.customer_phone}
🏠 <b>Адрес:</b> {order.delivery_address or 'Не указан'}

📝 <b>Статус:</b> {order.status_display}

Вы получите уведомление, когда статус заказа изменится.
            """.strip()

            await self.send_notification(
                telegram_id=user.telegram_id,
                message=customer_message,
                notification_type=NotificationType.ORDER_CREATED,
                target_type=NotificationTarget.USER,
                order_id=order.id,
                user_id=user.id,
                title="Заказ создан"
            )

            # Notify admin
            await self._notify_admin_new_order(order)

            return True

        except Exception as e:
            logger.error(f"Error notifying order created {order.id}: {e}")
            return False

    async def _notify_admin_new_order(self, order: Order) -> bool:
        """Notify admin about new order."""
        try:
            # Get order items with product details
            items_result = await self.db.execute(
                select(OrderItem)
                .options(selectinload(OrderItem.product))
                .where(OrderItem.order_id == order.id)
            )
            items = items_result.scalars().all()

            items_text = ""
            for item in items:
                items_text += f"• {item.product.name} - {item.quantity} шт. × {item.formatted_price} = {item.formatted_total}\n"

            admin_message = f"""
🔔 <b>НОВЫЙ ЗАКАЗ #{order.id}</b>

👤 <b>Покупатель:</b> {order.customer_name}
📞 <b>Телефон:</b> {order.customer_phone}
🏠 <b>Адрес доставки:</b> {order.delivery_address or 'Не указан'}

📦 <b>Состав заказа:</b>
{items_text}

💰 <b>Сумма заказа:</b> {order.formatted_total}
💳 <b>Способ оплаты:</b> {order.payment_method}

📝 <b>Примечания:</b> {order.notes or 'Нет'}

⏰ <b>Время заказа:</b> {order.created_at.strftime('%d.%m.%Y %H:%M:%S')}
            """.strip()

            await self.send_notification(
                telegram_id=settings.admin_id,
                message=admin_message,
                notification_type=NotificationType.ADMIN_NEW_ORDER,
                target_type=NotificationTarget.ADMIN,
                order_id=order.id,
                title="Новый заказ"
            )

            return True

        except Exception as e:
            logger.error(f"Error notifying admin about order {order.id}: {e}")
            return False

    async def notify_order_status_change(self, order: Order, old_status: OrderStatus) -> bool:
        """Notify user and admin about order status change with enhanced status support."""
        try:
            # Get user for notification
            user_result = await self.db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {order.user_id} not found for order {order.id}")
                return False

            # Extended notification type mapping for new statuses
            notification_type_map = {
                OrderStatus.CONFIRMED: NotificationType.ORDER_CONFIRMED,
                OrderStatus.PREPARING: NotificationType.ORDER_PREPARING,
                OrderStatus.READY: NotificationType.ORDER_READY,
                OrderStatus.COMPLETED: NotificationType.ORDER_COMPLETED,
                OrderStatus.CANCELLED: NotificationType.ORDER_CANCELLED,
                OrderStatus.REFUNDED: NotificationType.ORDER_REFUNDED,  # New status
                OrderStatus.FAILED: NotificationType.ORDER_FAILED,      # New status
            }

            notification_type = notification_type_map.get(order.status)
            if not notification_type:
                logger.warning(f"No notification type for status {order.status}")
                # Use generic status change notification
                notification_type = NotificationType.ORDER_STATUS_CHANGED

            # User notification messages
            user_messages = {
                OrderStatus.CONFIRMED: f"""
✅ <b>Заказ #{order.id} подтвержден!</b>

Отлично! Ваш заказ подтвержден и принят в работу.

💰 <b>Сумма:</b> {order.formatted_total}
🏷 <b>Статус:</b> {order.status_display}

Мы начинаем готовить ваш заказ. Вы получите уведомление, когда он будет готов.
                """.strip(),

                OrderStatus.PREPARING: f"""
👨‍🍳 <b>Заказ #{order.id} готовится!</b>

Ваш заказ уже в работе! Наши повара готовят для вас самые вкусные блюда.

🏷 <b>Статус:</b> {order.status_display}

Ожидайте уведомление о готовности заказа.
                """.strip(),

                OrderStatus.READY: f"""
📦 <b>Заказ #{order.id} готов!</b>

Отличные новости! Ваш заказ готов к выдаче.

🏷 <b>Статус:</b> {order.status_display}
🏠 <b>Адрес:</b> {order.delivery_address or 'Самовывоз'}

Если заказ на доставку - курьер скоро свяжется с вами.
Если самовывоз - можете забирать!
                """.strip(),

                OrderStatus.COMPLETED: f"""
✅ <b>Заказ #{order.id} выполнен!</b>

Спасибо за покупку! Ваш заказ успешно выполнен.

💰 <b>Сумма:</b> {order.formatted_total}

Надеемся, вам понравилось! Приходите к нам еще!
                """.strip(),

                OrderStatus.CANCELLED: f"""
❌ <b>Заказ #{order.id} отменен</b>

К сожалению, ваш заказ был отменен.

{f"💰 Сумма возврата: {order.refund_amount}₽" if order.refund_amount else ""}
{f"📝 Причина отмены: {order.cancellation_reason}" if order.cancellation_reason else ""}

Если у вас есть вопросы, обратитесь к администратору.
                """.strip(),

                OrderStatus.REFUNDED: f"""
💰 <b>Возврат по заказу #{order.id} обработан</b>

Возврат средств по вашему заказу успешно обработан.

💵 <b>Сумма возврата:</b> {order.refund_amount or order.total_amount}₽
{f"📝 Причина возврата: {order.refund_reason}" if order.refund_reason else ""}

Средства поступят на ваш счет в течение 3-7 рабочих дней.
                """.strip(),

                OrderStatus.FAILED: f"""
⚠️ <b>Ошибка обработки заказа #{order.id}</b>

К сожалению, при обработке вашего заказа произошла ошибка.

💰 <b>Сумма:</b> {order.formatted_total}

Мы работаем над устранением проблемы. Администратор свяжется с вами в ближайшее время.
                """.strip()
            }

            # Send user notification
            user_message = user_messages.get(order.status, f"Статус заказа #{order.id} изменен на: {order.status_display}")

            await self.send_notification(
                telegram_id=user.telegram_id,
                message=user_message,
                notification_type=notification_type,
                target_type=NotificationTarget.USER,
                order_id=order.id,
                user_id=user.id,
                title=f"Заказ #{order.id}"
            )

            # Schedule feedback request for completed orders
            if order.status == OrderStatus.COMPLETED:
                await self._schedule_feedback_request(order, user)

            return True

        except Exception as e:
            logger.error(f"Error notifying order status change {order.id}: {e}")
            return False

    async def _schedule_feedback_request(self, order: Order, user: User) -> None:
        """Schedule feedback request 1 hour after order completion."""
        try:
            # Check if feedback already exists
            existing_feedback = await self.db.execute(
                select(FeedbackRating).where(FeedbackRating.order_id == order.id)
            )
            if existing_feedback.scalar_one_or_none():
                return  # Feedback already exists

            # Schedule feedback request for 1 hour later
            schedule_time = datetime.utcnow() + timedelta(hours=1)

            feedback_message = f"""
⭐ <b>Оцените заказ #{order.id}</b>

Как вам понравился заказ? Ваше мнение очень важно для нас!

💰 <b>Сумма заказа:</b> {order.formatted_total}
📅 <b>Дата:</b> {order.created_at.strftime('%d.%m.%Y')}

Пожалуйста, поставьте оценку от 1 до 5 звезд:
            """.strip()

            # Create inline keyboard for ratings
            inline_keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "⭐", "callback_data": f"rate_order_{order.id}_1"},
                        {"text": "⭐⭐", "callback_data": f"rate_order_{order.id}_2"},
                        {"text": "⭐⭐⭐", "callback_data": f"rate_order_{order.id}_3"},
                        {"text": "⭐⭐⭐⭐", "callback_data": f"rate_order_{order.id}_4"},
                        {"text": "⭐⭐⭐⭐⭐", "callback_data": f"rate_order_{order.id}_5"}
                    ]
                ]
            }

            await self.send_notification(
                telegram_id=user.telegram_id,
                message=feedback_message,
                notification_type=NotificationType.FEEDBACK_REQUEST,
                target_type=NotificationTarget.USER,
                order_id=order.id,
                user_id=user.id,
                title="Оцените заказ",
                inline_keyboard=inline_keyboard,
                schedule_for=schedule_time
            )

            logger.info(f"Feedback request scheduled for order {order.id}")

        except Exception as e:
            logger.error(f"Error scheduling feedback request for order {order.id}: {e}")

    # Payment notification methods
    async def notify_payment_success(self, order: Order, payment_data: Dict[str, Any]) -> bool:
        """Notify about successful payment."""
        try:
            user_result = await self.db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return False

            message = f"""
💳 <b>Оплата заказа #{order.id} прошла успешно!</b>

✅ Платеж подтвержден
💰 <b>Сумма:</b> {order.formatted_total}
🏷 <b>Статус заказа:</b> {order.status_display}

Мы начинаем готовить ваш заказ!
            """.strip()

            await self.send_notification(
                telegram_id=user.telegram_id,
                message=message,
                notification_type=NotificationType.PAYMENT_SUCCESS,
                target_type=NotificationTarget.USER,
                order_id=order.id,
                user_id=user.id,
                title="Оплата подтверждена",
                metadata=payment_data
            )

            return True

        except Exception as e:
            logger.error(f"Error notifying payment success for order {order.id}: {e}")
            return False

    async def notify_payment_failed(self, order: Order, error_message: str) -> bool:
        """Notify about failed payment."""
        try:
            user_result = await self.db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return False

            message = f"""
❌ <b>Ошибка оплаты заказа #{order.id}</b>

К сожалению, не удалось обработать ваш платеж.

💰 <b>Сумма:</b> {order.formatted_total}
❗ <b>Причина:</b> {error_message}

Попробуйте оплатить заказ еще раз или обратитесь к администратору.
            """.strip()

            await self.send_notification(
                telegram_id=user.telegram_id,
                message=message,
                notification_type=NotificationType.PAYMENT_FAILED,
                target_type=NotificationTarget.USER,
                order_id=order.id,
                user_id=user.id,
                title="Ошибка оплаты",
                metadata={"error": error_message}
            )

            # Notify admin about payment failure
            admin_message = f"""
❌ <b>Ошибка оплаты заказа #{order.id}</b>

👤 <b>Клиент:</b> {order.customer_name}
📞 <b>Телефон:</b> {order.customer_phone}
💰 <b>Сумма:</b> {order.formatted_total}
❗ <b>Ошибка:</b> {error_message}
            """.strip()

            await self.send_notification(
                telegram_id=settings.admin_id,
                message=admin_message,
                notification_type=NotificationType.ADMIN_PAYMENT_FAILED,
                target_type=NotificationTarget.ADMIN,
                order_id=order.id,
                title="Ошибка оплаты",
                metadata={"error": error_message}
            )

            return True

        except Exception as e:
            logger.error(f"Error notifying payment failure for order {order.id}: {e}")
            return False

    # Feedback methods
    async def save_feedback_rating(
        self,
        order_id: int,
        user_id: int,
        rating: int,
        feedback_text: Optional[str] = None,
        notification_id: Optional[int] = None
    ) -> Optional[FeedbackRating]:
        """Save customer feedback rating."""
        try:
            # Check if feedback already exists
            existing = await self.db.execute(
                select(FeedbackRating).where(FeedbackRating.order_id == order_id)
            )
            if existing.scalar_one_or_none():
                logger.warning(f"Feedback already exists for order {order_id}")
                return None

            feedback = FeedbackRating(
                order_id=order_id,
                user_id=user_id,
                rating=rating,
                feedback_text=feedback_text,
                notification_id=notification_id
            )

            self.db.add(feedback)
            await self.db.commit()
            await self.db.refresh(feedback)

            # Send thank you message
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if user:
                thanks_message = f"""
🙏 <b>Спасибо за отзыв!</b>

Ваша оценка заказа #{order_id}: {feedback.rating_emoji}

Мы ценим ваше мнение и постоянно работаем над улучшением качества наших услуг!
                """.strip()

                await self.send_notification(
                    telegram_id=user.telegram_id,
                    message=thanks_message,
                    notification_type=NotificationType.FEEDBACK_REQUEST,
                    target_type=NotificationTarget.USER,
                    order_id=order_id,
                    user_id=user_id,
                    title="Спасибо за отзыв!"
                )

            logger.info(f"Feedback saved for order {order_id}: {rating} stars")
            return feedback

        except Exception as e:
            logger.error(f"Error saving feedback for order {order_id}: {e}")
            await self.db.rollback()
            return None

    # Utility methods
    async def process_scheduled_notifications(self) -> int:
        """Process all scheduled notifications that are due."""
        try:
            # Get notifications that are scheduled and due
            current_time = datetime.utcnow()

            result = await self.db.execute(
                select(Notification).where(
                    and_(
                        Notification.status == NotificationStatus.SCHEDULED,
                        Notification.scheduled_at <= current_time,
                        Notification.is_deleted == False
                    )
                )
            )

            notifications = result.scalars().all()
            sent_count = 0

            for notification in notifications:
                try:
                    success = await self._send_telegram_message(notification)
                    if success:
                        sent_count += 1
                except Exception as e:
                    logger.error(f"Error processing notification {notification.id}: {e}")

            logger.info(f"Processed {sent_count} scheduled notifications")
            return sent_count

        except Exception as e:
            logger.error(f"Error processing scheduled notifications: {e}")
            return 0

    async def retry_failed_notifications(self, max_retries: int = 3) -> int:
        """Retry failed notifications that haven't exceeded max retries."""
        try:
            result = await self.db.execute(
                select(Notification).where(
                    and_(
                        Notification.status == NotificationStatus.FAILED,
                        Notification.retry_count < max_retries,
                        Notification.is_deleted == False
                    )
                )
            )

            notifications = result.scalars().all()
            retried_count = 0

            for notification in notifications:
                try:
                    success = await self._send_telegram_message(notification)
                    if success:
                        retried_count += 1
                except Exception as e:
                    logger.error(f"Error retrying notification {notification.id}: {e}")

            logger.info(f"Retried {retried_count} failed notifications")
            return retried_count

        except Exception as e:
            logger.error(f"Error retrying failed notifications: {e}")
            return 0

    async def get_notification_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get notification statistics for the last N days."""
        try:
            from datetime import datetime, timedelta

            start_date = datetime.utcnow() - timedelta(days=days)

            # Total notifications
            total_result = await self.db.execute(
                select(Notification).where(
                    and_(
                        Notification.created_at >= start_date,
                        Notification.is_deleted == False
                    )
                )
            )
            total_notifications = len(total_result.scalars().all())

            # Sent notifications
            sent_result = await self.db.execute(
                select(Notification).where(
                    and_(
                        Notification.created_at >= start_date,
                        Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED]),
                        Notification.is_deleted == False
                    )
                )
            )
            sent_notifications = len(sent_result.scalars().all())

            # Failed notifications
            failed_result = await self.db.execute(
                select(Notification).where(
                    and_(
                        Notification.created_at >= start_date,
                        Notification.status == NotificationStatus.FAILED,
                        Notification.is_deleted == False
                    )
                )
            )
            failed_notifications = len(failed_result.scalars().all())

            success_rate = (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0

            return {
                "period_days": days,
                "total_notifications": total_notifications,
                "sent_notifications": sent_notifications,
                "failed_notifications": failed_notifications,
                "success_rate": round(success_rate, 2)
            }

        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {}

    # Legacy compatibility methods (kept for backward compatibility)
    @staticmethod
    async def send_admin_notification(message: str) -> bool:
        """Legacy method - send notification to admin."""
        try:
            await bot.send_message(
                chat_id=settings.admin_id,
                text=message,
                parse_mode="HTML"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")
            return False

    @staticmethod
    async def send_user_notification(telegram_id: int, message: str) -> bool:
        """Legacy method - send notification to user."""
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML"
            )
            return True
        except Exception as e:
            logger.error(f"Error sending user notification to {telegram_id}: {e}")
            return False

    # Compatibility wrapper for new methods (will be removed in future versions)
    @staticmethod
    async def send_notification(telegram_id: int, message: str) -> bool:
        """Legacy compatibility method."""
        return await NotificationService.send_user_notification(telegram_id, message)