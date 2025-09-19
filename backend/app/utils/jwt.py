"""JWT token utilities."""

import jwt
import redis
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set
from uuid import uuid4

from app.config import settings


class JWTManager:
    """JWT token manager with blacklisting support."""

    def __init__(self):
        """Initialize JWT manager."""
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = getattr(settings, 'refresh_token_expire_days', 30)

        # Redis for token blacklisting
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)

        # Add standard claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "jti": str(uuid4())  # JWT ID for blacklisting
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": str(uuid4())
        })

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Check token type
            if payload.get("type") != token_type:
                return None

            # Check if token is blacklisted
            if self.is_token_blacklisted(payload.get("jti")):
                return None

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Don't verify expiration for blacklisting
            )

            jti = payload.get("jti")
            if not jti:
                return False

            # Calculate remaining time until token expiry
            exp = payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                ttl = int((exp_datetime - datetime.now(timezone.utc)).total_seconds())

                # Only blacklist if token hasn't expired
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{jti}", ttl, "1")

            return True

        except jwt.JWTError:
            return False

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        if not jti:
            return False
        return self.redis_client.exists(f"blacklist:{jti}")

    def blacklist_user_tokens(self, user_id: int) -> int:
        """Blacklist all tokens for a specific user."""
        # This would require keeping track of user tokens
        # For simplicity, we'll use a user-specific blacklist
        blacklist_key = f"user_blacklist:{user_id}"
        current_time = datetime.now(timezone.utc).timestamp()

        # Set user blacklist with long expiration
        self.redis_client.setex(blacklist_key, 86400 * 30, str(int(current_time)))  # 30 days
        return 1

    def is_user_blacklisted(self, user_id: int, token_iat: float) -> bool:
        """Check if user tokens issued before a certain time are blacklisted."""
        blacklist_key = f"user_blacklist:{user_id}"
        blacklist_time = self.redis_client.get(blacklist_key)

        if blacklist_time:
            return token_iat < float(blacklist_time)
        return False

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Create new access token using refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        # Extract user data
        user_data = {
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "telegram_id": payload.get("telegram_id")
        }

        # Create new tokens
        new_access_token = self.create_access_token(user_data)
        new_refresh_token = self.create_refresh_token(user_data)

        # Blacklist old refresh token
        self.blacklist_token(refresh_token)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token information without verification."""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        except jwt.JWTError:
            return None

    def cleanup_expired_blacklist(self) -> int:
        """Clean up expired blacklist entries (called by scheduler)."""
        # Redis automatically handles TTL, but we can clean up user blacklists
        pattern = "user_blacklist:*"
        keys = self.redis_client.keys(pattern)
        cleaned = 0

        current_time = datetime.now(timezone.utc).timestamp()

        for key in keys:
            blacklist_time = self.redis_client.get(key)
            if blacklist_time:
                # Remove user blacklists older than 30 days
                if current_time - float(blacklist_time) > 86400 * 30:
                    self.redis_client.delete(key)
                    cleaned += 1

        return cleaned


# Global JWT manager instance
jwt_manager = JWTManager()


# Convenience functions
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    return jwt_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token."""
    return jwt_manager.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify token."""
    return jwt_manager.verify_token(token, token_type)


def blacklist_token(token: str) -> bool:
    """Blacklist token."""
    return jwt_manager.blacklist_token(token)


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Refresh access token."""
    return jwt_manager.refresh_access_token(refresh_token)