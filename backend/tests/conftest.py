"""Pytest configuration and fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User, UserRole
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create async database session for testing."""
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(db_session):
    """Create test user."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        role=UserRole.USER,
        password_hash="hashed_password"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def test_admin_user(db_session):
    """Create test admin user."""
    user = User(
        telegram_id=987654321,
        username="admin",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        role=UserRole.ADMIN,
        is_admin=True,
        password_hash="hashed_admin_password"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def test_manager_user(db_session):
    """Create test manager user."""
    user = User(
        telegram_id=555666777,
        username="manager",
        first_name="Manager",
        last_name="User",
        email="manager@example.com",
        role=UserRole.MANAGER,
        password_hash="hashed_manager_password"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('app.utils.jwt.redis.from_url') as mock_redis_factory:
        mock_client = MagicMock()
        mock_redis_factory.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch('app.utils.jwt.settings') as mock_settings:
        mock_settings.secret_key = "test-secret-key"
        mock_settings.algorithm = "HS256"
        mock_settings.access_token_expire_minutes = 30
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.bot_token = "test-bot-token"
        yield mock_settings


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": 1,
        "role": "user",
        "telegram_id": 123456789,
        "username": "testuser"
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data for testing."""
    return {
        "user_id": 2,
        "role": "admin",
        "telegram_id": 987654321,
        "username": "admin"
    }


# Auth-specific fixtures
@pytest.fixture
def valid_login_data():
    """Valid login request data."""
    return {
        "username": "testuser",
        "password": "TestPassword123!"
    }


@pytest.fixture
def invalid_login_data():
    """Invalid login request data."""
    return {
        "username": "nonexistent",
        "password": "wrongpassword"
    }


@pytest.fixture
def valid_registration_data():
    """Valid user registration data."""
    return {
        "username": "newuser",
        "password": "NewPassword123!",
        "first_name": "New",
        "last_name": "User",
        "email": "new@example.com",
        "role": "manager"
    }


@pytest.fixture
def telegram_init_data():
    """Sample Telegram WebApp init data."""
    return {
        "init_data": "query_id=AAH&user=%7B%22id%22%3A123456789%2C%22first_name%22%3A%22Test%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3A%22testuser%22%7D&auth_date=1234567890&hash=test_hash"
    }


@pytest.fixture
def change_password_data():
    """Valid change password data."""
    return {
        "current_password": "OldPassword123!",
        "new_password": "NewPassword123!"
    }


# Mock external services
@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    with patch('app.services.notification.NotificationService') as mock_service:
        mock_service.notify_new_order = AsyncMock()
        mock_service.notify_order_status_change = AsyncMock()
        mock_service.notify_user_order_status = AsyncMock()
        yield mock_service


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot."""
    with patch('app.bot.bot.bot') as mock_bot:
        mock_bot.send_message = AsyncMock()
        mock_bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
        yield mock_bot