"""Security utilities for password hashing, validation and other security features."""

import secrets
import hashlib
import re
from passlib.context import CryptContext
from passlib.hash import bcrypt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


# Password context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordValidator:
    """Password strength validator."""

    def __init__(self):
        """Initialize password validator."""
        self.min_length = 8
        self.max_length = 128

    def validate_password(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength.

        Returns:
            Dict with validation result and details
        """
        errors = []
        score = 0

        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        elif len(password) >= 12:
            score += 1

        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")

        # Character type checks
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))

        if not has_upper:
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1

        if not has_lower:
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1

        if not has_digit:
            errors.append("Password must contain at least one digit")
        else:
            score += 1

        if not has_special:
            errors.append("Password must contain at least one special character")
        else:
            score += 1

        # Common patterns to avoid
        common_patterns = [
            (r'(.)\1{2,}', "Password should not contain repeated characters"),
            (r'(012|123|234|345|456|567|678|789|890)', "Password should not contain sequential numbers"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', "Password should not contain sequential letters"),
            (r'(qwerty|asdf|zxcv)', "Password should not contain keyboard patterns")
        ]

        for pattern, message in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append(message)
                score -= 1

        # Calculate strength
        strength = "weak"
        if score >= 4 and not errors:
            strength = "strong"
        elif score >= 2 and len(errors) <= 1:
            strength = "medium"

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": max(0, score)
        }


class SecurityUtils:
    """Security utility functions."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """Generate numeric verification code."""
        return ''.join(secrets.choice('0123456789') for _ in range(length))

    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant time string comparison to prevent timing attacks."""
        return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))

    @staticmethod
    def hash_string(value: str, salt: str = "") -> str:
        """Hash string with optional salt."""
        return hashlib.sha256((value + salt).encode()).hexdigest()

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 255) -> str:
        """Sanitize input string."""
        if not input_string:
            return ""

        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', input_string)

        # Trim and limit length
        sanitized = sanitized.strip()[:max_length]

        return sanitized

    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
        """Check if redirect URL is safe."""
        if not url:
            return False

        # Relative URLs are generally safe
        if url.startswith('/') and not url.startswith('//'):
            return True

        # Check against allowed hosts
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc in allowed_hosts
        except:
            return False


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        """Initialize rate limiter."""
        self._attempts = {}  # {key: [(timestamp, count), ...]}

    def is_allowed(
        self,
        key: str,
        max_attempts: int = 5,
        window_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limiting.

        Args:
            key: Unique identifier (IP, user_id, etc.)
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes

        Returns:
            Dict with allowed status and remaining attempts
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)

        # Clean old entries for this key
        if key in self._attempts:
            self._attempts[key] = [
                (timestamp, count) for timestamp, count in self._attempts[key]
                if timestamp > window_start
            ]
        else:
            self._attempts[key] = []

        # Count current attempts
        current_attempts = sum(count for _, count in self._attempts[key])

        # Check if allowed
        allowed = current_attempts < max_attempts
        remaining = max(0, max_attempts - current_attempts - 1)

        # Record this attempt
        if not allowed:
            # Find existing entry for current minute
            current_minute = now.replace(second=0, microsecond=0)
            found = False
            for i, (timestamp, count) in enumerate(self._attempts[key]):
                if timestamp == current_minute:
                    self._attempts[key][i] = (current_minute, count + 1)
                    found = True
                    break

            if not found:
                self._attempts[key].append((current_minute, 1))

        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_time": window_start + timedelta(minutes=window_minutes),
            "current_attempts": current_attempts
        }

    def record_attempt(self, key: str):
        """Record an attempt for the given key."""
        now = datetime.utcnow()
        current_minute = now.replace(second=0, microsecond=0)

        if key not in self._attempts:
            self._attempts[key] = []

        # Find existing entry for current minute
        found = False
        for i, (timestamp, count) in enumerate(self._attempts[key]):
            if timestamp == current_minute:
                self._attempts[key][i] = (current_minute, count + 1)
                found = True
                break

        if not found:
            self._attempts[key].append((current_minute, 1))

    def reset_key(self, key: str):
        """Reset attempts for a specific key."""
        if key in self._attempts:
            del self._attempts[key]

    def cleanup_old_entries(self, older_than_hours: int = 24):
        """Clean up old entries to prevent memory leaks."""
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

        for key in list(self._attempts.keys()):
            self._attempts[key] = [
                (timestamp, count) for timestamp, count in self._attempts[key]
                if timestamp > cutoff
            ]

            # Remove empty entries
            if not self._attempts[key]:
                del self._attempts[key]


# Global instances
password_validator = PasswordValidator()
security_utils = SecurityUtils()
rate_limiter = RateLimiter()


# Convenience functions
def hash_password(password: str) -> str:
    """Hash password."""
    return security_utils.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return security_utils.verify_password(plain_password, hashed_password)


def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength."""
    return password_validator.validate_password(password)


def generate_secure_token(length: int = 32) -> str:
    """Generate secure token."""
    return security_utils.generate_secure_token(length)