"""Tests for security utilities."""

import pytest
from datetime import datetime, timedelta

from app.utils.security import (
    SecurityUtils, PasswordValidator, RateLimiter,
    hash_password, verify_password, validate_password
)


class TestSecurityUtils:
    """Test security utility functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = SecurityUtils.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are quite long

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = SecurityUtils.hash_password(password)

        result = SecurityUtils.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = SecurityUtils.hash_password(password)

        result = SecurityUtils.verify_password(wrong_password, hashed)
        assert result is False

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token = SecurityUtils.generate_secure_token()

        assert token is not None
        assert len(token) > 20  # URL-safe base64 tokens are quite long
        assert isinstance(token, str)

    def test_generate_secure_token_custom_length(self):
        """Test secure token generation with custom length."""
        token = SecurityUtils.generate_secure_token(16)

        assert token is not None
        assert isinstance(token, str)

    def test_generate_numeric_code(self):
        """Test numeric code generation."""
        code = SecurityUtils.generate_numeric_code()

        assert code is not None
        assert len(code) == 6  # Default length
        assert code.isdigit()

    def test_generate_numeric_code_custom_length(self):
        """Test numeric code generation with custom length."""
        code = SecurityUtils.generate_numeric_code(8)

        assert len(code) == 8
        assert code.isdigit()

    def test_constant_time_compare_equal(self):
        """Test constant time comparison with equal strings."""
        str1 = "test_string"
        str2 = "test_string"

        result = SecurityUtils.constant_time_compare(str1, str2)
        assert result is True

    def test_constant_time_compare_different(self):
        """Test constant time comparison with different strings."""
        str1 = "test_string"
        str2 = "different_string"

        result = SecurityUtils.constant_time_compare(str1, str2)
        assert result is False

    def test_hash_string(self):
        """Test string hashing."""
        test_string = "test_string"
        hashed = SecurityUtils.hash_string(test_string)

        assert hashed is not None
        assert len(hashed) == 64  # SHA256 hex digest length
        assert hashed != test_string

    def test_hash_string_with_salt(self):
        """Test string hashing with salt."""
        test_string = "test_string"
        salt = "test_salt"

        hashed_no_salt = SecurityUtils.hash_string(test_string)
        hashed_with_salt = SecurityUtils.hash_string(test_string, salt)

        assert hashed_no_salt != hashed_with_salt

    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "123@example.com"
        ]

        for email in valid_emails:
            assert SecurityUtils.validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid_email",
            "@example.com",
            "test@",
            "test@.com",
            "",
            None
        ]

        for email in invalid_emails:
            assert SecurityUtils.validate_email(email) is False

    def test_sanitize_input_normal(self):
        """Test input sanitization with normal input."""
        input_str = "normal input string"
        result = SecurityUtils.sanitize_input(input_str)

        assert result == input_str

    def test_sanitize_input_with_control_chars(self):
        """Test input sanitization with control characters."""
        input_str = "test\x00\x1F\x7Fstring"
        result = SecurityUtils.sanitize_input(input_str)

        assert "\x00" not in result
        assert "\x1F" not in result
        assert "\x7F" not in result
        assert "teststring" == result

    def test_sanitize_input_trim_whitespace(self):
        """Test input sanitization trims whitespace."""
        input_str = "   test string   "
        result = SecurityUtils.sanitize_input(input_str)

        assert result == "test string"

    def test_sanitize_input_length_limit(self):
        """Test input sanitization respects length limit."""
        long_string = "a" * 1000
        result = SecurityUtils.sanitize_input(long_string, max_length=100)

        assert len(result) == 100

    def test_sanitize_input_empty(self):
        """Test input sanitization with empty input."""
        result = SecurityUtils.sanitize_input("")
        assert result == ""

        result = SecurityUtils.sanitize_input(None)
        assert result == ""

    def test_is_safe_redirect_url_relative(self):
        """Test safe redirect URL validation with relative URLs."""
        safe_urls = ["/dashboard", "/admin/users", "/"]

        for url in safe_urls:
            result = SecurityUtils.is_safe_redirect_url(url, [])
            assert result is True

    def test_is_safe_redirect_url_protocol_relative(self):
        """Test safe redirect URL validation with protocol-relative URLs."""
        unsafe_url = "//evil.com/malware"
        result = SecurityUtils.is_safe_redirect_url(unsafe_url, [])
        assert result is False

    def test_is_safe_redirect_url_allowed_hosts(self):
        """Test safe redirect URL validation with allowed hosts."""
        allowed_hosts = ["example.com", "api.example.com"]

        safe_urls = [
            "https://example.com/page",
            "https://api.example.com/endpoint"
        ]

        for url in safe_urls:
            result = SecurityUtils.is_safe_redirect_url(url, allowed_hosts)
            assert result is True

    def test_is_safe_redirect_url_disallowed_hosts(self):
        """Test safe redirect URL validation with disallowed hosts."""
        allowed_hosts = ["example.com"]

        unsafe_urls = [
            "https://evil.com/malware",
            "https://fake-example.com/phishing"
        ]

        for url in unsafe_urls:
            result = SecurityUtils.is_safe_redirect_url(url, allowed_hosts)
            assert result is False


class TestPasswordValidator:
    """Test password validation functionality."""

    @pytest.fixture
    def validator(self):
        """Create password validator instance."""
        return PasswordValidator()

    def test_validate_strong_password(self, validator):
        """Test validation of strong password."""
        strong_password = "MyStr0ng!P@ssw0rd"
        result = validator.validate_password(strong_password)

        assert result["valid"] is True
        assert result["strength"] == "strong"
        assert len(result["errors"]) == 0
        assert result["score"] >= 4

    def test_validate_weak_password(self, validator):
        """Test validation of weak password."""
        weak_password = "weak"
        result = validator.validate_password(weak_password)

        assert result["valid"] is False
        assert result["strength"] == "weak"
        assert len(result["errors"]) > 0

    def test_validate_password_too_short(self, validator):
        """Test validation of too short password."""
        short_password = "1234567"  # 7 chars, below minimum 8
        result = validator.validate_password(short_password)

        assert result["valid"] is False
        assert any("at least" in error for error in result["errors"])

    def test_validate_password_too_long(self, validator):
        """Test validation of too long password."""
        long_password = "a" * 130  # Above maximum 128
        result = validator.validate_password(long_password)

        assert result["valid"] is False
        assert any("no more than" in error for error in result["errors"])

    def test_validate_password_missing_uppercase(self, validator):
        """Test validation of password missing uppercase."""
        password = "lowercase123!"
        result = validator.validate_password(password)

        assert result["valid"] is False
        assert any("uppercase" in error for error in result["errors"])

    def test_validate_password_missing_lowercase(self, validator):
        """Test validation of password missing lowercase."""
        password = "UPPERCASE123!"
        result = validator.validate_password(password)

        assert result["valid"] is False
        assert any("lowercase" in error for error in result["errors"])

    def test_validate_password_missing_digit(self, validator):
        """Test validation of password missing digit."""
        password = "NoDigitsHere!"
        result = validator.validate_password(password)

        assert result["valid"] is False
        assert any("digit" in error for error in result["errors"])

    def test_validate_password_missing_special(self, validator):
        """Test validation of password missing special character."""
        password = "NoSpecialChars123"
        result = validator.validate_password(password)

        assert result["valid"] is False
        assert any("special character" in error for error in result["errors"])

    def test_validate_password_repeated_chars(self, validator):
        """Test validation of password with repeated characters."""
        password = "Password111!!!"  # Has repeated chars
        result = validator.validate_password(password)

        assert any("repeated" in error for error in result["errors"])

    def test_validate_password_sequential_numbers(self, validator):
        """Test validation of password with sequential numbers."""
        password = "Password123!"  # Has "123"
        result = validator.validate_password(password)

        assert any("sequential" in error for error in result["errors"])

    def test_validate_password_keyboard_pattern(self, validator):
        """Test validation of password with keyboard patterns."""
        password = "Passwordqwerty!"  # Has "qwerty"
        result = validator.validate_password(password)

        assert any("keyboard" in error for error in result["errors"])


class TestRateLimiter:
    """Test rate limiting functionality."""

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance."""
        return RateLimiter()

    def test_initial_request_allowed(self, rate_limiter):
        """Test that initial request is allowed."""
        result = rate_limiter.is_allowed("test_key")

        assert result["allowed"] is True
        assert result["remaining"] >= 0

    def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit is enforced."""
        key = "test_key"
        max_attempts = 3

        # Make allowed requests
        for i in range(max_attempts):
            result = rate_limiter.is_allowed(key, max_attempts=max_attempts)
            assert result["allowed"] is True

        # Next request should be blocked
        result = rate_limiter.is_allowed(key, max_attempts=max_attempts)
        assert result["allowed"] is False

    def test_record_attempt(self, rate_limiter):
        """Test recording attempts."""
        key = "test_key"

        # Record an attempt
        rate_limiter.record_attempt(key)

        # Check it's recorded
        result = rate_limiter.is_allowed(key, max_attempts=5)
        assert result["current_attempts"] > 0

    def test_reset_key(self, rate_limiter):
        """Test resetting attempts for a key."""
        key = "test_key"

        # Record some attempts
        for _ in range(3):
            rate_limiter.record_attempt(key)

        # Reset the key
        rate_limiter.reset_key(key)

        # Check attempts are reset
        result = rate_limiter.is_allowed(key)
        assert result["current_attempts"] == 0

    def test_different_keys_independent(self, rate_limiter):
        """Test that different keys are tracked independently."""
        key1 = "key1"
        key2 = "key2"
        max_attempts = 2

        # Exhaust attempts for key1
        for i in range(max_attempts):
            result = rate_limiter.is_allowed(key1, max_attempts=max_attempts)
            assert result["allowed"] is True

        # key1 should be blocked
        result = rate_limiter.is_allowed(key1, max_attempts=max_attempts)
        assert result["allowed"] is False

        # key2 should still be allowed
        result = rate_limiter.is_allowed(key2, max_attempts=max_attempts)
        assert result["allowed"] is True


# Convenience function tests
class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_hash_password_function(self):
        """Test hash_password convenience function."""
        password = "test123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 50

    def test_verify_password_function(self):
        """Test verify_password convenience function."""
        password = "test123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_validate_password_function(self):
        """Test validate_password convenience function."""
        result = validate_password("StrongPass123!")

        assert "valid" in result
        assert "strength" in result
        assert "errors" in result