"""Tests for notification API endpoints."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.notification import (
    NotificationType, NotificationStatus, NotificationTarget,
    Notification, FeedbackRating
)


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_notification():
    """Mock notification."""
    notification = Notification(
        id=1,
        target_type=NotificationTarget.USER,
        target_telegram_id=123456789,
        notification_type=NotificationType.ORDER_CREATED,
        status=NotificationStatus.SENT,
        title="Test Notification",
        message="Test message",
        order_id=1,
        user_id=1,
        created_at=datetime.utcnow(),
        retry_count=0
    )
    notification.sent_at = datetime.utcnow()
    return notification


@pytest.fixture
def mock_feedback():
    """Mock feedback."""
    feedback = FeedbackRating(
        id=1,
        order_id=1,
        user_id=1,
        rating=5,
        feedback_text="Excellent service!",
        created_at=datetime.utcnow()
    )
    feedback.rating_emoji = "⭐⭐⭐⭐⭐"
    feedback.rating_text = "Отлично"
    return feedback


class TestNotificationAPI:
    """Test notification API endpoints."""

    @patch('app.api.notifications.get_notification_service')
    def test_create_notification(self, mock_get_service, client, mock_notification):
        """Test creating a notification."""
        mock_service = AsyncMock()
        mock_service.send_notification.return_value = mock_notification
        mock_get_service.return_value = mock_service

        notification_data = {
            "target_telegram_id": 123456789,
            "notification_type": "order_created",
            "target_type": "user",
            "title": "Test Notification",
            "message": "Test message",
            "order_id": 1,
            "user_id": 1
        }

        response = client.post("/api/notifications/", json=notification_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["message"] == "Test message"
        assert data["notification_type"] == "order_created"

    @patch('app.api.notifications.get_db')
    def test_get_notifications(self, mock_get_db, client, mock_notification):
        """Test getting notifications."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_notification]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/notifications/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1

    @patch('app.api.notifications.get_db')
    def test_get_notification_by_id(self, mock_get_db, client, mock_notification):
        """Test getting a specific notification."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification
        mock_db.execute.return_value = mock_result

        response = client.get("/api/notifications/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["message"] == "Test message"

    @patch('app.api.notifications.get_db')
    def test_get_notification_not_found(self, mock_get_db, client):
        """Test getting a non-existent notification."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock notification not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/notifications/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.notifications.get_notification_service')
    @patch('app.api.notifications.get_db')
    def test_retry_notification(self, mock_get_db, mock_get_service, client, mock_notification):
        """Test retrying a failed notification."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        mock_service = AsyncMock()
        mock_service._send_telegram_message.return_value = True
        mock_get_service.return_value = mock_service

        # Mock failed notification
        mock_notification.status = NotificationStatus.FAILED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification
        mock_db.execute.return_value = mock_result

        response = client.post("/api/notifications/1/retry")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @patch('app.api.notifications.get_db')
    def test_delete_notification(self, mock_get_db, client, mock_notification):
        """Test deleting a notification."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock notification found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_notification
        mock_db.execute.return_value = mock_result

        response = client.delete("/api/notifications/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted successfully" in data["message"]


class TestNotificationStatsAPI:
    """Test notification statistics API endpoints."""

    @patch('app.api.notifications.get_notification_service')
    def test_get_notification_stats(self, mock_get_service, client):
        """Test getting notification statistics."""
        mock_service = AsyncMock()
        mock_service.get_notification_stats.return_value = {
            "period_days": 7,
            "total_notifications": 100,
            "sent_notifications": 90,
            "failed_notifications": 5,
            "success_rate": 90.0
        }
        mock_get_service.return_value = mock_service

        response = client.get("/api/notifications/stats/overview?days=7")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_notifications"] == 100
        assert data["sent_notifications"] == 90
        assert data["success_rate"] == 90.0
        assert data["pending_notifications"] == 5  # total - sent - failed

    @patch('app.api.notifications.get_db')
    def test_get_stats_by_type(self, mock_get_db, client):
        """Test getting statistics by notification type."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock database query results
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.notification_type = NotificationType.ORDER_CREATED
        mock_row.total = 50
        mock_row.sent = 45
        mock_row.failed = 3

        mock_result.__iter__ = lambda self: iter([mock_row])
        mock_db.execute.return_value = mock_result

        response = client.get("/api/notifications/stats/by-type?days=7")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["period_days"] == 7
        assert len(data["stats_by_type"]) == 1
        assert data["stats_by_type"][0]["notification_type"] == "order_created"
        assert data["stats_by_type"][0]["total"] == 50


class TestFeedbackAPI:
    """Test feedback API endpoints."""

    @patch('app.api.notifications.get_notification_service')
    def test_create_feedback(self, mock_get_service, client, mock_feedback):
        """Test creating feedback."""
        mock_service = AsyncMock()
        mock_service.save_feedback_rating.return_value = mock_feedback
        mock_get_service.return_value = mock_service

        feedback_data = {
            "order_id": 1,
            "user_id": 1,
            "rating": 5,
            "feedback_text": "Excellent service!"
        }

        response = client.post("/api/notifications/feedback", json=feedback_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rating"] == 5
        assert data["feedback_text"] == "Excellent service!"

    @patch('app.api.notifications.get_notification_service')
    def test_create_feedback_already_exists(self, mock_get_service, client):
        """Test creating feedback when it already exists."""
        mock_service = AsyncMock()
        mock_service.save_feedback_rating.return_value = None  # Already exists
        mock_get_service.return_value = mock_service

        feedback_data = {
            "order_id": 1,
            "user_id": 1,
            "rating": 5
        }

        response = client.post("/api/notifications/feedback", json=feedback_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    @patch('app.api.notifications.get_db')
    def test_get_feedback(self, mock_get_db, client, mock_feedback):
        """Test getting feedback."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_feedback]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/notifications/feedback")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["rating"] == 5

    @patch('app.api.notifications.get_db')
    def test_get_feedback_stats(self, mock_get_db, client):
        """Test getting feedback statistics."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock average rating query
        mock_avg_result = MagicMock()
        mock_avg_result.scalar.return_value = 4.5

        # Mock rating distribution query
        mock_dist_result = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.rating = 5
        mock_row1.count = 10
        mock_row2 = MagicMock()
        mock_row2.rating = 4
        mock_row2.count = 5

        mock_dist_result.__iter__ = lambda self: iter([mock_row1, mock_row2])

        mock_db.execute.side_effect = [mock_avg_result, mock_dist_result]

        response = client.get("/api/notifications/feedback/stats?days=30")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["average_rating"] == 4.5
        assert data["total_feedback"] == 15
        assert "rating_distribution" in data


class TestNotificationTemplateAPI:
    """Test notification template API endpoints."""

    @patch('app.api.notifications.get_db')
    def test_create_template(self, mock_get_db, client):
        """Test creating a notification template."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        template_data = {
            "notification_type": "order_created",
            "target_type": "user",
            "title_template": "Order Created",
            "message_template": "Your order #{order_id} has been created",
            "enabled": True,
            "delay_minutes": 0
        }

        response = client.post("/api/notifications/templates", json=template_data)

        assert response.status_code == status.HTTP_200_OK
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.api.notifications.get_db')
    def test_get_templates(self, mock_get_db, client):
        """Test getting notification templates."""
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db

        # Mock template
        from app.models.notification import NotificationTemplate
        mock_template = NotificationTemplate(
            id=1,
            notification_type=NotificationType.ORDER_CREATED,
            target_type=NotificationTarget.USER,
            message_template="Test template",
            enabled=True,
            delay_minutes=0
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_template]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/notifications/templates")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["message_template"] == "Test template"


class TestSchedulerAPI:
    """Test scheduler API endpoints."""

    @patch('app.api.notifications.scheduler')
    def test_get_scheduled_tasks(self, mock_scheduler, client):
        """Test getting scheduled tasks."""
        from app.utils.scheduler import ScheduledTask

        mock_task = ScheduledTask(
            task_id="test_task",
            execute_at=datetime.utcnow() + timedelta(hours=1),
            task_type="send_notification",
            payload={"message": "test"}
        )

        mock_scheduler.get_scheduled_tasks.return_value = {"test_task": mock_task}

        response = client.get("/api/notifications/scheduler/tasks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_id"] == "test_task"

    @patch('app.api.notifications.scheduler')
    def test_cancel_scheduled_task(self, mock_scheduler, client):
        """Test cancelling a scheduled task."""
        mock_scheduler.cancel_task = MagicMock()

        response = client.post("/api/notifications/scheduler/tasks/test_task/cancel")

        assert response.status_code == status.HTTP_200_OK
        mock_scheduler.cancel_task.assert_called_once_with("test_task")


class TestNotificationProcessingAPI:
    """Test notification processing API endpoints."""

    @patch('app.api.notifications.get_notification_service')
    def test_process_scheduled_notifications(self, mock_get_service, client):
        """Test processing scheduled notifications."""
        mock_service = AsyncMock()
        mock_service.process_scheduled_notifications.return_value = 5
        mock_get_service.return_value = mock_service

        response = client.post("/api/notifications/process-scheduled")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Processed 5 scheduled notifications" in data["message"]

    @patch('app.api.notifications.get_notification_service')
    def test_retry_failed_notifications(self, mock_get_service, client):
        """Test retrying failed notifications."""
        mock_service = AsyncMock()
        mock_service.retry_failed_notifications.return_value = 3
        mock_get_service.return_value = mock_service

        response = client.post("/api/notifications/retry-failed?max_retries=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Retried 3 failed notifications" in data["message"]


class TestAPIValidation:
    """Test API input validation."""

    def test_create_notification_invalid_data(self, client):
        """Test creating notification with invalid data."""
        invalid_data = {
            "target_telegram_id": "invalid",  # Should be int
            "notification_type": "invalid_type",
            "message": ""  # Empty message
        }

        response = client.post("/api/notifications/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_feedback_invalid_rating(self, client):
        """Test creating feedback with invalid rating."""
        invalid_data = {
            "order_id": 1,
            "user_id": 1,
            "rating": 10  # Invalid rating (should be 1-5)
        }

        response = client.post("/api/notifications/feedback", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_notifications_invalid_params(self, client):
        """Test getting notifications with invalid parameters."""
        response = client.get("/api/notifications/?skip=-1&limit=0")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


if __name__ == "__main__":
    pytest.main([__file__])