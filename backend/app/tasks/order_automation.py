"""Background tasks for order automation and workflow processing."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.database import get_async_session
from app.services.order import OrderService
from app.services.order_workflow import OrderWorkflow
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class OrderAutomationTasks:
    """Background tasks for order workflow automation."""

    @staticmethod
    async def process_automatic_transitions() -> Dict[str, Any]:
        """
        Process automatic status transitions for all eligible orders.
        This should be run periodically (e.g., every 5-10 minutes).
        """
        results = {
            'task_started_at': datetime.utcnow().isoformat(),
            'processed_orders': 0,
            'transitions_made': 0,
            'errors': []
        }

        try:
            async with get_async_session() as db:
                service = OrderService(db)
                automation_results = await service.process_automatic_transitions(db)

                results.update(automation_results)
                logger.info(f"Automatic transitions processed: {automation_results}")

        except Exception as e:
            error_msg = f"Error in automatic transitions task: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        results['task_completed_at'] = datetime.utcnow().isoformat()
        return results

    @staticmethod
    async def process_overdue_orders(threshold_minutes: int = 60) -> Dict[str, Any]:
        """
        Process overdue orders and send notifications.
        This should be run periodically (e.g., every 30 minutes).
        """
        results = {
            'task_started_at': datetime.utcnow().isoformat(),
            'overdue_orders_found': 0,
            'notifications_sent': 0,
            'errors': []
        }

        try:
            async with get_async_session() as db:
                service = OrderService(db)
                overdue_orders = await service.get_overdue_orders(threshold_minutes, db)

                results['overdue_orders_found'] = len(overdue_orders)

                # Send notifications for overdue orders
                notification_service = NotificationService(db)

                for order in overdue_orders:
                    try:
                        # Check if we already sent overdue notification for this order
                        overdue_notified = order.get_automation_flag('overdue_notification_sent', False)

                        if not overdue_notified:
                            # Send admin notification
                            admin_message = f"""
⚠️ <b>ПРОСРОЧЕННЫЙ ЗАКАЗ #{order.id}</b>

👤 <b>Клиент:</b> {order.customer_name}
📞 <b>Телефон:</b> {order.customer_phone}
💰 <b>Сумма:</b> {order.formatted_total}
🏷 <b>Статус:</b> {order.status_display}
📅 <b>Создан:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}
⏰ <b>Ожидаемое время:</b> {order.estimated_delivery_time.strftime('%d.%m.%Y %H:%M') if order.estimated_delivery_time else 'Не указано'}

Заказ просрочен на {int((datetime.utcnow() - (order.estimated_delivery_time or order.created_at)).total_seconds() / 60)} минут.
                            """.strip()

                            success = await notification_service.send_notification(
                                telegram_id=settings.admin_id,  # Need to import settings
                                message=admin_message,
                                notification_type=NotificationType.ADMIN_OVERDUE_ORDER,
                                target_type=NotificationTarget.ADMIN,
                                order_id=order.id,
                                title="Просроченный заказ"
                            )

                            if success:
                                # Mark as notified
                                order.set_automation_flag('overdue_notification_sent', True)
                                await db.commit()
                                results['notifications_sent'] += 1

                    except Exception as e:
                        error_msg = f"Error processing overdue order {order.id}: {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)

                logger.info(f"Overdue orders processed: {results}")

        except Exception as e:
            error_msg = f"Error in overdue orders task: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        results['task_completed_at'] = datetime.utcnow().isoformat()
        return results

    @staticmethod
    async def process_scheduled_notifications() -> Dict[str, Any]:
        """
        Process scheduled notifications (e.g., feedback requests).
        This should be run frequently (e.g., every 5 minutes).
        """
        results = {
            'task_started_at': datetime.utcnow().isoformat(),
            'notifications_processed': 0,
            'errors': []
        }

        try:
            async with get_async_session() as db:
                notification_service = NotificationService(db)
                processed_count = await notification_service.process_scheduled_notifications()

                results['notifications_processed'] = processed_count
                logger.info(f"Scheduled notifications processed: {processed_count}")

        except Exception as e:
            error_msg = f"Error in scheduled notifications task: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        results['task_completed_at'] = datetime.utcnow().isoformat()
        return results

    @staticmethod
    async def retry_failed_notifications(max_retries: int = 3) -> Dict[str, Any]:
        """
        Retry failed notifications.
        This should be run periodically (e.g., every 15 minutes).
        """
        results = {
            'task_started_at': datetime.utcnow().isoformat(),
            'notifications_retried': 0,
            'errors': []
        }

        try:
            async with get_async_session() as db:
                notification_service = NotificationService(db)
                retried_count = await notification_service.retry_failed_notifications(max_retries)

                results['notifications_retried'] = retried_count
                logger.info(f"Failed notifications retried: {retried_count}")

        except Exception as e:
            error_msg = f"Error in retry notifications task: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        results['task_completed_at'] = datetime.utcnow().isoformat()
        return results

    @staticmethod
    async def calculate_order_metrics() -> Dict[str, Any]:
        """
        Calculate and update order metrics.
        This should be run periodically (e.g., hourly).
        """
        results = {
            'task_started_at': datetime.utcnow().isoformat(),
            'orders_updated': 0,
            'errors': []
        }

        try:
            async with get_async_session() as db:
                # Update preparation durations for orders that are ready/completed but missing duration
                from sqlalchemy import select, and_
                from app.models.order import Order, OrderStatus

                orders_to_update = await db.execute(
                    select(Order).where(
                        and_(
                            Order.status.in_([OrderStatus.READY, OrderStatus.COMPLETED]),
                            Order.preparation_duration.is_(None),
                            Order.actual_preparation_start.isnot(None),
                            Order.actual_preparation_end.isnot(None)
                        )
                    )
                )
                orders = orders_to_update.scalars().all()

                for order in orders:
                    if order.actual_preparation_start and order.actual_preparation_end:
                        duration = order.actual_preparation_end - order.actual_preparation_start
                        order.preparation_duration = int(duration.total_seconds() / 60)
                        results['orders_updated'] += 1

                # Update total durations for completed orders
                completed_orders = await db.execute(
                    select(Order).where(
                        and_(
                            Order.status == OrderStatus.COMPLETED,
                            Order.total_duration.is_(None),
                            Order.status_completed_at.isnot(None)
                        )
                    )
                )
                for order in completed_orders.scalars().all():
                    if order.status_completed_at:
                        duration = order.status_completed_at - order.created_at
                        order.total_duration = int(duration.total_seconds() / 60)
                        results['orders_updated'] += 1

                await db.commit()
                logger.info(f"Order metrics updated: {results}")

        except Exception as e:
            error_msg = f"Error in calculate metrics task: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        results['task_completed_at'] = datetime.utcnow().isoformat()
        return results

    @staticmethod
    async def cleanup_old_records(days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old records (soft delete very old data).
        This should be run daily.
        """
        results = {
            'task_started_at': datetime.utcnow().isoformat(),
            'records_cleaned': 0,
            'errors': []
        }

        try:
            async with get_async_session() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

                # Clean up old status history records for completed/cancelled orders
                from sqlalchemy import select, and_, update
                from app.models.order_status_history import OrderStatusHistory
                from app.models.order import Order, OrderStatus

                # Find old completed orders
                old_orders = await db.execute(
                    select(Order.id).where(
                        and_(
                            Order.status.in_([OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
                            Order.updated_at < cutoff_date,
                            Order.is_deleted == False
                        )
                    )
                )
                old_order_ids = [row[0] for row in old_orders.all()]

                if old_order_ids:
                    # Archive old status history (keep for audit but mark as archived)
                    history_update = await db.execute(
                        update(OrderStatusHistory)
                        .where(OrderStatusHistory.order_id.in_(old_order_ids))
                        .values(workflow_data=OrderStatusHistory.workflow_data.op('||')({'archived': True}))
                    )
                    results['records_cleaned'] = len(old_order_ids)

                await db.commit()
                logger.info(f"Old records cleaned: {results}")

        except Exception as e:
            error_msg = f"Error in cleanup task: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)

        results['task_completed_at'] = datetime.utcnow().isoformat()
        return results

    @staticmethod
    async def run_all_maintenance_tasks() -> Dict[str, Any]:
        """
        Run all maintenance tasks in sequence.
        This can be used for comprehensive maintenance.
        """
        all_results = {
            'maintenance_started_at': datetime.utcnow().isoformat(),
            'tasks': {},
            'total_errors': 0
        }

        tasks = [
            ('automatic_transitions', OrderAutomationTasks.process_automatic_transitions),
            ('overdue_orders', lambda: OrderAutomationTasks.process_overdue_orders()),
            ('scheduled_notifications', OrderAutomationTasks.process_scheduled_notifications),
            ('retry_failed_notifications', lambda: OrderAutomationTasks.retry_failed_notifications()),
            ('calculate_metrics', OrderAutomationTasks.calculate_order_metrics),
            ('cleanup_old_records', lambda: OrderAutomationTasks.cleanup_old_records())
        ]

        for task_name, task_func in tasks:
            try:
                logger.info(f"Running maintenance task: {task_name}")
                task_results = await task_func()
                all_results['tasks'][task_name] = task_results
                all_results['total_errors'] += len(task_results.get('errors', []))

                # Small delay between tasks
                await asyncio.sleep(1)

            except Exception as e:
                error_msg = f"Error in maintenance task {task_name}: {e}"
                all_results['tasks'][task_name] = {
                    'error': error_msg,
                    'task_failed_at': datetime.utcnow().isoformat()
                }
                all_results['total_errors'] += 1
                logger.error(error_msg)

        all_results['maintenance_completed_at'] = datetime.utcnow().isoformat()
        logger.info(f"All maintenance tasks completed. Total errors: {all_results['total_errors']}")

        return all_results


# Convenient functions for scheduling
async def run_automatic_transitions():
    """Wrapper function for running automatic transitions."""
    return await OrderAutomationTasks.process_automatic_transitions()


async def run_overdue_monitoring():
    """Wrapper function for monitoring overdue orders."""
    return await OrderAutomationTasks.process_overdue_orders()


async def run_notification_processing():
    """Wrapper function for processing notifications."""
    return await OrderAutomationTasks.process_scheduled_notifications()


async def run_maintenance():
    """Wrapper function for running all maintenance tasks."""
    return await OrderAutomationTasks.run_all_maintenance_tasks()


# Example scheduler integration (if using APScheduler or similar)
TASK_SCHEDULES = {
    'automatic_transitions': {'minutes': 5},  # Every 5 minutes
    'overdue_monitoring': {'minutes': 30},    # Every 30 minutes
    'notification_processing': {'minutes': 5}, # Every 5 minutes
    'retry_notifications': {'minutes': 15},   # Every 15 minutes
    'calculate_metrics': {'hours': 1},        # Every hour
    'cleanup_old_records': {'days': 1},       # Daily
}