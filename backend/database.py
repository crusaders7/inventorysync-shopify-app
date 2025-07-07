"""
InventorySync Database Configuration
SQLAlchemy setup for inventory management data
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
import logging

from .config import get_database_url, is_development

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = get_database_url()

# For async operations (production)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://") if "postgresql" in DATABASE_URL else DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

# SQLAlchemy setup
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Sync engine (for migrations and development)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=is_development(),  # Log SQL queries in development
)

# Async engine (for production API)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=is_development(),
    future=True,
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_db() -> Session:
    """
    Dependency for synchronous database sessions
    Used for migrations and setup scripts
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for asynchronous database sessions
    Used for API endpoints
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with async_engine.begin() as conn:
        # Import all models here to ensure they're registered
        from . import models  # noqa: F401
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    await async_engine.dispose()
    logger.info("Database connections closed")


# Database utilities
class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    async def create_tables():
        """Create all database tables"""
        await init_db()
    
    @staticmethod
    async def drop_tables():
        """Drop all database tables (development only)"""
        if not is_development():
            raise RuntimeError("Cannot drop tables in production")
        
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
    
    @staticmethod
    async def reset_database():
        """Reset database (development only)"""
        if not is_development():
            raise RuntimeError("Cannot reset database in production")
        
        await DatabaseManager.drop_tables()
        await DatabaseManager.create_tables()
        logger.info("Database reset completed")


# Database health check
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False