"""Comprehensive tests for the notification system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification, NotificationTemplate, FeedbackRating,
    NotificationType, NotificationStatus, NotificationTarget
)
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.services.notification import NotificationService
from app.utils.scheduler import NotificationScheduler


@pytest.fixture
async def mock_db():
    """Mock database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.refresh = AsyncMock()
    return mock_session


@pytest.fixture
def mock_user():
    """Mock user."""
    user = User(
        id=1,
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    return user


@pytest.fixture
def mock_order():
    """Mock order."""
    order = Order(
        id=1,
        user_id=1,
        status=OrderStatus.PENDING,
        total_amount=1500.0,
        customer_name="Test User",
        customer_phone="+1234567890",
        delivery_address="Test Address",
        notes="Test notes",
        payment_method="card"
    )
    order.created_at = datetime.utcnow()
    return order


class TestNotificationService:
    """Test NotificationService functionality."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, mock_db, mock_user):
        """Test successful notification sending."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            # Mock database operations
            mock_notification = Notification(
                id=1,
                target_type=NotificationTarget.USER,
                target_telegram_id=mock_user.telegram_id,
                notification_type=NotificationType.ORDER_CREATED,
                message="Test message",
                status=NotificationStatus.PENDING
            )

            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            # Call method
            result = await notification_service.send_notification(
                telegram_id=mock_user.telegram_id,
                message="Test message",
                notification_type=NotificationType.ORDER_CREATED,
                title="Test Title"
            )

            # Assertions
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()
            mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_with_inline_keyboard(self, mock_db, mock_user):
        """Test notification sending with inline keyboard."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            inline_keyboard = {
                "inline_keyboard": [
                    [{"text": "⭐⭐⭐⭐⭐", "callback_data": "rate_5"}]
                ]
            }

            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            await notification_service.send_notification(
                telegram_id=mock_user.telegram_id,
                message="Rate this order",
                notification_type=NotificationType.FEEDBACK_REQUEST,
                inline_keyboard=inline_keyboard
            )

            # Check that inline keyboard was processed
            call_args = mock_bot.send_message.call_args
            assert 'reply_markup' in call_args.kwargs

    @pytest.mark.asyncio
    async def test_notify_order_created(self, mock_db, mock_order, mock_user):
        """Test order created notification."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            # Mock database queries
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_user_result

            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            # Mock admin notification
            with patch.object(notification_service, '_notify_admin_new_order', new_callable=AsyncMock) as mock_admin_notify:
                result = await notification_service.notify_order_created(mock_order)

                assert result is True
                mock_admin_notify.assert_called_once()
                assert mock_bot.send_message.call_count >= 1

    @pytest.mark.asyncio
    async def test_notify_order_status_change(self, mock_db, mock_order, mock_user):
        """Test order status change notification."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            # Mock database queries
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_user_result

            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            # Change order status to completed
            mock_order.status = OrderStatus.COMPLETED
            old_status = OrderStatus.READY

            with patch.object(notification_service, '_schedule_feedback_request', new_callable=AsyncMock) as mock_schedule_feedback:
                result = await notification_service.notify_order_status_change(mock_order, old_status)

                assert result is True
                # Should schedule feedback for completed orders
                mock_schedule_feedback.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_feedback_rating(self, mock_db, mock_user):
        """Test saving feedback rating."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            # Mock no existing feedback
            mock_existing_result = MagicMock()
            mock_existing_result.scalar_one_or_none.return_value = None

            # Mock user query
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user

            mock_db.execute.side_effect = [mock_existing_result, mock_user_result]
            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            result = await notification_service.save_feedback_rating(
                order_id=1,
                user_id=mock_user.id,
                rating=5,
                feedback_text="Great service!"
            )

            # Should return a feedback object (mocked)
            assert result is not None or mock_db.add.called

    @pytest.mark.asyncio
    async def test_process_scheduled_notifications(self, mock_db):
        """Test processing scheduled notifications."""
        notification_service = NotificationService(mock_db)

        # Mock scheduled notifications
        mock_notification = Notification(
            id=1,
            target_telegram_id=123456789,
            notification_type=NotificationType.FEEDBACK_REQUEST,
            message="Test scheduled message",
            status=NotificationStatus.SCHEDULED,
            scheduled_at=datetime.utcnow() - timedelta(minutes=5)
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_notification]
        mock_db.execute.return_value = mock_result

        with patch.object(notification_service, '_send_telegram_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            sent_count = await notification_service.process_scheduled_notifications()

            assert sent_count == 1
            mock_send.assert_called_once_with(mock_notification)

    @pytest.mark.asyncio
    async def test_notification_retry_logic(self, mock_db):
        """Test notification retry functionality."""
        notification_service = NotificationService(mock_db)

        # Mock failed notifications
        mock_notification = Notification(
            id=1,
            target_telegram_id=123456789,
            notification_type=NotificationType.ORDER_CREATED,
            message="Test message",
            status=NotificationStatus.FAILED,
            retry_count=1
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_notification]
        mock_db.execute.return_value = mock_result

        with patch.object(notification_service, '_send_telegram_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            retried_count = await notification_service.retry_failed_notifications()

            assert retried_count == 1
            mock_send.assert_called_once_with(mock_notification)

    @pytest.mark.asyncio
    async def test_get_notification_stats(self, mock_db):
        """Test getting notification statistics."""
        notification_service = NotificationService(mock_db)

        # Mock statistics queries
        mock_results = [
            MagicMock(),  # Total notifications
            MagicMock(),  # Sent notifications
            MagicMock(),  # Failed notifications
        ]

        # Mock scalar returns
        mock_results[0].scalars.return_value.all.return_value = [1, 2, 3]  # 3 total
        mock_results[1].scalars.return_value.all.return_value = [1, 2]     # 2 sent
        mock_results[2].scalars.return_value.all.return_value = [3]        # 1 failed

        mock_db.execute.side_effect = mock_results

        stats = await notification_service.get_notification_stats(days=7)

        # Should return statistical data
        assert isinstance(stats, dict)
        assert 'period_days' in stats


class TestNotificationScheduler:
    """Test NotificationScheduler functionality."""

    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance."""
        return NotificationScheduler()

    @pytest.mark.asyncio
    async def test_schedule_task(self, scheduler):
        """Test task scheduling."""
        execute_at = datetime.utcnow() + timedelta(minutes=30)

        await scheduler.schedule_task(
            task_id="test_task_1",
            execute_at=execute_at,
            task_type="send_notification",
            payload={"message": "Test"}
        )

        assert "test_task_1" in scheduler.tasks
        assert scheduler.tasks["test_task_1"].execute_at == execute_at

    @pytest.mark.asyncio
    async def test_schedule_notification(self, scheduler):
        """Test notification scheduling."""
        await scheduler.schedule_notification(
            telegram_id=123456789,
            message="Test scheduled notification",
            notification_type="order_created",
            delay_minutes=60
        )

        # Should have a scheduled task
        assert len(scheduler.tasks) == 1

    @pytest.mark.asyncio
    async def test_schedule_feedback_request(self, scheduler):
        """Test feedback request scheduling."""
        await scheduler.schedule_feedback_request(
            order_id=1,
            user_id=1,
            telegram_id=123456789,
            delay_hours=1
        )

        # Should have a scheduled feedback task
        assert len(scheduler.tasks) == 1
        task = list(scheduler.tasks.values())[0]
        assert task.task_type == "process_feedback_request"

    def test_cancel_task(self, scheduler):
        """Test task cancellation."""
        # Add a task first
        scheduler.tasks["test_cancel"] = MagicMock()

        scheduler.cancel_task("test_cancel")

        assert "test_cancel" not in scheduler.tasks

    @pytest.mark.asyncio
    async def test_task_execution(self, scheduler):
        """Test task execution."""
        # Mock task handler
        mock_handler = AsyncMock()
        scheduler.task_handlers["test_handler"] = mock_handler

        # Create a task
        from app.utils.scheduler import ScheduledTask
        task = ScheduledTask(
            task_id="test_exec",
            execute_at=datetime.utcnow(),
            task_type="test_handler",
            payload={"test": "data"}
        )

        await scheduler._execute_task(task)

        mock_handler.assert_called_once_with({"test": "data"})

    @pytest.mark.asyncio
    async def test_process_due_tasks(self, scheduler):
        """Test processing of due tasks."""
        # Add a due task
        from app.utils.scheduler import ScheduledTask
        past_time = datetime.utcnow() - timedelta(minutes=5)

        task = ScheduledTask(
            task_id="due_task",
            execute_at=past_time,
            task_type="send_notification",
            payload={"message": "Due task"}
        )

        scheduler.tasks["due_task"] = task

        # Mock the handler
        mock_handler = AsyncMock()
        scheduler.task_handlers["send_notification"] = mock_handler

        # Mock database notifications processing
        with patch.object(scheduler, '_process_database_notifications', new_callable=AsyncMock):
            await scheduler._process_due_tasks()

        # Task should be removed from scheduler and handler called
        assert "due_task" not in scheduler.tasks
        mock_handler.assert_called_once()


class TestNotificationModels:
    """Test notification models."""

    def test_notification_model_properties(self):
        """Test Notification model properties."""
        notification = Notification(
            id=1,
            target_type=NotificationTarget.USER,
            target_telegram_id=123456789,
            notification_type=NotificationType.ORDER_CREATED,
            message="Test message",
            status=NotificationStatus.SENT
        )

        assert notification.is_sent is True
        assert notification.is_failed is False
        assert notification.is_scheduled is False
        assert notification.should_retry is False

    def test_feedback_rating_model_properties(self):
        """Test FeedbackRating model properties."""
        feedback = FeedbackRating(
            id=1,
            order_id=1,
            user_id=1,
            rating=5
        )

        assert feedback.rating_emoji == "⭐⭐⭐⭐⭐"
        assert feedback.rating_text == "Отлично"

    def test_notification_template_model(self):
        """Test NotificationTemplate model."""
        template = NotificationTemplate(
            notification_type=NotificationType.ORDER_CONFIRMED,
            target_type=NotificationTarget.USER,
            message_template="Order {order_id} confirmed!",
            enabled=True
        )

        assert template.enabled is True
        assert "{order_id}" in template.message_template


class TestNotificationIntegration:
    """Integration tests for notification system."""

    @pytest.mark.asyncio
    async def test_order_notification_flow(self, mock_db, mock_order, mock_user):
        """Test complete order notification flow."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            # Mock database operations
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_user_result
            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            # Test order creation notification
            await notification_service.notify_order_created(mock_order)

            # Test status change notifications
            for status in [OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY, OrderStatus.COMPLETED]:
                old_status = mock_order.status
                mock_order.status = status

                with patch.object(notification_service, '_schedule_feedback_request', new_callable=AsyncMock):
                    await notification_service.notify_order_status_change(mock_order, old_status)

            # Should have multiple notification calls
            assert mock_bot.send_message.call_count >= 5

    @pytest.mark.asyncio
    async def test_payment_notification_integration(self, mock_db, mock_order, mock_user):
        """Test payment notification integration."""
        with patch('app.services.notification.bot') as mock_bot:
            mock_bot.send_message = AsyncMock()

            notification_service = NotificationService(mock_db)

            # Mock database operations
            mock_user_result = MagicMock()
            mock_user_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_user_result
            mock_db.add.return_value = None
            mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

            # Test successful payment notification
            payment_data = {
                "payment_id": 1,
                "amount": 1500.0,
                "payment_method": "card"
            }

            result = await notification_service.notify_payment_success(mock_order, payment_data)
            assert result is True

            # Test failed payment notification
            result = await notification_service.notify_payment_failed(mock_order, "Card declined")
            assert result is True

            # Should have notification calls for both success and failure
            assert mock_bot.send_message.call_count >= 2


@pytest.mark.asyncio
async def test_notification_error_handling(mock_db):
    """Test notification error handling."""
    with patch('app.services.notification.bot') as mock_bot:
        # Simulate Telegram API error
        mock_bot.send_message.side_effect = Exception("Telegram API error")

        notification_service = NotificationService(mock_db)
        mock_db.add.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', 1)

        # Should handle the error gracefully
        result = await notification_service.send_notification(
            telegram_id=123456789,
            message="Test message",
            notification_type=NotificationType.ORDER_CREATED
        )

        # Should still create notification record even if sending fails
        assert mock_db.add.called


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__])