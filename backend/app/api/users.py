"""Users API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.services.user import UserService

router = APIRouter()


@router.get("/me")
async def get_current_user(
    telegram_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get current user by Telegram ID."""
    service = UserService(db)
    user = await service.get_user_by_telegram_id(telegram_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "phone": user.phone
    }