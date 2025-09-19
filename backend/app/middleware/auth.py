"""Authentication middleware and dependencies."""

import logging
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.user import User, UserRole
from app.services.auth import AuthService, AuthenticationError, AuthorizationError
from app.utils.security import rate_limiter


logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Authentication middleware for FastAPI dependencies."""

    @staticmethod
    async def get_current_user(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_async_session)
    ) -> Optional[User]:
        """
        Get current authenticated user (optional).
        Returns None if no valid token provided.
        """
        if not credentials:
            return None

        auth_service = AuthService(db)

        try:
            user = await auth_service.get_current_user(credentials.credentials)
            if user:
                # Add user info to request state for logging
                request.state.user_id = user.id
                request.state.user_role = user.role.value
            return user
        except Exception as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return None

    @staticmethod
    async def require_authenticated_user(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: AsyncSession = Depends(get_async_session)
    ) -> User:
        """
        Require authenticated user.
        Raises HTTPException if not authenticated.
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        auth_service = AuthService(db)

        try:
            user = await auth_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Add user info to request state
            request.state.user_id = user.id
            request.state.user_role = user.role.value

            return user

        except AuthenticationError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )

    @staticmethod
    def require_roles(allowed_roles: List[UserRole]):
        """
        Create dependency that requires specific roles.

        Args:
            allowed_roles: List of allowed user roles

        Returns:
            FastAPI dependency function
        """
        async def role_dependency(
            request: Request,
            user: User = Depends(AuthMiddleware.require_authenticated_user),
            db: AsyncSession = Depends(get_async_session)
        ) -> User:
            if user.role not in allowed_roles:
                logger.warning(
                    f"User {user.id} with role {user.role.value} "
                    f"attempted to access endpoint requiring {[r.value for r in allowed_roles]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
                )
            return user

        return role_dependency

    @staticmethod
    def require_permissions(required_permissions: List[str]):
        """
        Create dependency that requires specific permissions.

        Args:
            required_permissions: List of required permissions

        Returns:
            FastAPI dependency function
        """
        async def permission_dependency(
            request: Request,
            user: User = Depends(AuthMiddleware.require_authenticated_user),
            db: AsyncSession = Depends(get_async_session)
        ) -> User:
            auth_service = AuthService(db)

            # Check all required permissions
            for permission in required_permissions:
                if not await auth_service.check_permission(user, permission):
                    logger.warning(
                        f"User {user.id} with role {user.role.value} "
                        f"attempted to access endpoint requiring permission: {permission}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required permission: {permission}"
                    )

            return user

        return permission_dependency

    @staticmethod
    async def require_admin_user(
        request: Request,
        user: User = Depends(require_authenticated_user),
        db: AsyncSession = Depends(get_async_session)
    ) -> User:
        """
        Require admin user.
        """
        if user.role != UserRole.ADMIN:
            logger.warning(f"Non-admin user {user.id} attempted to access admin endpoint")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user

    @staticmethod
    async def require_manager_or_admin(
        request: Request,
        user: User = Depends(require_authenticated_user),
        db: AsyncSession = Depends(get_async_session)
    ) -> User:
        """
        Require manager or admin user.
        """
        if user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            logger.warning(f"User {user.id} with insufficient privileges attempted to access manager endpoint")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager or admin access required"
            )
        return user

    @staticmethod
    def rate_limit_dependency(
        max_attempts: int = 60,
        window_minutes: int = 1,
        key_func=lambda request: request.client.host
    ):
        """
        Create rate limiting dependency.

        Args:
            max_attempts: Maximum attempts per window
            window_minutes: Time window in minutes
            key_func: Function to extract rate limit key from request

        Returns:
            FastAPI dependency function
        """
        async def rate_limit_check(request: Request):
            key = key_func(request)
            if not key:
                return

            check = rate_limiter.is_allowed(
                f"api:{key}",
                max_attempts=max_attempts,
                window_minutes=window_minutes
            )

            if not check["allowed"]:
                logger.warning(f"Rate limit exceeded for key: {key}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(window_minutes * 60),
                        "X-RateLimit-Remaining": str(check["remaining"])
                    }
                )

            # Add rate limit info to response headers
            request.state.rate_limit_remaining = check["remaining"]
            request.state.rate_limit_reset = check["reset_time"].isoformat()

        return rate_limit_check


# Convenience dependency instances
get_current_user = AuthMiddleware.get_current_user
require_authenticated_user = AuthMiddleware.require_authenticated_user
require_admin_user = AuthMiddleware.require_admin_user
require_manager_or_admin = AuthMiddleware.require_manager_or_admin

# Role-based dependencies
require_admin = AuthMiddleware.require_roles([UserRole.ADMIN])
require_manager = AuthMiddleware.require_roles([UserRole.ADMIN, UserRole.MANAGER])
require_user = AuthMiddleware.require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.USER])

# Permission-based dependencies
require_product_write = AuthMiddleware.require_permissions(["product:create", "product:update", "product:delete"])
require_order_read = AuthMiddleware.require_permissions(["order:view_all"])
require_order_write = AuthMiddleware.require_permissions(["order:create", "order:update"])

# Rate limiting dependencies
auth_rate_limit = AuthMiddleware.rate_limit_dependency(
    max_attempts=10,
    window_minutes=15,
    key_func=lambda req: req.client.host
)

api_rate_limit = AuthMiddleware.rate_limit_dependency(
    max_attempts=100,
    window_minutes=1,
    key_func=lambda req: req.client.host
)

strict_rate_limit = AuthMiddleware.rate_limit_dependency(
    max_attempts=5,
    window_minutes=5,
    key_func=lambda req: req.client.host
)


class SecurityHeadersMiddleware:
    """Add security headers to responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))

                # Add security headers
                security_headers = {
                    b"X-Content-Type-Options": b"nosniff",
                    b"X-Frame-Options": b"DENY",
                    b"X-XSS-Protection": b"1; mode=block",
                    b"Strict-Transport-Security": b"max-age=31536000; includeSubDomains",
                    b"Referrer-Policy": b"strict-origin-when-cross-origin",
                    b"Content-Security-Policy": b"default-src 'self'",
                }

                for header, value in security_headers.items():
                    if header not in headers:
                        headers[header] = value

                # Convert headers back to list format
                message["headers"] = [(k, v) for k, v in headers.items()]

            await send(message)

        await self.app(scope, receive, send_wrapper)


# Audit logging middleware
class AuditLogMiddleware:
    """Audit logging middleware for authentication events."""

    def __init__(self, app):
        self.app = app
        self.audit_logger = logging.getLogger("audit")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Log authentication events
                await self._log_auth_event(request, message.get("status", 500))

            await send(message)

        await self.app(scope, receive, send_wrapper)

    async def _log_auth_event(self, request: Request, status_code: int):
        """Log authentication-related events."""
        path = request.url.path

        # Log auth endpoints
        if path.startswith("/api/auth/"):
            user_id = getattr(request.state, "user_id", None)
            user_role = getattr(request.state, "user_role", None)
            client_ip = request.client.host

            self.audit_logger.info(
                f"AUTH {request.method} {path} - "
                f"Status: {status_code} - "
                f"IP: {client_ip} - "
                f"User: {user_id} - "
                f"Role: {user_role}"
            )

        # Log failed authorization attempts
        elif status_code in [401, 403]:
            user_id = getattr(request.state, "user_id", None)
            client_ip = request.client.host

            self.audit_logger.warning(
                f"ACCESS_DENIED {request.method} {path} - "
                f"Status: {status_code} - "
                f"IP: {client_ip} - "
                f"User: {user_id}"
            )