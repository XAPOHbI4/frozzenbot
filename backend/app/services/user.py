"""User service."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.models.user import User


class UserService:
    """User service for managing Telegram users."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def create_or_update_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: str = "",
        last_name: Optional[str] = None
    ) -> User:
        """Create or update user in database."""
        async for db in get_async_session():
            # Try to find existing user
            result = await db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Update existing user
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = True
            else:
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=telegram_id == 1050239011  # Admin ID from config
                )
                db.add(user)

            await db.commit()
            await db.refresh(user)
            return user
            break

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        async for db in get_async_session():
            result = await db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
            break

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        async for db in get_async_session():
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
            break