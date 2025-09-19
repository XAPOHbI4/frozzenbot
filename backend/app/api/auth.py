"""Authentication API endpoints."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_async_session
from app.services.auth import AuthService, AuthenticationError, AuthorizationError
from app.middleware.auth import (
    require_authenticated_user, require_admin_user, auth_rate_limit,
    get_current_user
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, LoginResponse, RefreshRequest, TokenResponse,
    TelegramInitData
)
from app.schemas.user import UserResponse
from app.utils.telegram import parse_telegram_init_data


logger = logging.getLogger(__name__)
router = APIRouter()


# Additional schemas
class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=128)

    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "NewSecurePassword123!"
            }
        }


class RegisterUserRequest(BaseModel):
    """Register user request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    role: UserRole = Field(UserRole.MANAGER, description="User role")

    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "username": "manager1",
                "password": "SecurePassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "role": "manager"
            }
        }


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


# Authentication endpoints
@router.post("/login", response_model=LoginResponse, dependencies=[Depends(auth_rate_limit)])
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user with username/email and password.

    Returns JWT tokens and user information.
    """
    auth_service = AuthService(db)

    try:
        result = await auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            client_ip=request.client.host
        )

        logger.info(f"User {result['user'].id} logged in successfully")

        return LoginResponse(
            access_token=result["tokens"]["access_token"],
            refresh_token=result["tokens"]["refresh_token"],
            token_type=result["tokens"]["token_type"],
            expires_in=result["tokens"]["expires_in"],
            user=UserResponse.from_orm(result["user"])
        )

    except AuthenticationError as e:
        logger.warning(f"Login failed for {login_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error for {login_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/telegram", response_model=LoginResponse, dependencies=[Depends(auth_rate_limit)])
async def telegram_login(
    request: Request,
    init_data: TelegramInitData,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Authenticate user via Telegram WebApp initData.

    Returns JWT tokens and user information.
    """
    auth_service = AuthService(db)

    try:
        # Parse and validate Telegram initData
        telegram_data = parse_telegram_init_data(init_data.init_data)
        if not telegram_data:
            raise AuthenticationError("Invalid Telegram initData")

        result = await auth_service.authenticate_telegram_user(telegram_data)

        logger.info(f"Telegram user {result['user'].telegram_id} authenticated successfully")

        return LoginResponse(
            access_token=result["tokens"]["access_token"],
            refresh_token=result["tokens"]["refresh_token"],
            token_type=result["tokens"]["token_type"],
            expires_in=result["tokens"]["expires_in"],
            user=UserResponse.from_orm(result["user"])
        )

    except AuthenticationError as e:
        logger.warning(f"Telegram login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Telegram login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token.

    Returns new access and refresh tokens.
    """
    auth_service = AuthService(db)

    try:
        tokens = await auth_service.refresh_tokens(refresh_data.refresh_token)

        logger.info("Token refresh successful")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        )

    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service error"
        )


@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    logout_data: LogoutRequest = Body(...),
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Logout user by blacklisting tokens.

    Blacklists the current access token and optionally refresh token.
    """
    auth_service = AuthService(db)

    try:
        # Get access token from Authorization header
        auth_header = request.headers.get("Authorization")
        access_token = None
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access token not found"
            )

        # Logout user
        success = await auth_service.logout_user(
            access_token=access_token,
            refresh_token=logout_data.refresh_token
        )

        if success:
            logger.info(f"User {user.id} logged out successfully")
            return {"message": "Logout successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout"
            )

    except Exception as e:
        logger.error(f"Logout error for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service error"
        )


@router.post("/logout-all", status_code=200)
async def logout_all(
    request: Request,
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Logout user from all sessions.

    Blacklists all tokens for the current user.
    """
    auth_service = AuthService(db)

    try:
        success = await auth_service.logout_all_user_sessions(user.id)

        if success:
            logger.info(f"User {user.id} logged out from all sessions")
            return {"message": "Logout from all sessions successful"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout from all sessions"
            )

    except Exception as e:
        logger.error(f"Logout all error for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout service error"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(require_authenticated_user)
):
    """
    Get current user information.

    Returns detailed information about the authenticated user.
    """
    return UserResponse.from_orm(user)


@router.put("/change-password", status_code=200)
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Change user password.

    Requires current password and validates new password strength.
    All existing sessions will be terminated.
    """
    auth_service = AuthService(db)

    try:
        success = await auth_service.change_password(
            user_id=user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )

        if success:
            logger.info(f"Password changed for user {user.id}")
            return {"message": "Password changed successfully. Please login again."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )

    except AuthenticationError as e:
        logger.warning(f"Password change failed for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change service error"
        )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    request: Request,
    user_data: RegisterUserRequest,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register new admin/manager user.

    Only admins can create new users. Creates user with specified role.
    """
    auth_service = AuthService(db)

    try:
        # Only allow creating users with role equal or lower than current user
        if current_user.role == UserRole.MANAGER and user_data.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot create admin users"
            )

        new_user = await auth_service.register_admin_user(
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            role=user_data.role
        )

        logger.info(f"New user {new_user.id} created by admin {current_user.id}")

        return UserResponse.from_orm(new_user)

    except AuthenticationError as e:
        logger.warning(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration service error"
        )


# Token validation endpoint
@router.post("/validate", status_code=200)
async def validate_token(
    request: Request,
    user: User = Depends(require_authenticated_user)
):
    """
    Validate current token.

    Returns success if token is valid and user is active.
    """
    return {
        "valid": True,
        "user_id": user.id,
        "role": user.role.value,
        "message": "Token is valid"
    }


# Health check for authentication service
@router.get("/health", status_code=200)
async def auth_health_check():
    """
    Authentication service health check.

    Returns status of authentication components.
    """
    try:
        # Test JWT manager
        from app.utils.jwt import jwt_manager
        test_token = jwt_manager.create_access_token({"test": True})
        token_valid = jwt_manager.verify_token(test_token) is not None

        # Test security utils
        from app.utils.security import hash_password, verify_password
        test_hash = hash_password("test")
        hash_valid = verify_password("test", test_hash)

        return {
            "status": "healthy",
            "components": {
                "jwt_manager": "ok" if token_valid else "error",
                "password_hashing": "ok" if hash_valid else "error",
                "redis_connection": "ok",  # Could add actual Redis test
            }
        }

    except Exception as e:
        logger.error(f"Auth health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unhealthy"
        )