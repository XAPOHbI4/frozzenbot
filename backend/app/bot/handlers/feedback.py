"""Feedback handlers for Telegram bot."""

import logging
from typing import Optional
from aiogram import types
from aiogram.dispatcher import FSMContext

from app.database import async_session_maker
from app.models.user import User
from app.models.order import Order
from app.models.notification import FeedbackRating
from app.services.notification import NotificationService
from app.bot.bot import dp, bot
from sqlalchemy import select

logger = logging.getLogger(__name__)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('rate_order_'))
async def handle_order_rating(callback_query: types.CallbackQuery):
    """Handle order rating callback."""
    try:
        # Parse callback data: rate_order_{order_id}_{rating}
        parts = callback_query.data.split('_')
        if len(parts) != 4:
            await callback_query.answer("Неверный формат данных")
            return

        order_id = int(parts[2])
        rating = int(parts[3])

        if not (1 <= rating <= 5):
            await callback_query.answer("Неверная оценка")
            return

        user_telegram_id = callback_query.from_user.id

        async with async_session_maker() as db:
            # Get user
            user_result = await db.execute(
                select(User).where(User.telegram_id == user_telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                await callback_query.answer("Пользователь не найден")
                return

            # Get order and verify it belongs to user
            order_result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = order_result.scalar_one_or_none()

            if not order:
                await callback_query.answer("Заказ не найден")
                return

            if order.user_id != user.id:
                await callback_query.answer("Этот заказ не принадлежит вам")
                return

            # Check if feedback already exists
            existing_feedback = await db.execute(
                select(FeedbackRating).where(FeedbackRating.order_id == order_id)
            )
            if existing_feedback.scalar_one_or_none():
                await callback_query.answer("Вы уже оценили этот заказ")
                return

            # Save feedback
            notification_service = NotificationService(db)
            feedback = await notification_service.save_feedback_rating(
                order_id=order_id,
                user_id=user.id,
                rating=rating
            )

            if feedback:
                # Update message to show rating was saved
                rating_emoji = feedback.rating_emoji
                new_text = f"""
✅ <b>Спасибо за оценку заказа #{order_id}!</b>

Ваша оценка: {rating_emoji}

Мы ценим ваше мнение и используем его для улучшения качества нашего сервиса!

Если у вас есть дополнительные комментарии, напишите их в следующем сообщении.
                """.strip()

                # Create inline keyboard for additional feedback
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton(
                        "💬 Оставить комментарий",
                        callback_data=f"feedback_comment_{order_id}"
                    )
                )
                keyboard.add(
                    types.InlineKeyboardButton(
                        "✅ Готово",
                        callback_data=f"feedback_done_{order_id}"
                    )
                )

                await bot.edit_message_text(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                    text=new_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

                await callback_query.answer(f"Оценка {rating_emoji} сохранена!")

            else:
                await callback_query.answer("Ошибка при сохранении оценки")

    except ValueError:
        await callback_query.answer("Неверный формат данных")
        logger.error(f"Invalid callback data format: {callback_query.data}")
    except Exception as e:
        await callback_query.answer("Произошла ошибка")
        logger.error(f"Error handling order rating: {e}")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('feedback_comment_'))
async def handle_feedback_comment_request(callback_query: types.CallbackQuery, state: FSMContext):
    """Handle request for additional feedback comment."""
    try:
        # Parse callback data: feedback_comment_{order_id}
        parts = callback_query.data.split('_')
        if len(parts) != 3:
            await callback_query.answer("Неверный формат данных")
            return

        order_id = int(parts[2])

        # Store order_id in state for next message
        await state.update_data(pending_feedback_order_id=order_id)

        await callback_query.message.reply(
            "💬 <b>Пожалуйста, напишите ваш комментарий о заказе:</b>\n\n"
            "Расскажите, что вам понравилось или что можно улучшить. "
            "Ваш отзыв поможет нам стать лучше!",
            parse_mode="HTML"
        )

        await callback_query.answer("Ожидаем ваш комментарий")

    except ValueError:
        await callback_query.answer("Неверный формат данных")
        logger.error(f"Invalid callback data format: {callback_query.data}")
    except Exception as e:
        await callback_query.answer("Произошла ошибка")
        logger.error(f"Error handling feedback comment request: {e}")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('feedback_done_'))
async def handle_feedback_done(callback_query: types.CallbackQuery):
    """Handle feedback completion."""
    try:
        # Parse callback data: feedback_done_{order_id}
        parts = callback_query.data.split('_')
        if len(parts) != 3:
            await callback_query.answer("Неверный формат данных")
            return

        order_id = int(parts[2])

        # Update message to show completion
        new_text = f"""
🙏 <b>Спасибо за ваш отзыв о заказе #{order_id}!</b>

Ваше мнение очень важно для нас. Мы постоянно работаем над улучшением качества наших услуг.

Будем рады видеть вас снова! 😊
        """.strip()

        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=new_text,
            parse_mode="HTML"
        )

        await callback_query.answer("Спасибо за отзыв!")

    except ValueError:
        await callback_query.answer("Неверный формат данных")
        logger.error(f"Invalid callback data format: {callback_query.data}")
    except Exception as e:
        await callback_query.answer("Произошла ошибка")
        logger.error(f"Error handling feedback done: {e}")


@dp.message_handler(state='*', content_types=types.ContentTypes.TEXT)
async def handle_feedback_text(message: types.Message, state: FSMContext):
    """Handle text messages that might be feedback comments."""
    try:
        # Check if user has pending feedback
        data = await state.get_data()
        pending_order_id = data.get('pending_feedback_order_id')

        if not pending_order_id:
            # This is not a feedback message, let other handlers process it
            return

        # Clear pending feedback from state
        await state.update_data(pending_feedback_order_id=None)

        user_telegram_id = message.from_user.id
        feedback_text = message.text

        if not feedback_text or len(feedback_text.strip()) == 0:
            await message.reply("Комментарий не может быть пустым. Попробуйте еще раз.")
            return

        if len(feedback_text) > 1000:
            await message.reply("Комментарий слишком длинный. Максимум 1000 символов.")
            return

        async with async_session_maker() as db:
            # Get user
            user_result = await db.execute(
                select(User).where(User.telegram_id == user_telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                await message.reply("Пользователь не найден")
                return

            # Get existing feedback
            feedback_result = await db.execute(
                select(FeedbackRating).where(
                    FeedbackRating.order_id == pending_order_id,
                    FeedbackRating.user_id == user.id
                )
            )
            feedback = feedback_result.scalar_one_or_none()

            if not feedback:
                await message.reply("Оценка не найдена. Сначала поставьте оценку заказу.")
                return

            # Update feedback with text
            feedback.feedback_text = feedback_text.strip()
            await db.commit()

            # Send confirmation
            await message.reply(
                f"✅ <b>Ваш комментарий сохранен!</b>\n\n"
                f"📝 <i>{feedback_text}</i>\n\n"
                f"Спасибо за развернутый отзыв о заказе #{pending_order_id}!",
                parse_mode="HTML"
            )

            # Notify admin about new detailed feedback
            from app.config import settings
            admin_message = f"""
💬 <b>Новый развернутый отзыв</b>

📦 <b>Заказ:</b> #{pending_order_id}
👤 <b>Клиент:</b> {user.full_name}
⭐ <b>Оценка:</b> {feedback.rating_emoji}

📝 <b>Комментарий:</b>
<i>{feedback_text}</i>
            """.strip()

            notification_service = NotificationService(db)
            await notification_service.send_admin_notification(admin_message)

    except Exception as e:
        await message.reply("Произошла ошибка при сохранении комментария")
        logger.error(f"Error handling feedback text: {e}")


# Additional handlers for feedback management

@dp.message_handler(commands=['my_feedback'])
async def show_user_feedback(message: types.Message):
    """Show user's feedback history."""
    try:
        user_telegram_id = message.from_user.id

        async with async_session_maker() as db:
            # Get user
            user_result = await db.execute(
                select(User).where(User.telegram_id == user_telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                await message.reply("Пользователь не найден")
                return

            # Get user's feedback with order details
            feedback_result = await db.execute(
                select(FeedbackRating, Order)
                .join(Order, FeedbackRating.order_id == Order.id)
                .where(FeedbackRating.user_id == user.id)
                .order_by(FeedbackRating.created_at.desc())
            )
            feedback_list = feedback_result.all()

            if not feedback_list:
                await message.reply(
                    "📝 У вас пока нет отзывов.\n\n"
                    "После выполнения заказов мы попросим вас оценить наш сервис!"
                )
                return

            text = "📝 <b>Ваши отзывы:</b>\n\n"

            for feedback, order in feedback_list:
                text += f"📦 <b>Заказ #{order.id}</b>\n"
                text += f"⭐ <b>Оценка:</b> {feedback.rating_emoji}\n"
                text += f"📅 <b>Дата:</b> {feedback.created_at.strftime('%d.%m.%Y')}\n"

                if feedback.feedback_text:
                    text += f"💬 <b>Комментарий:</b> <i>{feedback.feedback_text}</i>\n"

                text += "\n"

            await message.reply(text, parse_mode="HTML")

    except Exception as e:
        await message.reply("Произошла ошибка при получении отзывов")
        logger.error(f"Error showing user feedback: {e}")


@dp.message_handler(commands=['feedback_stats'], user_id=lambda message: message.from_user.id == int(settings.admin_id))
async def show_feedback_stats(message: types.Message):
    """Show feedback statistics (admin only)."""
    try:
        async with async_session_maker() as db:
            from datetime import datetime, timedelta
            from sqlalchemy import func

            # Get stats for last 30 days
            start_date = datetime.utcnow() - timedelta(days=30)

            # Total feedback count
            total_result = await db.execute(
                select(func.count(FeedbackRating.id))
                .where(FeedbackRating.created_at >= start_date)
            )
            total_feedback = total_result.scalar() or 0

            # Average rating
            avg_result = await db.execute(
                select(func.avg(FeedbackRating.rating))
                .where(FeedbackRating.created_at >= start_date)
            )
            avg_rating = avg_result.scalar() or 0

            # Rating distribution
            rating_dist_result = await db.execute(
                select(
                    FeedbackRating.rating,
                    func.count(FeedbackRating.id).label('count')
                )
                .where(FeedbackRating.created_at >= start_date)
                .group_by(FeedbackRating.rating)
            )

            rating_distribution = {}
            for row in rating_dist_result:
                rating_distribution[row.rating] = row.count

            # Build message
            text = f"""
📊 <b>Статистика отзывов за 30 дней</b>

📝 <b>Всего отзывов:</b> {total_feedback}
⭐ <b>Средняя оценка:</b> {avg_rating:.1f}

📈 <b>Распределение оценок:</b>
            """.strip()

            for rating in range(5, 0, -1):
                count = rating_distribution.get(rating, 0)
                percentage = (count / total_feedback * 100) if total_feedback > 0 else 0
                stars = "⭐" * rating
                text += f"\n{stars} {count} ({percentage:.1f}%)"

            await message.reply(text, parse_mode="HTML")

    except Exception as e:
        await message.reply("Произошла ошибка при получении статистики")
        logger.error(f"Error showing feedback stats: {e}")


# Helper function for external use
async def send_feedback_request(order_id: int, user_telegram_id: int):
    """Send feedback request for an order."""
    try:
        feedback_message = f"""
⭐ <b>Оцените заказ #{order_id}</b>

Как вам понравился заказ? Ваше мнение очень важно для нас!

Пожалуйста, поставьте оценку от 1 до 5 звезд:
        """.strip()

        # Create inline keyboard for ratings
        keyboard = types.InlineKeyboardMarkup()
        rating_buttons = []
        for rating in range(1, 6):
            stars = "⭐" * rating
            rating_buttons.append(
                types.InlineKeyboardButton(
                    text=stars,
                    callback_data=f"rate_order_{order_id}_{rating}"
                )
            )

        keyboard.row(*rating_buttons)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=feedback_message,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        logger.info(f"Feedback request sent for order {order_id} to user {user_telegram_id}")

    except Exception as e:
        logger.error(f"Error sending feedback request for order {order_id}: {e}")