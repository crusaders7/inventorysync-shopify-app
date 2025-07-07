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
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./inventorysync.db",
        description="Database connection URL"
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
    
    # Authentication
    secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        description="JWT Secret Key"
    )
    algorithm: str = Field(default="HS256", description="JWT Algorithm")
    access_token_expire_minutes: int = Field(
        default=30, 
        description="JWT Token expiry in minutes"
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
    if is_production():
        # Use PostgreSQL in production
        return settings.database_url
    else:
        # Use SQLite for development
        return "sqlite:///./inventorysync_dev.db"


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