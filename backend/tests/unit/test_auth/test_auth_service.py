"""Tests for authentication service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.auth import AuthService, AuthenticationError, AuthorizationError
from app.models.user import User, UserRole
from app.utils.security import hash_password


class TestAuthService:
    """Test authentication service functionality."""

    @pytest.fixture
    async def auth_service(self, db_session):
        """Create auth service instance."""
        return AuthService(db_session)

    @pytest.fixture
    async def user_with_password(self, db_session):
        """Create user with hashed password."""
        password = "TestPassword123!"
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            role=UserRole.USER,
            password_hash=hash_password(password)
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return user, password

    async def test_authenticate_user_success(self, auth_service, user_with_password):
        """Test successful user authentication."""
        user, password = user_with_password

        with patch('app.utils.security.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = {"allowed": True, "remaining": 5}

            result = await auth_service.authenticate_user(
                username=user.username,
                password=password,
                client_ip="127.0.0.1"
            )

        assert result is not None
        assert result["user"].id == user.id
        assert "tokens" in result
        assert result["tokens"]["access_token"]
        assert result["tokens"]["refresh_token"]

    async def test_authenticate_user_invalid_username(self, auth_service):
        """Test authentication with invalid username."""
        with patch('app.utils.security.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = {"allowed": True, "remaining": 5}

            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await auth_service.authenticate_user(
                    username="nonexistent",
                    password="password",
                    client_ip="127.0.0.1"
                )

    async def test_authenticate_user_invalid_password(self, auth_service, user_with_password):
        """Test authentication with invalid password."""
        user, _ = user_with_password

        with patch('app.utils.security.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = {"allowed": True, "remaining": 5}

            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await auth_service.authenticate_user(
                    username=user.username,
                    password="wrong_password",
                    client_ip="127.0.0.1"
                )

    async def test_authenticate_user_rate_limited(self, auth_service):
        """Test authentication with rate limiting."""
        with patch('app.utils.security.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = {"allowed": False, "remaining": 0}

            with pytest.raises(AuthenticationError, match="Too many authentication attempts"):
                await auth_service.authenticate_user(
                    username="test",
                    password="password",
                    client_ip="127.0.0.1"
                )

    async def test_authenticate_user_account_locked(self, auth_service, user_with_password):
        """Test authentication with locked account."""
        user, password = user_with_password

        # Lock the user account
        user.locked_until = datetime.utcnow().replace(microsecond=0) + \
                           datetime.timedelta(minutes=30)
        await auth_service.db.commit()

        with patch('app.utils.security.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = {"allowed": True, "remaining": 5}

            with pytest.raises(AuthenticationError, match="Account is temporarily locked"):
                await auth_service.authenticate_user(
                    username=user.username,
                    password=password,
                    client_ip="127.0.0.1"
                )

    async def test_authenticate_user_inactive(self, auth_service, user_with_password):
        """Test authentication with inactive user."""
        user, password = user_with_password

        # Deactivate user
        user.is_active = False
        await auth_service.db.commit()

        with patch('app.utils.security.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = {"allowed": True, "remaining": 5}

            with pytest.raises(AuthenticationError, match="Account is disabled"):
                await auth_service.authenticate_user(
                    username=user.username,
                    password=password,
                    client_ip="127.0.0.1"
                )

    async def test_authenticate_telegram_user_new(self, auth_service):
        """Test Telegram authentication for new user."""
        telegram_data = {
            "id": 999888777,
            "first_name": "Telegram",
            "last_name": "User",
            "username": "telegramuser"
        }

        result = await auth_service.authenticate_telegram_user(telegram_data)

        assert result is not None
        assert result["user"].telegram_id == telegram_data["id"]
        assert result["user"].first_name == telegram_data["first_name"]
        assert "tokens" in result

    async def test_authenticate_telegram_user_existing(self, auth_service, test_user):
        """Test Telegram authentication for existing user."""
        telegram_data = {
            "id": test_user.telegram_id,
            "first_name": "Updated",
            "last_name": "Name",
            "username": "updated_username"
        }

        result = await auth_service.authenticate_telegram_user(telegram_data)

        assert result is not None
        assert result["user"].id == test_user.id
        # Check that user info was updated
        assert result["user"].first_name == "Updated"

    async def test_refresh_tokens_success(self, auth_service, test_user):
        """Test successful token refresh."""
        # Create initial tokens
        initial_result = await auth_service._generate_tokens(test_user)
        refresh_token = initial_result["refresh_token"]

        with patch('app.utils.jwt.jwt_manager.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
                "token_type": "bearer",
                "expires_in": 1800
            }

            result = await auth_service.refresh_tokens(refresh_token)

            assert result is not None
            assert result["access_token"] == "new_access_token"

    async def test_refresh_tokens_invalid(self, auth_service):
        """Test token refresh with invalid token."""
        with patch('app.utils.jwt.jwt_manager.refresh_access_token') as mock_refresh:
            mock_refresh.return_value = None

            with pytest.raises(AuthenticationError, match="Invalid or expired refresh token"):
                await auth_service.refresh_tokens("invalid_token")

    async def test_logout_user(self, auth_service):
        """Test user logout."""
        access_token = "test_access_token"
        refresh_token = "test_refresh_token"

        with patch('app.utils.jwt.jwt_manager.blacklist_token') as mock_blacklist:
            mock_blacklist.return_value = True

            result = await auth_service.logout_user(access_token, refresh_token)

            assert result is True
            assert mock_blacklist.call_count == 2

    async def test_logout_all_user_sessions(self, auth_service):
        """Test logout from all sessions."""
        user_id = 1

        with patch('app.utils.jwt.jwt_manager.blacklist_user_tokens') as mock_blacklist:
            mock_blacklist.return_value = 1

            result = await auth_service.logout_all_user_sessions(user_id)

            assert result is True
            mock_blacklist.assert_called_once_with(user_id)

    async def test_change_password_success(self, auth_service, user_with_password):
        """Test successful password change."""
        user, current_password = user_with_password
        new_password = "NewPassword123!"

        with patch('app.services.auth.AuthService.logout_all_user_sessions') as mock_logout:
            mock_logout.return_value = True

            result = await auth_service.change_password(
                user_id=user.id,
                current_password=current_password,
                new_password=new_password
            )

            assert result is True
            mock_logout.assert_called_once_with(user.id)

    async def test_change_password_invalid_current(self, auth_service, user_with_password):
        """Test password change with invalid current password."""
        user, _ = user_with_password

        with pytest.raises(AuthenticationError, match="Invalid current password"):
            await auth_service.change_password(
                user_id=user.id,
                current_password="wrong_password",
                new_password="NewPassword123!"
            )

    async def test_change_password_weak_new(self, auth_service, user_with_password):
        """Test password change with weak new password."""
        user, current_password = user_with_password

        with pytest.raises(AuthenticationError, match="not strong enough"):
            await auth_service.change_password(
                user_id=user.id,
                current_password=current_password,
                new_password="weak"
            )

    async def test_register_admin_user_success(self, auth_service):
        """Test successful admin user registration."""
        user_data = {
            "username": "newadmin",
            "password": "AdminPassword123!",
            "first_name": "New",
            "last_name": "Admin",
            "email": "admin@example.com",
            "role": UserRole.ADMIN
        }

        user = await auth_service.register_admin_user(**user_data)

        assert user is not None
        assert user.username == user_data["username"]
        assert user.role == UserRole.ADMIN
        assert user.password_hash is not None

    async def test_register_admin_user_duplicate_username(self, auth_service, test_user):
        """Test admin registration with duplicate username."""
        with pytest.raises(AuthenticationError, match="Username already exists"):
            await auth_service.register_admin_user(
                username=test_user.username,
                password="Password123!",
                first_name="Test",
                role=UserRole.ADMIN
            )

    async def test_register_admin_user_duplicate_email(self, auth_service, test_user):
        """Test admin registration with duplicate email."""
        with pytest.raises(AuthenticationError, match="Email already exists"):
            await auth_service.register_admin_user(
                username="newuser",
                password="Password123!",
                first_name="Test",
                email=test_user.email,
                role=UserRole.ADMIN
            )

    async def test_get_current_user_valid_token(self, auth_service, test_user):
        """Test getting current user with valid token."""
        tokens = await auth_service._generate_tokens(test_user)
        access_token = tokens["access_token"]

        user = await auth_service.get_current_user(access_token)

        assert user is not None
        assert user.id == test_user.id

    async def test_get_current_user_invalid_token(self, auth_service):
        """Test getting current user with invalid token."""
        user = await auth_service.get_current_user("invalid_token")

        assert user is None

    async def test_check_permission_admin(self, auth_service, test_admin_user):
        """Test permission check for admin user."""
        result = await auth_service.check_permission(test_admin_user, "any:permission")

        assert result is True  # Admin has all permissions

    async def test_check_permission_user(self, auth_service, test_user):
        """Test permission check for regular user."""
        # User should have basic permissions
        result = await auth_service.check_permission(test_user, "product:view")
        assert result is True

        # User should not have admin permissions
        result = await auth_service.check_permission(test_user, "admin:access")
        assert result is False

    async def test_require_permission_success(self, auth_service, test_admin_user):
        """Test require permission with sufficient permissions."""
        # Should not raise exception
        await auth_service.require_permission(test_admin_user, "any:permission")

    async def test_require_permission_failure(self, auth_service, test_user):
        """Test require permission with insufficient permissions."""
        with pytest.raises(AuthorizationError, match="Permission required"):
            await auth_service.require_permission(test_user, "admin:access")