"""Tests for authentication middleware."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.middleware.auth import AuthMiddleware
from app.models.user import User, UserRole
from app.services.auth import AuthenticationError


class TestAuthMiddleware:
    """Test authentication middleware."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request object."""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        return request

    @pytest.fixture
    def mock_credentials(self):
        """Create mock HTTP credentials."""
        return HTTPAuthorizationCredentials(
            scheme="bearer",
            credentials="valid_token_123"
        )

    async def test_get_current_user_valid_token(self, mock_request, mock_credentials, db_session, test_user):
        """Test get_current_user with valid token."""
        with patch('app.services.auth.AuthService.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user

            user = await AuthMiddleware.get_current_user(
                request=mock_request,
                credentials=mock_credentials,
                db=db_session
            )

            assert user == test_user
            assert mock_request.state.user_id == test_user.id
            assert mock_request.state.user_role == test_user.role.value

    async def test_get_current_user_no_credentials(self, mock_request, db_session):
        """Test get_current_user without credentials."""
        user = await AuthMiddleware.get_current_user(
            request=mock_request,
            credentials=None,
            db=db_session
        )

        assert user is None

    async def test_get_current_user_invalid_token(self, mock_request, mock_credentials, db_session):
        """Test get_current_user with invalid token."""
        with patch('app.services.auth.AuthService.get_current_user') as mock_get_user:
            mock_get_user.return_value = None

            user = await AuthMiddleware.get_current_user(
                request=mock_request,
                credentials=mock_credentials,
                db=db_session
            )

            assert user is None

    async def test_require_authenticated_user_success(self, mock_request, mock_credentials, db_session, test_user):
        """Test require_authenticated_user with valid user."""
        with patch('app.services.auth.AuthService.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user

            user = await AuthMiddleware.require_authenticated_user(
                request=mock_request,
                credentials=mock_credentials,
                db=db_session
            )

            assert user == test_user

    async def test_require_authenticated_user_no_credentials(self, mock_request, db_session):
        """Test require_authenticated_user without credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await AuthMiddleware.require_authenticated_user(
                request=mock_request,
                credentials=None,
                db=db_session
            )

        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)

    async def test_require_authenticated_user_invalid_token(self, mock_request, mock_credentials, db_session):
        """Test require_authenticated_user with invalid token."""
        with patch('app.services.auth.AuthService.get_current_user') as mock_get_user:
            mock_get_user.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await AuthMiddleware.require_authenticated_user(
                    request=mock_request,
                    credentials=mock_credentials,
                    db=db_session
                )

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in str(exc_info.value.detail)

    async def test_require_roles_success(self, mock_request, db_session, test_admin_user):
        """Test require_roles with sufficient role."""
        with patch('app.middleware.auth.AuthMiddleware.require_authenticated_user') as mock_auth:
            mock_auth.return_value = test_admin_user

            role_dependency = AuthMiddleware.require_roles([UserRole.ADMIN])
            user = await role_dependency(
                request=mock_request,
                user=test_admin_user,
                db=db_session
            )

            assert user == test_admin_user

    async def test_require_roles_insufficient(self, mock_request, db_session, test_user):
        """Test require_roles with insufficient role."""
        with patch('app.middleware.auth.AuthMiddleware.require_authenticated_user') as mock_auth:
            mock_auth.return_value = test_user

            role_dependency = AuthMiddleware.require_roles([UserRole.ADMIN])

            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(
                    request=mock_request,
                    user=test_user,
                    db=db_session
                )

            assert exc_info.value.status_code == 403
            assert "Access denied" in str(exc_info.value.detail)

    async def test_require_permissions_success(self, mock_request, db_session, test_admin_user):
        """Test require_permissions with sufficient permissions."""
        with patch('app.middleware.auth.AuthMiddleware.require_authenticated_user') as mock_auth:
            mock_auth.return_value = test_admin_user

            with patch('app.services.auth.AuthService.check_permission') as mock_check:
                mock_check.return_value = True

                permission_dependency = AuthMiddleware.require_permissions(["admin:access"])
                user = await permission_dependency(
                    request=mock_request,
                    user=test_admin_user,
                    db=db_session
                )

                assert user == test_admin_user

    async def test_require_permissions_insufficient(self, mock_request, db_session, test_user):
        """Test require_permissions with insufficient permissions."""
        with patch('app.middleware.auth.AuthMiddleware.require_authenticated_user') as mock_auth:
            mock_auth.return_value = test_user

            with patch('app.services.auth.AuthService.check_permission') as mock_check:
                mock_check.return_value = False

                permission_dependency = AuthMiddleware.require_permissions(["admin:access"])

                with pytest.raises(HTTPException) as exc_info:
                    await permission_dependency(
                        request=mock_request,
                        user=test_user,
                        db=db_session
                    )

                assert exc_info.value.status_code == 403
                assert "Access denied" in str(exc_info.value.detail)

    async def test_require_admin_user_success(self, mock_request, db_session, test_admin_user):
        """Test require_admin_user with admin user."""
        user = await AuthMiddleware.require_admin_user(
            request=mock_request,
            user=test_admin_user,
            db=db_session
        )

        assert user == test_admin_user

    async def test_require_admin_user_failure(self, mock_request, db_session, test_user):
        """Test require_admin_user with non-admin user."""
        with pytest.raises(HTTPException) as exc_info:
            await AuthMiddleware.require_admin_user(
                request=mock_request,
                user=test_user,
                db=db_session
            )

        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)

    async def test_require_manager_or_admin_with_admin(self, mock_request, db_session, test_admin_user):
        """Test require_manager_or_admin with admin user."""
        user = await AuthMiddleware.require_manager_or_admin(
            request=mock_request,
            user=test_admin_user,
            db=db_session
        )

        assert user == test_admin_user

    async def test_require_manager_or_admin_with_manager(self, mock_request, db_session, test_manager_user):
        """Test require_manager_or_admin with manager user."""
        user = await AuthMiddleware.require_manager_or_admin(
            request=mock_request,
            user=test_manager_user,
            db=db_session
        )

        assert user == test_manager_user

    async def test_require_manager_or_admin_with_user(self, mock_request, db_session, test_user):
        """Test require_manager_or_admin with regular user."""
        with pytest.raises(HTTPException) as exc_info:
            await AuthMiddleware.require_manager_or_admin(
                request=mock_request,
                user=test_user,
                db=db_session
            )

        assert exc_info.value.status_code == 403
        assert "Manager or admin access required" in str(exc_info.value.detail)

    async def test_rate_limit_dependency_allowed(self, mock_request):
        """Test rate limit dependency when requests are allowed."""
        with patch('app.utils.security.rate_limiter.is_allowed') as mock_rate_limit:
            mock_rate_limit.return_value = {
                "allowed": True,
                "remaining": 5,
                "reset_time": "2024-01-01T12:00:00"
            }

            rate_limit_dep = AuthMiddleware.rate_limit_dependency()

            # Should not raise exception
            await rate_limit_dep(mock_request)

            assert hasattr(mock_request.state, 'rate_limit_remaining')
            assert mock_request.state.rate_limit_remaining == 5

    async def test_rate_limit_dependency_exceeded(self, mock_request):
        """Test rate limit dependency when rate limit is exceeded."""
        with patch('app.utils.security.rate_limiter.is_allowed') as mock_rate_limit:
            mock_rate_limit.return_value = {
                "allowed": False,
                "remaining": 0,
                "reset_time": "2024-01-01T12:00:00"
            }

            rate_limit_dep = AuthMiddleware.rate_limit_dependency()

            with pytest.raises(HTTPException) as exc_info:
                await rate_limit_dep(mock_request)

            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value.detail)

    def test_rate_limit_custom_parameters(self, mock_request):
        """Test rate limit dependency with custom parameters."""
        custom_key_func = lambda req: "custom_key"
        rate_limit_dep = AuthMiddleware.rate_limit_dependency(
            max_attempts=10,
            window_minutes=5,
            key_func=custom_key_func
        )

        with patch('app.utils.security.rate_limiter.is_allowed') as mock_rate_limit:
            mock_rate_limit.return_value = {"allowed": True, "remaining": 5}

            # Should use custom parameters
            asyncio.run(rate_limit_dep(mock_request))

            mock_rate_limit.assert_called_once_with(
                "api:custom_key",
                max_attempts=10,
                window_minutes=5
            )