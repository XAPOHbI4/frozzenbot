"""Authentication service with comprehensive business logic."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.utils.jwt import jwt_manager, create_access_token, create_refresh_token
from app.utils.security import (
    hash_password, verify_password, validate_password,
    security_utils, rate_limiter
)
from app.config import settings


logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


class AuthorizationError(Exception):
    """Custom authorization error."""
    pass


class AuthService:
    """Authentication service with comprehensive business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize authentication service."""
        self.db = db
        self.max_failed_attempts = 5
        self.lockout_minutes = 30

    async def authenticate_user(self, username: str, password: str, client_ip: str = None) -> Dict[str, Any]:
        """
        Authenticate user with comprehensive security checks.

        Args:
            username: Username or email
            password: Plain password
            client_ip: Client IP for rate limiting

        Returns:
            Dict with authentication result

        Raises:
            AuthenticationError: Authentication failed
        """
        # Rate limiting check
        if client_ip:
            rate_check = rate_limiter.is_allowed(
                f"auth:{client_ip}",
                max_attempts=10,
                window_minutes=15
            )
            if not rate_check["allowed"]:
                logger.warning(f"Rate limit exceeded for IP {client_ip}")
                raise AuthenticationError("Too many authentication attempts. Please try again later.")

        # Find user by username or email
        user = await self._find_user_by_credentials(username)
        if not user:
            logger.warning(f"Authentication attempt for non-existent user: {username}")

            # Record failed attempt for rate limiting
            if client_ip:
                rate_limiter.record_attempt(f"auth:{client_ip}")

            raise AuthenticationError("Invalid credentials")

        # Check if user is locked
        if user.is_locked:
            logger.warning(f"Authentication attempt for locked user: {user.id}")
            raise AuthenticationError("Account is temporarily locked due to too many failed attempts")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Authentication attempt for inactive user: {user.id}")
            raise AuthenticationError("Account is disabled")

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            await self._handle_failed_login(user, client_ip)
            logger.warning(f"Invalid password for user: {user.id}")
            raise AuthenticationError("Invalid credentials")

        # Successful authentication
        await self._handle_successful_login(user)
        logger.info(f"Successful authentication for user: {user.id}")

        # Generate tokens
        tokens = await self._generate_tokens(user)

        return {
            "user": user,
            "tokens": tokens,
            "message": "Authentication successful"
        }

    async def authenticate_telegram_user(self, telegram_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate user via Telegram WebApp initData.

        Args:
            telegram_data: Parsed Telegram user data

        Returns:
            Dict with authentication result
        """
        telegram_id = telegram_data.get("id")
        if not telegram_id:
            raise AuthenticationError("Invalid Telegram data")

        # Find or create user
        user = await self._find_user_by_telegram_id(telegram_id)
        if not user:
            # Create new user from Telegram data
            user = await self._create_telegram_user(telegram_data)

        # Update user info from Telegram
        await self._update_user_from_telegram(user, telegram_data)

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Telegram authentication attempt for inactive user: {user.id}")
            raise AuthenticationError("Account is disabled")

        # Update last login
        user.update_last_login()
        await self.db.commit()

        logger.info(f"Successful Telegram authentication for user: {user.id}")

        # Generate tokens
        tokens = await self._generate_tokens(user)

        return {
            "user": user,
            "tokens": tokens,
            "message": "Telegram authentication successful"
        }

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New tokens

        Raises:
            AuthenticationError: Refresh failed
        """
        tokens = jwt_manager.refresh_access_token(refresh_token)
        if not tokens:
            logger.warning("Invalid refresh token used")
            raise AuthenticationError("Invalid or expired refresh token")

        # Verify user still exists and is active
        payload = jwt_manager.verify_token(tokens["access_token"])
        if not payload:
            raise AuthenticationError("Failed to generate valid tokens")

        user = await self._find_user_by_id(payload.get("user_id"))
        if not user or not user.is_active:
            # Blacklist the new tokens
            jwt_manager.blacklist_token(tokens["access_token"])
            jwt_manager.blacklist_token(tokens["refresh_token"])
            raise AuthenticationError("User account is not available")

        logger.info(f"Tokens refreshed for user: {user.id}")
        return tokens

    async def logout_user(self, access_token: str, refresh_token: Optional[str] = None) -> bool:
        """
        Logout user by blacklisting tokens.

        Args:
            access_token: Access token to blacklist
            refresh_token: Optional refresh token to blacklist

        Returns:
            Success status
        """
        success = True

        # Blacklist access token
        if not jwt_manager.blacklist_token(access_token):
            success = False

        # Blacklist refresh token if provided
        if refresh_token and not jwt_manager.blacklist_token(refresh_token):
            success = False

        if success:
            # Get user info for logging
            payload = jwt_manager.get_token_info(access_token)
            if payload:
                logger.info(f"User logged out: {payload.get('user_id')}")

        return success

    async def logout_all_user_sessions(self, user_id: int) -> bool:
        """
        Logout user from all sessions by blacklisting all their tokens.

        Args:
            user_id: User ID

        Returns:
            Success status
        """
        jwt_manager.blacklist_user_tokens(user_id)
        logger.info(f"All sessions terminated for user: {user_id}")
        return True

    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password with validation.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Success status

        Raises:
            AuthenticationError: Password change failed
        """
        user = await self._find_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        # Verify current password
        if not user.password_hash or not verify_password(current_password, user.password_hash):
            logger.warning(f"Invalid current password for user: {user.id}")
            raise AuthenticationError("Invalid current password")

        # Validate new password
        validation = validate_password(new_password)
        if not validation["valid"]:
            raise AuthenticationError(f"New password is not strong enough: {', '.join(validation['errors'])}")

        # Hash new password
        new_hash = hash_password(new_password)

        # Update password
        user.password_hash = new_hash
        user.password_changed_at = datetime.utcnow()
        await self.db.commit()

        # Blacklist all existing sessions
        await self.logout_all_user_sessions(user.id)

        logger.info(f"Password changed for user: {user.id}")
        return True

    async def register_admin_user(
        self,
        username: str,
        password: str,
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        role: UserRole = UserRole.MANAGER
    ) -> User:
        """
        Register new admin/manager user.

        Args:
            username: Username
            password: Plain password
            first_name: First name
            last_name: Last name
            email: Email address
            role: User role

        Returns:
            Created user

        Raises:
            AuthenticationError: Registration failed
        """
        # Validate inputs
        if not username or len(username) < 3:
            raise AuthenticationError("Username must be at least 3 characters long")

        if email and not security_utils.validate_email(email):
            raise AuthenticationError("Invalid email format")

        # Check if username already exists
        existing_user = await self._find_user_by_credentials(username)
        if existing_user:
            raise AuthenticationError("Username already exists")

        # Check if email already exists
        if email:
            existing_email = await self._find_user_by_email(email)
            if existing_email:
                raise AuthenticationError("Email already exists")

        # Validate password
        validation = validate_password(password)
        if not validation["valid"]:
            raise AuthenticationError(f"Password is not strong enough: {', '.join(validation['errors'])}")

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user = User(
            telegram_id=0,  # Will be updated when user connects Telegram
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
            role=role,
            is_admin=role == UserRole.ADMIN,
            password_changed_at=datetime.utcnow()
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"New admin user registered: {user.id} ({username})")
        return user

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from token.

        Args:
            token: Access token

        Returns:
            User if valid, None otherwise
        """
        payload = jwt_manager.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        # Check user blacklist
        token_iat = payload.get("iat", 0)
        if jwt_manager.is_user_blacklisted(user_id, token_iat):
            return None

        user = await self._find_user_by_id(user_id)
        if not user or not user.is_active:
            return None

        return user

    async def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has specific permission.

        Args:
            user: User object
            permission: Permission string

        Returns:
            True if user has permission
        """
        return user.has_permission(permission)

    async def require_permission(self, user: User, permission: str) -> None:
        """
        Require user to have specific permission.

        Args:
            user: User object
            permission: Permission string

        Raises:
            AuthorizationError: User doesn't have permission
        """
        if not await self.check_permission(user, permission):
            raise AuthorizationError(f"Permission required: {permission}")

    # Private methods
    async def _find_user_by_credentials(self, username: str) -> Optional[User]:
        """Find user by username or email."""
        stmt = select(User).where(
            (User.username == username) | (User.email == username)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Find user by Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_user_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _generate_tokens(self, user: User) -> Dict[str, Any]:
        """Generate access and refresh tokens for user."""
        token_data = {
            "user_id": user.id,
            "role": user.role.value,
            "telegram_id": user.telegram_id,
            "username": user.username
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }

    async def _handle_failed_login(self, user: User, client_ip: Optional[str] = None):
        """Handle failed login attempt."""
        user.increment_failed_attempts(self.max_failed_attempts, self.lockout_minutes)
        await self.db.commit()

        if client_ip:
            rate_limiter.record_attempt(f"auth:{client_ip}")

    async def _handle_successful_login(self, user: User):
        """Handle successful login."""
        user.reset_failed_attempts()
        user.update_last_login()
        await self.db.commit()

    async def _create_telegram_user(self, telegram_data: Dict[str, Any]) -> User:
        """Create new user from Telegram data."""
        user = User(
            telegram_id=telegram_data["id"],
            username=telegram_data.get("username"),
            first_name=telegram_data["first_name"],
            last_name=telegram_data.get("last_name"),
            role=UserRole.USER
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"New Telegram user created: {user.id} (telegram_id: {user.telegram_id})")
        return user

    async def _update_user_from_telegram(self, user: User, telegram_data: Dict[str, Any]):
        """Update user information from Telegram data."""
        updated = False

        # Update basic info if changed
        if user.username != telegram_data.get("username"):
            user.username = telegram_data.get("username")
            updated = True

        if user.first_name != telegram_data["first_name"]:
            user.first_name = telegram_data["first_name"]
            updated = True

        if user.last_name != telegram_data.get("last_name"):
            user.last_name = telegram_data.get("last_name")
            updated = True

        if updated:
            await self.db.commit()


# Convenience functions for dependency injection
async def get_auth_service(db: AsyncSession) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)