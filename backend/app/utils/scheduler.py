"""Task scheduler for handling delayed notifications and background tasks."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Scheduled task representation."""
    task_id: str
    execute_at: datetime
    task_type: str
    payload: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3


class NotificationScheduler:
    """Scheduler for handling delayed notifications and background tasks."""

    def __init__(self):
        self.running = False
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default task handlers."""
        self.task_handlers.update({
            'send_notification': self._handle_send_notification,
            'process_feedback_request': self._handle_feedback_request,
            'retry_failed_notifications': self._handle_retry_failed_notifications,
            'daily_stats': self._handle_daily_stats,
        })

    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        logger.info("Starting notification scheduler")

        # Start main scheduler loop
        asyncio.create_task(self._scheduler_loop())

        # Schedule daily stats
        await self._schedule_daily_stats()

        # Schedule failed notification retries
        await self._schedule_failed_notification_retries()

    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Stopping notification scheduler")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                await self._process_due_tasks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _process_due_tasks(self):
        """Process all tasks that are due for execution."""
        current_time = datetime.utcnow()
        due_tasks = []

        # Find due tasks
        for task_id, task in list(self.tasks.items()):
            if task.execute_at <= current_time:
                due_tasks.append(task)
                del self.tasks[task_id]

        # Execute due tasks
        for task in due_tasks:
            await self._execute_task(task)

        # Also process scheduled notifications from database
        await self._process_database_notifications()

    async def _execute_task(self, task: ScheduledTask):
        """Execute a single task."""
        try:
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                logger.error(f"No handler found for task type: {task.task_type}")
                return

            await handler(task.payload)
            logger.info(f"Task {task.task_id} executed successfully")

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.execute_at = datetime.utcnow() + timedelta(minutes=5 * task.retry_count)
                self.tasks[task.task_id] = task
                logger.info(f"Task {task.task_id} scheduled for retry {task.retry_count}")

    async def _process_database_notifications(self):
        """Process scheduled notifications from database."""
        try:
            async with async_session_maker() as db:
                notification_service = NotificationService(db)
                await notification_service.process_scheduled_notifications()
        except Exception as e:
            logger.error(f"Error processing database notifications: {e}")

    # Task handlers
    async def _handle_send_notification(self, payload: Dict[str, Any]):
        """Handle sending a notification."""
        try:
            async with async_session_maker() as db:
                notification_service = NotificationService(db)

                await notification_service.send_notification(
                    telegram_id=payload['telegram_id'],
                    message=payload['message'],
                    notification_type=payload['notification_type'],
                    target_type=payload.get('target_type'),
                    order_id=payload.get('order_id'),
                    user_id=payload.get('user_id'),
                    title=payload.get('title'),
                    inline_keyboard=payload.get('inline_keyboard'),
                    metadata=payload.get('metadata')
                )

        except Exception as e:
            logger.error(f"Error handling send notification: {e}")
            raise

    async def _handle_feedback_request(self, payload: Dict[str, Any]):
        """Handle feedback request task."""
        try:
            async with async_session_maker() as db:
                notification_service = NotificationService(db)

                # Check if feedback already exists
                from app.models.notification import FeedbackRating
                from sqlalchemy import select

                existing = await db.execute(
                    select(FeedbackRating).where(FeedbackRating.order_id == payload['order_id'])
                )

                if existing.scalar_one_or_none():
                    logger.info(f"Feedback already exists for order {payload['order_id']}")
                    return

                # Send feedback request
                await notification_service.send_notification(
                    telegram_id=payload['telegram_id'],
                    message=payload['message'],
                    notification_type=payload['notification_type'],
                    target_type=payload['target_type'],
                    order_id=payload['order_id'],
                    user_id=payload['user_id'],
                    title=payload['title'],
                    inline_keyboard=payload['inline_keyboard']
                )

        except Exception as e:
            logger.error(f"Error handling feedback request: {e}")
            raise

    async def _handle_retry_failed_notifications(self, payload: Dict[str, Any]):
        """Handle retrying failed notifications."""
        try:
            async with async_session_maker() as db:
                notification_service = NotificationService(db)
                retried_count = await notification_service.retry_failed_notifications()
                logger.info(f"Retried {retried_count} failed notifications")

        except Exception as e:
            logger.error(f"Error handling retry failed notifications: {e}")
            raise

    async def _handle_daily_stats(self, payload: Dict[str, Any]):
        """Handle sending daily statistics to admin."""
        try:
            async with async_session_maker() as db:
                notification_service = NotificationService(db)

                # Get daily stats
                stats = await notification_service.get_notification_stats(days=1)

                if stats:
                    message = f"""
📊 <b>Ежедневная статистика уведомлений</b>

📅 <b>За последние 24 часа:</b>
📧 <b>Всего уведомлений:</b> {stats['total_notifications']}
✅ <b>Отправлено:</b> {stats['sent_notifications']}
❌ <b>Ошибок:</b> {stats['failed_notifications']}
📈 <b>Успешность:</b> {stats['success_rate']}%

<i>Автоматическая отчетность системы уведомлений</i>
                    """.strip()

                    from app.models.notification import NotificationType, NotificationTarget
                    from app.config import settings

                    await notification_service.send_notification(
                        telegram_id=settings.admin_id,
                        message=message,
                        notification_type=NotificationType.ADMIN_DAILY_STATS,
                        target_type=NotificationTarget.ADMIN,
                        title="Статистика уведомлений"
                    )

        except Exception as e:
            logger.error(f"Error handling daily stats: {e}")
            raise

    # Scheduling methods
    async def schedule_task(
        self,
        task_id: str,
        execute_at: datetime,
        task_type: str,
        payload: Dict[str, Any],
        max_retries: int = 3
    ):
        """Schedule a task for execution."""
        task = ScheduledTask(
            task_id=task_id,
            execute_at=execute_at,
            task_type=task_type,
            payload=payload,
            max_retries=max_retries
        )

        self.tasks[task_id] = task
        logger.info(f"Task {task_id} scheduled for {execute_at}")

    async def schedule_notification(
        self,
        telegram_id: int,
        message: str,
        notification_type: str,
        delay_minutes: int = 0,
        **kwargs
    ):
        """Schedule a notification to be sent later."""
        execute_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        task_id = f"notification_{telegram_id}_{int(execute_at.timestamp())}"

        payload = {
            'telegram_id': telegram_id,
            'message': message,
            'notification_type': notification_type,
            **kwargs
        }

        await self.schedule_task(
            task_id=task_id,
            execute_at=execute_at,
            task_type='send_notification',
            payload=payload
        )

    async def schedule_feedback_request(
        self,
        order_id: int,
        user_id: int,
        telegram_id: int,
        delay_hours: int = 1
    ):
        """Schedule a feedback request for an order."""
        execute_at = datetime.utcnow() + timedelta(hours=delay_hours)
        task_id = f"feedback_{order_id}_{int(execute_at.timestamp())}"

        from app.models.notification import NotificationType, NotificationTarget

        feedback_message = f"""
⭐ <b>Оцените заказ #{order_id}</b>

Как вам понравился заказ? Ваше мнение очень важно для нас!

Пожалуйста, поставьте оценку от 1 до 5 звезд:
        """.strip()

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "⭐", "callback_data": f"rate_order_{order_id}_1"},
                    {"text": "⭐⭐", "callback_data": f"rate_order_{order_id}_2"},
                    {"text": "⭐⭐⭐", "callback_data": f"rate_order_{order_id}_3"},
                    {"text": "⭐⭐⭐⭐", "callback_data": f"rate_order_{order_id}_4"},
                    {"text": "⭐⭐⭐⭐⭐", "callback_data": f"rate_order_{order_id}_5"}
                ]
            ]
        }

        payload = {
            'order_id': order_id,
            'user_id': user_id,
            'telegram_id': telegram_id,
            'message': feedback_message,
            'notification_type': NotificationType.FEEDBACK_REQUEST,
            'target_type': NotificationTarget.USER,
            'title': 'Оцените заказ',
            'inline_keyboard': inline_keyboard
        }

        await self.schedule_task(
            task_id=task_id,
            execute_at=execute_at,
            task_type='process_feedback_request',
            payload=payload
        )

    async def _schedule_daily_stats(self):
        """Schedule daily statistics reports."""
        # Schedule for every day at 9:00 AM
        from datetime import time

        now = datetime.utcnow()
        next_report = datetime.combine(now.date(), time(9, 0))

        # If it's already past 9 AM today, schedule for tomorrow
        if next_report <= now:
            next_report += timedelta(days=1)

        await self.schedule_task(
            task_id=f"daily_stats_{int(next_report.timestamp())}",
            execute_at=next_report,
            task_type='daily_stats',
            payload={}
        )

        logger.info(f"Daily stats scheduled for {next_report}")

    async def _schedule_failed_notification_retries(self):
        """Schedule periodic retries for failed notifications."""
        # Schedule retry every 2 hours
        execute_at = datetime.utcnow() + timedelta(hours=2)

        await self.schedule_task(
            task_id=f"retry_failed_{int(execute_at.timestamp())}",
            execute_at=execute_at,
            task_type='retry_failed_notifications',
            payload={}
        )

        logger.info(f"Failed notification retries scheduled for {execute_at}")

    def cancel_task(self, task_id: str):
        """Cancel a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Task {task_id} cancelled")

    def get_scheduled_tasks(self) -> Dict[str, ScheduledTask]:
        """Get all scheduled tasks."""
        return self.tasks.copy()


# Global scheduler instance
scheduler = NotificationScheduler()


# Utility functions for easy access
async def start_scheduler():
    """Start the global scheduler."""
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    await scheduler.stop()


async def schedule_notification(
    telegram_id: int,
    message: str,
    notification_type: str,
    delay_minutes: int = 0,
    **kwargs
):
    """Schedule a notification using the global scheduler."""
    await scheduler.schedule_notification(
        telegram_id=telegram_id,
        message=message,
        notification_type=notification_type,
        delay_minutes=delay_minutes,
        **kwargs
    )


async def schedule_feedback_request(
    order_id: int,
    user_id: int,
    telegram_id: int,
    delay_hours: int = 1
):
    """Schedule a feedback request using the global scheduler."""
    await scheduler.schedule_feedback_request(
        order_id=order_id,
        user_id=user_id,
        telegram_id=telegram_id,
        delay_hours=delay_hours
    )