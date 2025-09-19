"""Tests for feedback handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message, User as TelegramUser, Chat

from app.bot.handlers.feedback import (
    handle_order_rating,
    handle_feedback_comment_request,
    handle_feedback_done,
    handle_feedback_text
)
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.notification import FeedbackRating


@pytest.fixture
def mock_callback_query():
    """Mock callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "rate_order_1_5"
    callback.from_user = TelegramUser(
        id=123456789,
        is_bot=False,
        first_name="Test",
        username="testuser"
    )
    callback.message = MagicMock(spec=Message)
    callback.message.chat = Chat(id=123456789, type="private")
    callback.message.message_id = 100
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_message():
    """Mock message."""
    message = MagicMock(spec=Message)
    message.from_user = TelegramUser(
        id=123456789,
        is_bot=False,
        first_name="Test",
        username="testuser"
    )
    message.text = "Great service! Very satisfied with the order."
    message.reply = AsyncMock()
    return message


@pytest.fixture
def mock_user():
    """Mock user."""
    return User(
        id=1,
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def mock_order():
    """Mock order."""
    return Order(
        id=1,
        user_id=1,
        status=OrderStatus.COMPLETED,
        total_amount=1500.0,
        customer_name="Test User",
        customer_phone="+1234567890"
    )


class TestFeedbackHandlers:
    """Test feedback bot handlers."""

    @pytest.mark.asyncio
    async def test_handle_order_rating_success(self, mock_callback_query, mock_user, mock_order):
        """Test successful order rating handling."""
        with patch('app.bot.handlers.feedback.async_session_maker') as mock_session_maker:
            # Mock database session
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Mock user query
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user

            # Mock order query
            mock_order_result = MagicMock()
            mock_order_result.scalar_one_or_none.return_value = mock_order

            # Mock existing feedback query (no existing feedback)
            mock_feedback_result = MagicMock()
            mock_feedback_result.scalar_one_or_none.return_value = None

            mock_db.execute.side_effect = [
                mock_user_result,
                mock_order_result,
                mock_feedback_result
            ]

            # Mock NotificationService
            with patch('app.bot.handlers.feedback.NotificationService') as mock_notification_service:
                mock_service_instance = AsyncMock()
                mock_notification_service.return_value = mock_service_instance

                mock_feedback = MagicMock()
                mock_feedback.rating_emoji = "⭐⭐⭐⭐⭐"
                mock_service_instance.save_feedback_rating.return_value = mock_feedback

                # Mock bot edit message
                with patch('app.bot.handlers.feedback.bot') as mock_bot:
                    mock_bot.edit_message_text = AsyncMock()

                    await handle_order_rating(mock_callback_query)

                    # Assertions
                    mock_service_instance.save_feedback_rating.assert_called_once_with(
                        order_id=1,
                        user_id=1,
                        rating=5
                    )
                    mock_bot.edit_message_text.assert_called_once()
                    mock_callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_order_rating_invalid_format(self, mock_callback_query):
        """Test handling invalid callback data format."""
        mock_callback_query.data = "invalid_format"

        await handle_order_rating(mock_callback_query)

        mock_callback_query.answer.assert_called_once_with("Неверный формат данных")

    @pytest.mark.asyncio
    async def test_handle_order_rating_invalid_rating(self, mock_callback_query):
        """Test handling invalid rating value."""
        mock_callback_query.data = "rate_order_1_10"  # Invalid rating

        await handle_order_rating(mock_callback_query)

        mock_callback_query.answer.assert_called_once_with("Неверная оценка")

    @pytest.mark.asyncio
    async def test_handle_order_rating_user_not_found(self, mock_callback_query):
        """Test handling when user is not found."""
        with patch('app.bot.handlers.feedback.async_session_maker') as mock_session_maker:
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Mock user not found
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_user_result

            await handle_order_rating(mock_callback_query)

            mock_callback_query.answer.assert_called_once_with("Пользователь не найден")

    @pytest.mark.asyncio
    async def test_handle_order_rating_already_exists(self, mock_callback_query, mock_user, mock_order):
        """Test handling when feedback already exists."""
        with patch('app.bot.handlers.feedback.async_session_maker') as mock_session_maker:
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Mock user and order found
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user

            mock_order_result = MagicMock()
            mock_order_result.scalar_one_or_none.return_value = mock_order

            # Mock existing feedback
            mock_feedback_result = MagicMock()
            mock_feedback_result.scalar_one_or_none.return_value = MagicMock()  # Existing feedback

            mock_db.execute.side_effect = [
                mock_user_result,
                mock_order_result,
                mock_feedback_result
            ]

            await handle_order_rating(mock_callback_query)

            mock_callback_query.answer.assert_called_once_with("Вы уже оценили этот заказ")

    @pytest.mark.asyncio
    async def test_handle_feedback_comment_request(self, mock_callback_query):
        """Test feedback comment request handling."""
        mock_callback_query.data = "feedback_comment_1"
        mock_state = AsyncMock()

        await handle_feedback_comment_request(mock_callback_query, mock_state)

        mock_state.update_data.assert_called_once_with(pending_feedback_order_id=1)
        mock_callback_query.message.reply.assert_called_once()
        mock_callback_query.answer.assert_called_once_with("Ожидаем ваш комментарий")

    @pytest.mark.asyncio
    async def test_handle_feedback_done(self, mock_callback_query):
        """Test feedback completion handling."""
        mock_callback_query.data = "feedback_done_1"

        with patch('app.bot.handlers.feedback.bot') as mock_bot:
            mock_bot.edit_message_text = AsyncMock()

            await handle_feedback_done(mock_callback_query)

            mock_bot.edit_message_text.assert_called_once()
            mock_callback_query.answer.assert_called_once_with("Спасибо за отзыв!")

    @pytest.mark.asyncio
    async def test_handle_feedback_text_success(self, mock_message, mock_user):
        """Test successful feedback text handling."""
        mock_state = AsyncMock()
        mock_state.get_data.return_value = {"pending_feedback_order_id": 1}

        with patch('app.bot.handlers.feedback.async_session_maker') as mock_session_maker:
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Mock user query
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user

            # Mock existing feedback
            mock_feedback = MagicMock()
            mock_feedback_result = MagicMock()
            mock_feedback_result.scalar_one_or_none.return_value = mock_feedback

            mock_db.execute.side_effect = [mock_user_result, mock_feedback_result]

            # Mock NotificationService
            with patch('app.bot.handlers.feedback.NotificationService') as mock_notification_service:
                mock_service_instance = AsyncMock()
                mock_notification_service.return_value = mock_service_instance

                await handle_feedback_text(mock_message, mock_state)

                # Assertions
                mock_state.update_data.assert_called_once_with(pending_feedback_order_id=None)
                mock_message.reply.assert_called_once()
                assert mock_feedback.feedback_text == "Great service! Very satisfied with the order."
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_feedback_text_no_pending(self, mock_message):
        """Test feedback text handling when no pending feedback."""
        mock_state = AsyncMock()
        mock_state.get_data.return_value = {}  # No pending feedback

        # Should return early without processing
        await handle_feedback_text(mock_message, mock_state)

        mock_message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_feedback_text_empty(self, mock_message):
        """Test feedback text handling with empty text."""
        mock_message.text = ""
        mock_state = AsyncMock()
        mock_state.get_data.return_value = {"pending_feedback_order_id": 1}

        await handle_feedback_text(mock_message, mock_state)

        mock_message.reply.assert_called_once_with("Комментарий не может быть пустым. Попробуйте еще раз.")

    @pytest.mark.asyncio
    async def test_handle_feedback_text_too_long(self, mock_message):
        """Test feedback text handling with too long text."""
        mock_message.text = "x" * 1001  # Too long
        mock_state = AsyncMock()
        mock_state.get_data.return_value = {"pending_feedback_order_id": 1}

        await handle_feedback_text(mock_message, mock_state)

        mock_message.reply.assert_called_once_with("Комментарий слишком длинный. Максимум 1000 символов.")


class TestFeedbackUtilityFunctions:
    """Test feedback utility functions."""

    @pytest.mark.asyncio
    async def test_send_feedback_request(self):
        """Test send_feedback_request utility function."""
        from app.bot.handlers.feedback import send_feedback_request

        with patch('app.bot.handlers.feedback.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            await send_feedback_request(order_id=1, user_telegram_id=123456789)

            mock_bot.send_message.assert_called_once()
            call_args = mock_bot.send_message.call_args
            assert call_args.kwargs['chat_id'] == 123456789
            assert 'reply_markup' in call_args.kwargs
            assert "Оцените заказ #1" in call_args.kwargs['text']


class TestFeedbackCommands:
    """Test feedback command handlers."""

    @pytest.mark.asyncio
    async def test_show_user_feedback_no_feedback(self, mock_message, mock_user):
        """Test showing user feedback when no feedback exists."""
        from app.bot.handlers.feedback import show_user_feedback

        with patch('app.bot.handlers.feedback.async_session_maker') as mock_session_maker:
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Mock user found
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user

            # Mock no feedback
            mock_feedback_result = MagicMock()
            mock_feedback_result.all.return_value = []

            mock_db.execute.side_effect = [mock_user_result, mock_feedback_result]

            await show_user_feedback(mock_message)

            mock_message.reply.assert_called_once()
            assert "У вас пока нет отзывов" in mock_message.reply.call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_user_feedback_with_feedback(self, mock_message, mock_user, mock_order):
        """Test showing user feedback when feedback exists."""
        from app.bot.handlers.feedback import show_user_feedback

        with patch('app.bot.handlers.feedback.async_session_maker') as mock_session_maker:
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Mock user found
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user

            # Mock feedback with order
            mock_feedback = MagicMock()
            mock_feedback.rating_emoji = "⭐⭐⭐⭐⭐"
            mock_feedback.feedback_text = "Great service!"
            mock_feedback.created_at.strftime.return_value = "01.01.2024"

            mock_feedback_result = MagicMock()
            mock_feedback_result.all.return_value = [(mock_feedback, mock_order)]

            mock_db.execute.side_effect = [mock_user_result, mock_feedback_result]

            await show_user_feedback(mock_message)

            mock_message.reply.assert_called_once()
            reply_text = mock_message.reply.call_args[0][0]
            assert "Ваши отзывы:" in reply_text
            assert "⭐⭐⭐⭐⭐" in reply_text
            assert "Great service!" in reply_text


if __name__ == "__main__":
    pytest.main([__file__])