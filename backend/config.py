"""
InventorySync Configuration
Centralized configuration management for the application
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "InventorySync"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # API Versioning
    api_version: str = Field(default="v1", description="Current API version")
    api_version_header: bool = Field(default=True, description="Enable API version headers")
    enable_cache_busting: bool = Field(default=True, description="Enable cache busting")
    deployment_id: Optional[str] = Field(default=None, description="Deployment identifier")
    build_number: Optional[str] = Field(default=None, description="Build number for cache invalidation")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./inventorysync.db",
        description="Database connection URL"
    )
    database_url_async: Optional[str] = Field(
        default=None,
        description="Async database connection URL for PostgreSQL"
    )
    
    # Shopify API
    shopify_api_key: Optional[str] = Field(
        default=None,
        description="Shopify App API Key"
    )
    shopify_api_secret: Optional[str] = Field(
        default=None, 
        description="Shopify App Secret Key"
    )
    shopify_webhook_secret: Optional[str] = Field(
        default=None,
        description="Shopify Webhook Secret"
    )
    
    # App URLs
    app_url: str = Field(
        default="http://localhost:8000",
        description="Backend API URL"
    )
    frontend_url: str = Field(
        default="http://localhost:3000", 
        description="Frontend application URL"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    
    # Authentication
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT Secret Key"
    )
    jwt_secret_key: str = Field(
        default="your-jwt-secret-key-change-in-production",
        description="JWT Secret Key"
    )
    algorithm: str = Field(default="HS256", description="JWT Algorithm")
    access_token_expire_minutes: int = Field(
        default=30, 
        description="JWT Token expiry in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=30,
        description="Refresh token expiry in days"
    )
    
    # Redis (for caching and background tasks)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # External APIs
    stripe_api_key: Optional[str] = Field(
        default=None,
        description="Stripe API Key for payments"
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None,
        description="Stripe Webhook Secret"
    )
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    
    # Feature Flags
    enable_forecasting: bool = Field(
        default=True,
        description="Enable AI forecasting features"
    )
    enable_multi_location: bool = Field(
        default=True,
        description="Enable multi-location support"
    )
    enable_supplier_integration: bool = Field(
        default=False,
        description="Enable supplier integration (beta)"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="API rate limit per minute"
    )
    disable_rate_limit: bool = Field(
        default=False,
        description="Disable rate limiting (development only)"
    )
    
    # Additional Settings from .env
    postgres_password: Optional[str] = Field(default=None)
    redis_password: Optional[str] = Field(default=None)
    log_level: str = Field(default="INFO")
    cors_origins: str = Field(default="http://localhost:3000")
    backup_webhook_url: Optional[str] = Field(default=None)
    enable_api_docs: bool = Field(default=True)
    enable_swagger_ui: bool = Field(default=True)
    
    # Security Settings
    ssl_redirect: bool = Field(default=False, description="Redirect HTTP to HTTPS")
    secure_cookies: bool = Field(default=False, description="Use secure cookies")
    session_cookie_secure: bool = Field(default=False)
    session_cookie_httponly: bool = Field(default=True)
    session_cookie_samesite: str = Field(default="lax")
    encryption_key: Optional[str] = Field(default=None, description="Data encryption key")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI to inject settings"""
    return settings


# Development environment check
def is_development() -> bool:
    """Check if running in development mode"""
    return settings.debug or os.getenv("ENVIRONMENT", "").lower() in ["dev", "development"]


def is_production() -> bool:
    """Check if running in production mode"""
    return os.getenv("ENVIRONMENT", "").lower() in ["prod", "production"]


# Database URL helpers
def get_database_url() -> str:
    """Get the appropriate database URL"""
    # Always use the database_url from settings
    # This allows switching between SQLite and PostgreSQL via .env
    return settings.database_url


# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "inventorysync.log",
            "mode": "a",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "inventorysync": {
            "level": "DEBUG" if is_development() else "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}