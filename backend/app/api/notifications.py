"""API endpoints for notification management."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.notification import (
    Notification, NotificationTemplate, FeedbackRating,
    NotificationType, NotificationStatus, NotificationTarget
)
from app.models.order import Order
from app.models.user import User
from app.services.notification import NotificationService
from app.utils.scheduler import scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# Pydantic models
class NotificationCreate(BaseModel):
    """Schema for creating a notification."""
    target_telegram_id: int
    notification_type: NotificationType
    target_type: NotificationTarget = NotificationTarget.USER
    title: Optional[str] = None
    message: str
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    inline_keyboard: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: int
    target_telegram_id: int
    notification_type: NotificationType
    target_type: NotificationTarget
    status: NotificationStatus
    title: Optional[str]
    message: str
    order_id: Optional[int]
    user_id: Optional[int]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    retry_count: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Schema for notification statistics."""
    period_days: int
    total_notifications: int
    sent_notifications: int
    failed_notifications: int
    pending_notifications: int
    scheduled_notifications: int
    success_rate: float


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    order_id: int
    user_id: int
    rating: int
    feedback_text: Optional[str]
    created_at: datetime
    rating_emoji: str
    rating_text: str

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    order_id: int
    user_id: int
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None
    notification_id: Optional[int] = None


class TemplateResponse(BaseModel):
    """Schema for notification template response."""
    id: int
    notification_type: NotificationType
    target_type: NotificationTarget
    title_template: Optional[str]
    message_template: str
    enabled: bool
    delay_minutes: int
    description: Optional[str]
    variables: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class TemplateCreate(BaseModel):
    """Schema for creating notification template."""
    notification_type: NotificationType
    target_type: NotificationTarget
    title_template: Optional[str] = None
    message_template: str
    enabled: bool = True
    delay_minutes: int = 0
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


# Dependencies
async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)


# Notification endpoints
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create and send a new notification."""
    try:
        notification = await notification_service.send_notification(
            telegram_id=notification_data.target_telegram_id,
            message=notification_data.message,
            notification_type=notification_data.notification_type,
            target_type=notification_data.target_type,
            order_id=notification_data.order_id,
            user_id=notification_data.user_id,
            title=notification_data.title,
            inline_keyboard=notification_data.inline_keyboard,
            schedule_for=notification_data.scheduled_at,
            notification_metadata=notification_data.metadata
        )

        if not notification:
            raise HTTPException(status_code=500, detail="Failed to create notification")

        return notification

    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    notification_type: Optional[NotificationType] = None,
    target_type: Optional[NotificationTarget] = None,
    status: Optional[NotificationStatus] = None,
    order_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get notifications with filtering."""
    try:
        # Build query
        query = select(Notification).where(Notification.is_deleted == False)

        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if target_type:
            query = query.where(Notification.target_type == target_type)
        if status:
            query = query.where(Notification.status == status)
        if order_id:
            query = query.where(Notification.order_id == order_id)
        if user_id:
            query = query.where(Notification.user_id == user_id)

        query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        notifications = result.scalars().all()

        return notifications

    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific notification by ID."""
    try:
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.is_deleted == False
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        return notification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/retry")
async def retry_notification(
    notification_id: int = Path(..., ge=1),
    notification_service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed notification."""
    try:
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.is_deleted == False
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.status != NotificationStatus.FAILED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry notification with status: {notification.status.value}"
            )

        # Reset status and retry
        notification.status = NotificationStatus.PENDING
        notification.error_message = None
        await db.commit()

        # Send notification
        success = await notification_service._send_telegram_message(notification)

        return {"success": success, "message": "Notification retry initiated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Delete (soft delete) a notification."""
    try:
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.is_deleted == False
                )
            )
        )
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.is_deleted = True
        await db.commit()

        return {"message": "Notification deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints
@router.get("/stats/overview", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(7, ge=1, le=365),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Get notification statistics for the specified period."""
    try:
        stats = await notification_service.get_notification_stats(days=days)

        if not stats:
            stats = {
                "period_days": days,
                "total_notifications": 0,
                "sent_notifications": 0,
                "failed_notifications": 0,
                "success_rate": 0.0
            }

        # Add additional stats
        stats["pending_notifications"] = stats["total_notifications"] - stats["sent_notifications"] - stats["failed_notifications"]
        stats["scheduled_notifications"] = 0  # We'll calculate this separately

        return stats

    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-type")
async def get_stats_by_type(
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get notification statistics grouped by type."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # Group by notification type
        result = await db.execute(
            select(
                Notification.notification_type,
                func.count(Notification.id).label('total'),
                func.sum(
                    func.case(
                        (Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED]), 1),
                        else_=0
                    )
                ).label('sent'),
                func.sum(
                    func.case(
                        (Notification.status == NotificationStatus.FAILED, 1),
                        else_=0
                    )
                ).label('failed')
            )
            .where(
                and_(
                    Notification.created_at >= start_date,
                    Notification.is_deleted == False
                )
            )
            .group_by(Notification.notification_type)
        )

        stats_by_type = []
        for row in result:
            total = row.total or 0
            sent = row.sent or 0
            failed = row.failed or 0
            success_rate = (sent / total * 100) if total > 0 else 0

            stats_by_type.append({
                "notification_type": row.notification_type.value,
                "total": total,
                "sent": sent,
                "failed": failed,
                "success_rate": round(success_rate, 2)
            })

        return {
            "period_days": days,
            "stats_by_type": stats_by_type
        }

    except Exception as e:
        logger.error(f"Error getting stats by type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Feedback endpoints
@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Create feedback rating for an order."""
    try:
        feedback = await notification_service.save_feedback_rating(
            order_id=feedback_data.order_id,
            user_id=feedback_data.user_id,
            rating=feedback_data.rating,
            feedback_text=feedback_data.feedback_text,
            notification_id=feedback_data.notification_id
        )

        if not feedback:
            raise HTTPException(status_code=400, detail="Feedback already exists for this order")

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    order_id: Optional[int] = None,
    user_id: Optional[int] = None,
    rating: Optional[int] = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """Get feedback ratings with filtering."""
    try:
        query = select(FeedbackRating).where(FeedbackRating.is_deleted == False)

        if order_id:
            query = query.where(FeedbackRating.order_id == order_id)
        if user_id:
            query = query.where(FeedbackRating.user_id == user_id)
        if rating:
            query = query.where(FeedbackRating.rating == rating)

        query = query.order_by(desc(FeedbackRating.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        feedback_list = result.scalars().all()

        return feedback_list

    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats")
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get feedback statistics."""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # Average rating
        avg_result = await db.execute(
            select(func.avg(FeedbackRating.rating))
            .where(
                and_(
                    FeedbackRating.created_at >= start_date,
                    FeedbackRating.is_deleted == False
                )
            )
        )
        avg_rating = avg_result.scalar() or 0

        # Rating distribution
        rating_dist_result = await db.execute(
            select(
                FeedbackRating.rating,
                func.count(FeedbackRating.id).label('count')
            )
            .where(
                and_(
                    FeedbackRating.created_at >= start_date,
                    FeedbackRating.is_deleted == False
                )
            )
            .group_by(FeedbackRating.rating)
        )

        rating_distribution = {}
        total_feedback = 0
        for row in rating_dist_result:
            rating_distribution[str(row.rating)] = row.count
            total_feedback += row.count

        return {
            "period_days": days,
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2),
            "rating_distribution": rating_distribution
        }

    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Template endpoints
@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a notification template."""
    try:
        template = NotificationTemplate(
            notification_type=template_data.notification_type,
            target_type=template_data.target_type,
            title_template=template_data.title_template,
            message_template=template_data.message_template,
            enabled=template_data.enabled,
            delay_minutes=template_data.delay_minutes,
            description=template_data.description,
            variables=template_data.variables
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        return template

    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[TemplateResponse])
async def get_templates(
    notification_type: Optional[NotificationType] = None,
    target_type: Optional[NotificationTarget] = None,
    enabled: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get notification templates with filtering."""
    try:
        query = select(NotificationTemplate).where(NotificationTemplate.is_deleted == False)

        if notification_type:
            query = query.where(NotificationTemplate.notification_type == notification_type)
        if target_type:
            query = query.where(NotificationTemplate.target_type == target_type)
        if enabled is not None:
            query = query.where(NotificationTemplate.enabled == enabled)

        result = await db.execute(query)
        templates = result.scalars().all()

        return templates

    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Process scheduled notifications endpoint
@router.post("/process-scheduled")
async def process_scheduled_notifications(
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Manually trigger processing of scheduled notifications."""
    try:
        sent_count = await notification_service.process_scheduled_notifications()
        return {"message": f"Processed {sent_count} scheduled notifications"}

    except Exception as e:
        logger.error(f"Error processing scheduled notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Retry failed notifications endpoint
@router.post("/retry-failed")
async def retry_failed_notifications(
    max_retries: int = Query(3, ge=1, le=10),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Retry all failed notifications."""
    try:
        retried_count = await notification_service.retry_failed_notifications(max_retries=max_retries)
        return {"message": f"Retried {retried_count} failed notifications"}

    except Exception as e:
        logger.error(f"Error retrying failed notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Scheduler endpoints
@router.get("/scheduler/tasks")
async def get_scheduled_tasks():
    """Get all scheduled tasks from the scheduler."""
    try:
        tasks = scheduler.get_scheduled_tasks()
        task_list = []

        for task_id, task in tasks.items():
            task_list.append({
                "task_id": task_id,
                "execute_at": task.execute_at,
                "task_type": task.task_type,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "payload": task.payload
            })

        return {"tasks": task_list}

    except Exception as e:
        logger.error(f"Error getting scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/tasks/{task_id}/cancel")
async def cancel_scheduled_task(task_id: str = Path(...)):
    """Cancel a scheduled task."""
    try:
        scheduler.cancel_task(task_id)
        return {"message": f"Task {task_id} cancelled successfully"}

    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))