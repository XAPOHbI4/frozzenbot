"""User model for Telegram users."""

from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel


class UserRole(enum.Enum):
    """User role enumeration."""
    USER = "user"  # Basic user - can place orders, view catalog
    MANAGER = "manager"  # Can manage products, orders
    ADMIN = "admin"  # Full access to everything


class User(BaseModel):
    """Telegram user model."""
    __tablename__ = "users"

    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True, unique=True, index=True)

    # Authentication fields
    password_hash = Column(String(255), nullable=True)  # For admin/manager users
    role = Column(SqlEnum(UserRole), default=UserRole.USER, nullable=False, index=True)

    # Legacy field for backward compatibility
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Security fields
    last_login_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(BigInteger, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    # Relationships
    carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return f"User(telegram_id={self.telegram_id}, username={self.username})"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False

    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return self.role == role

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission based on role."""
        permissions = {
            UserRole.USER: [
                "order:create", "order:view_own", "product:view", "category:view"
            ],
            UserRole.MANAGER: [
                "order:create", "order:view_own", "order:view_all", "order:update",
                "product:view", "product:create", "product:update", "product:delete",
                "category:view", "category:create", "category:update", "category:delete",
                "user:view_basic"
            ],
            UserRole.ADMIN: ["*"]  # Admin has all permissions
        }

        role_permissions = permissions.get(self.role, [])
        return "*" in role_permissions or permission in role_permissions

    def can_access_admin_panel(self) -> bool:
        """Check if user can access admin panel."""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER] and self.is_active

    def reset_failed_attempts(self):
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def increment_failed_attempts(self, max_attempts: int = 5, lockout_minutes: int = 30):
        """Increment failed login attempts and lock if necessary."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()