"""Tests for JWT utilities."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from app.utils.jwt import JWTManager, jwt_manager


class TestJWTManager:
    """Test JWT Manager functionality."""

    @pytest.fixture
    def jwt_mgr(self):
        """Create JWT manager instance for testing."""
        return JWTManager()

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for token generation."""
        return {
            "user_id": 1,
            "role": "admin",
            "telegram_id": 123456789,
            "username": "testuser"
        }

    def test_create_access_token(self, jwt_mgr, sample_user_data):
        """Test access token creation."""
        token = jwt_mgr.create_access_token(sample_user_data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are quite long

    def test_create_refresh_token(self, jwt_mgr, sample_user_data):
        """Test refresh token creation."""
        token = jwt_mgr.create_refresh_token(sample_user_data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_access_token_valid(self, jwt_mgr, sample_user_data):
        """Test verification of valid access token."""
        token = jwt_mgr.create_access_token(sample_user_data)
        payload = jwt_mgr.verify_token(token, "access")

        assert payload is not None
        assert payload["user_id"] == sample_user_data["user_id"]
        assert payload["role"] == sample_user_data["role"]
        assert payload["type"] == "access"

    def test_verify_refresh_token_valid(self, jwt_mgr, sample_user_data):
        """Test verification of valid refresh token."""
        token = jwt_mgr.create_refresh_token(sample_user_data)
        payload = jwt_mgr.verify_token(token, "refresh")

        assert payload is not None
        assert payload["user_id"] == sample_user_data["user_id"]
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self, jwt_mgr, sample_user_data):
        """Test verification fails with wrong token type."""
        access_token = jwt_mgr.create_access_token(sample_user_data)

        # Try to verify access token as refresh token
        payload = jwt_mgr.verify_token(access_token, "refresh")
        assert payload is None

    def test_verify_invalid_token(self, jwt_mgr):
        """Test verification of invalid token."""
        invalid_token = "invalid.jwt.token"
        payload = jwt_mgr.verify_token(invalid_token)

        assert payload is None

    def test_verify_expired_token(self, jwt_mgr, sample_user_data):
        """Test verification of expired token."""
        # Create token with very short expiration
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = jwt_mgr.create_access_token(sample_user_data, expired_delta)

        payload = jwt_mgr.verify_token(token)
        assert payload is None

    @patch('app.utils.jwt.jwt_manager.redis_client')
    def test_blacklist_token(self, mock_redis, jwt_mgr, sample_user_data):
        """Test token blacklisting."""
        mock_redis.setex.return_value = True

        token = jwt_mgr.create_access_token(sample_user_data)
        result = jwt_mgr.blacklist_token(token)

        assert result is True
        mock_redis.setex.assert_called_once()

    @patch('app.utils.jwt.jwt_manager.redis_client')
    def test_is_token_blacklisted(self, mock_redis, jwt_mgr):
        """Test checking if token is blacklisted."""
        mock_redis.exists.return_value = True

        result = jwt_mgr.is_token_blacklisted("some-jti-id")

        assert result is True
        mock_redis.exists.assert_called_once_with("blacklist:some-jti-id")

    @patch('app.utils.jwt.jwt_manager.redis_client')
    def test_blacklist_user_tokens(self, mock_redis, jwt_mgr):
        """Test blacklisting all user tokens."""
        mock_redis.setex.return_value = True

        result = jwt_mgr.blacklist_user_tokens(1)

        assert result == 1
        mock_redis.setex.assert_called_once()

    @patch('app.utils.jwt.jwt_manager.redis_client')
    def test_refresh_access_token_success(self, mock_redis, jwt_mgr, sample_user_data):
        """Test successful token refresh."""
        # Mock Redis to not blacklist tokens during test
        mock_redis.exists.return_value = False
        mock_redis.setex.return_value = True

        # Create refresh token
        refresh_token = jwt_mgr.create_refresh_token(sample_user_data)

        # Refresh tokens
        result = jwt_mgr.refresh_access_token(refresh_token)

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert "token_type" in result
        assert "expires_in" in result

    def test_refresh_access_token_invalid(self, jwt_mgr):
        """Test token refresh with invalid refresh token."""
        invalid_token = "invalid.refresh.token"

        result = jwt_mgr.refresh_access_token(invalid_token)

        assert result is None

    def test_get_token_info(self, jwt_mgr, sample_user_data):
        """Test getting token information without verification."""
        token = jwt_mgr.create_access_token(sample_user_data)

        info = jwt_mgr.get_token_info(token)

        assert info is not None
        assert info["user_id"] == sample_user_data["user_id"]
        assert info["type"] == "access"

    def test_token_contains_required_claims(self, jwt_mgr, sample_user_data):
        """Test that tokens contain all required claims."""
        token = jwt_mgr.create_access_token(sample_user_data)
        payload = jwt_mgr.verify_token(token)

        # Check required claims
        required_claims = ["exp", "iat", "type", "jti", "user_id", "role"]
        for claim in required_claims:
            assert claim in payload

    def test_token_expiration_time(self, jwt_mgr, sample_user_data):
        """Test token expiration time is set correctly."""
        before_creation = datetime.now(timezone.utc)
        token = jwt_mgr.create_access_token(sample_user_data)
        after_creation = datetime.now(timezone.utc)

        payload = jwt_mgr.verify_token(token)
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        # Check expiration is roughly access_token_expire_minutes from creation
        expected_exp = before_creation + timedelta(minutes=jwt_mgr.access_token_expire_minutes)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())

        assert time_diff < 5  # Should be within 5 seconds