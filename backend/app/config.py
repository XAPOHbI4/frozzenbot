"""Application configuration."""

import os
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Telegram Bot
    bot_token: str
    admin_id: int
    webapp_url: str = "https://domashniystandart.com"

    # Telegram Payments
    payment_provider_token: str  # Should be set via environment variable
    payment_webhook_url: str = "https://domashniystandart.com/api/payments/webhook"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Rate limiting
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window: int = 15
    api_rate_limit_attempts: int = 100
    api_rate_limit_window: int = 1

    # Account security
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 30
    password_min_length: int = 8
    password_max_length: int = 128

    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://domashniystandart.com",
        "https://www.domashniystandart.com"
    ]
    cors_allow_credentials: bool = True

    # Business Logic
    min_order_amount: int = 1500
    payment_card_info: str

    # App Settings
    debug: bool = False  # Default to False for production security
    environment: str = "production"  # production, development, testing
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "https://domashniystandart.com"  # Base URL for API endpoints

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override debug based on environment
        if self.environment.lower() in ["development", "dev", "testing", "test"]:
            self.debug = True
        else:
            self.debug = False

        # Production security checks
        if self.environment.lower() == "production":
            self._validate_production_config()

    def _validate_production_config(self):
        """Validate configuration for production environment."""
        if self.secret_key == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed from default value in production")

        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long in production")

        if "*" in self.cors_origins:
            raise ValueError("CORS origins cannot include wildcard (*) in production")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()