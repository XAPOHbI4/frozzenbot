"""Order management handlers for Telegram bot."""

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.order import OrderService
from app.services.notification import NotificationService

router = Router()


@router.callback_query(F.data.startswith("cancel_order:"))
async def handle_cancel_order(callback: types.CallbackQuery):
    """Handle order cancellation from notification message."""
    try:
        # Extract order ID from callback data
        order_id = int(callback.data.split(":")[1])
        user_telegram_id = callback.from_user.id

        # Get database session
        async for session in get_async_session():
            order_service = OrderService(session)

            # Get order and validate ownership
            order = await order_service.get_order_by_id(order_id)
            if not order:
                await callback.answer("❌ Заказ не найден", show_alert=True)
                return

            # Get user to validate ownership
            from sqlalchemy import select
            user_result = await session.execute(
                select(User).where(User.telegram_id == user_telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user or order.user_id != user.id:
                await callback.answer("❌ Это не ваш заказ", show_alert=True)
                return

            # Check if order can be cancelled
            if not order.can_be_cancelled:
                await callback.answer(
                    f"❌ Заказ в статусе '{order.status_display}' нельзя отменить",
                    show_alert=True
                )
                return

            # Cancel the order
            success = await order_service.cancel_order(
                order_id=order_id,
                reason="Отменен пользователем через бот",
                cancelled_by_user_id=user.id
            )

            if success:
                # Update the message to show cancellation
                cancel_text = f"""
❌ <b>Заказ #{order_id} отменен</b>

Ваш заказ был успешно отменен.
Если была произведена оплата, средства будут возвращены в течение 3-5 рабочих дней.

Спасибо за использование нашего сервиса! 🙏
                """

                # Remove the cancel button
                await callback.message.edit_text(
                    cancel_text,
                    reply_markup=None
                )

                await callback.answer("✅ Заказ отменен", show_alert=True)

                # Send admin notification about cancellation
                admin_text = f"""
🚫 <b>Заказ отменен пользователем</b>

📦 <b>Заказ:</b> #{order_id}
👤 <b>Клиент:</b> {order.customer_name}
📞 <b>Телефон:</b> {order.customer_phone}
💰 <b>Сумма:</b> {order.formatted_total}
⏰ <b>Время отмены:</b> {order.updated_at.strftime('%d.%m.%Y %H:%M')}

🔍 <b>Причина:</b> Отменен пользователем через бот
                """

                await NotificationService.send_admin_notification(admin_text)
            else:
                await callback.answer("❌ Ошибка при отмене заказа", show_alert=True)

            break

    except Exception as e:
        await callback.answer("❌ Ошибка при обработке запроса", show_alert=True)
        print(f"Error cancelling order: {e}")


async def send_order_notification(
    telegram_id: int,
    order: Order,
    message_type: str = "created"
):
    """Send order notification to user with cancel button if applicable."""

    # Format order details
    if message_type == "created":
        notification_text = f"""
✅ <b>Спасибо за заказ!</b>

Ваш заказ на сумму <b>{order.formatted_total}</b>:
"""
        # Add order items
        if order.items:
            for item in order.items:
                notification_text += f"• {item.product.name} - {item.quantity} шт.\n"

        notification_text += f"""

<b>Сумма к оплате:</b> {order.formatted_total}

Для оплаты сделайте перевод:
<code>5536 9141 2359 8116</code> (скопируется нажатием)

• <b>Комментарий к платежу:</b> {order.id}

• Можно перевести более крупную сумму для оплаты наличных.
Статус: ожидание оплаты ⏳

<b>Отменить</b>
        """

        # Add cancel button if order can be cancelled
        if order.can_be_cancelled:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="❌ Отменить заказ",
                            callback_data=f"cancel_order:{order.id}"
                        )
                    ]
                ]
            )
        else:
            keyboard = None

    elif message_type == "payment_success":
        notification_text = f"""
✅ <b>Оплата прошла успешно!</b>

Заказ #{order.id} оплачен и будет доставлен в указанное время.

<b>Доставка:</b> 10-15 мин

Заказ был успешно доставлен.
Благодарим вас за покупку! 🎉
        """
        keyboard = None

    elif message_type == "completed":
        notification_text = f"""
🎉 <b>Заказ доставлен!</b>

Заказ #{order.id} был успешно доставлен.

Оцените качество нашего сервиса:
        """

        # Add feedback buttons
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⭐", callback_data=f"feedback:{order.id}:1"),
                    InlineKeyboardButton(text="⭐⭐", callback_data=f"feedback:{order.id}:2"),
                    InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"feedback:{order.id}:3"),
                    InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"feedback:{order.id}:4"),
                    InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"feedback:{order.id}:5"),
                ]
            ]
        )

    # Send notification
    try:
        await NotificationService.send_notification(
            telegram_id,
            notification_text,
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Failed to send order notification: {e}")


@router.callback_query(F.data == "my_orders")
async def handle_my_orders(callback: types.CallbackQuery):
    """Show user's recent orders."""
    user_telegram_id = callback.from_user.id

    async for session in get_async_session():
        # Get user
        from sqlalchemy import select
        user_result = await session.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        # Get recent orders
        order_service = OrderService(session)
        orders = await order_service.get_user_orders(user.id, limit=5)

        if not orders:
            orders_text = """
📋 <b>Мои заказы</b>

У вас пока нет заказов.
Используйте кнопку "Каталог" для оформления первого заказа! 🛒
            """
        else:
            orders_text = "📋 <b>Мои последние заказы</b>\n\n"

            for order in orders:
                status_emoji = {
                    OrderStatus.PENDING: "⏳",
                    OrderStatus.CONFIRMED: "✅",
                    OrderStatus.PREPARING: "👨‍🍳",
                    OrderStatus.READY: "🎯",
                    OrderStatus.COMPLETED: "🎉",
                    OrderStatus.CANCELLED: "❌"
                }.get(order.status, "❓")

                orders_text += f"""
<b>Заказ #{order.id}</b> {status_emoji}
💰 Сумма: {order.formatted_total}
📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}
📊 Статус: {order.status_display}

"""

        await callback.message.edit_text(orders_text)
        await callback.answer()
        break