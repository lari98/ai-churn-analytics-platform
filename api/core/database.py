"""
Async database engine — Azure SQL via SQLAlchemy 2.0 async.
Connection pooling, health checks, and session management.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


# ─── Engine ──────────────────────────────────────────────────────────────────
# Azure SQL uses pyodbc driver; for async we use aioodbc or the asyncpg wrapper.
# Connection string from Azure Key Vault (via environment variable).

engine = create_async_engine(
    settings.DATABASE_URL.get_secret_value(),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,          # Verify connections before use
    pool_recycle=1800,           # Recycle connections every 30 min
    echo=settings.DB_ECHO,       # SQL logging (False in production)
    connect_args={
        "timeout": 30,
        "command_timeout": 60,
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ─── Session Dependency ───────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: provides an async database session.
    Automatically commits or rolls back on exit.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for non-FastAPI usage (scripts, background tasks)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── Health Check ────────────────────────────────────────────────────────────

async def check_database_health() -> dict:
    """Verify database connectivity for health endpoint."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {"status": "unhealthy", "database": str(exc)}


# ─── Database Initialisation ─────────────────────────────────────────────────

async def init_db() -> None:
    """
    Create all tables on startup (idempotent).
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialised")


async def close_db() -> None:
    """Dispose engine connection pool on shutdown."""
    await engine.dispose()
    logger.info("Database connections closed")
