"""
Track A Core Database — Phase 0 & Phase 1 Remediation
Provides SQLAlchemy 2.0 async engine configuration and connection pooling with asyncpg.
Includes resilient looping connection-retry mechanism for clean boot across container initialization.
Supports hybrid sync/async access cleanly across the entire platform.
"""

import asyncio
from typing import AsyncGenerator, Any
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session as SyncSession
from sqlalchemy import text
import structlog

from app.core.config import settings

logger = structlog.get_logger("app.core.database.engine")

# Ensure async database driver format
DATABASE_URL = (
    settings.DATABASE_URL
    or "postgresql+asyncpg://postgres:postgres@localhost:5432/iob"
)
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith(
    "postgresql+asyncpg://"
):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
if DATABASE_URL.startswith("sqlite://") and not DATABASE_URL.startswith(
    "sqlite+aiosqlite://"
):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

# Derive sync database URL for synchronous route handlers and ORM queries
SYNC_DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://", 1).replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1).replace("postgresql+async://", "postgresql://", 1)

# Instantiate async engine with target operational metrics (Section 6)
engine = create_async_engine(
    DATABASE_URL,
    pool_size=getattr(settings, "DATABASE_POOL_SIZE", 20) if not DATABASE_URL.startswith("sqlite") else 5,
    max_overflow=getattr(settings, "DATABASE_MAX_OVERFLOW", 10) if not DATABASE_URL.startswith("sqlite") else 10,
    pool_timeout=getattr(settings, "DATABASE_POOL_TIMEOUT", 30.0),
    pool_recycle=1800,
    echo=False,
)

# Instantiate sync engine for synchronous Session operations
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=getattr(settings, "DATABASE_POOL_SIZE", 20) if not SYNC_DATABASE_URL.startswith("sqlite") else 5,
    max_overflow=getattr(settings, "DATABASE_MAX_OVERFLOW", 10) if not SYNC_DATABASE_URL.startswith("sqlite") else 10,
    pool_timeout=getattr(settings, "DATABASE_POOL_TIMEOUT", 30.0),
    pool_recycle=1800,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


class SyncAsyncSessionWrapper:
    """Hybrid session wrapper supporting both sync (`db.query()`) and async (`await db.execute()`) access patterns."""
    def __init__(self, async_session: AsyncSession, sync_session: SyncSession) -> None:
        self._async_session = async_session
        self._sync_session = sync_session

    def query(self, *entities, **kwargs):
        return self._sync_session.query(*entities, **kwargs)

    def add(self, instance):
        self._sync_session.add(instance)
        self._async_session.add(instance)

    def add_all(self, instances):
        self._sync_session.add_all(instances)
        self._async_session.add_all(instances)

    def delete(self, instance):
        self._sync_session.delete(instance)

    def commit(self):
        return self._sync_session.commit()

    def rollback(self):
        return self._sync_session.rollback()

    def refresh(self, instance, attribute_names=None, with_for_update=None):
        return self._sync_session.refresh(instance, attribute_names=attribute_names, with_for_update=with_for_update)

    def flush(self):
        return self._sync_session.flush()

    def close(self):
        return self._sync_session.close()

    def get(self, entity, ident, options=None, populate_existing=False, **kwargs):
        return self._sync_session.get(entity, ident, options=options, populate_existing=populate_existing, **kwargs)

    async def execute(self, *args, **kwargs):
        return await self._async_session.execute(*args, **kwargs)

    async def aclose(self):
        await self._async_session.close()
        self._sync_session.close()

    async def __aenter__(self):
        await self._async_session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._async_session.__aexit__(exc_type, exc_val, exc_tb)
        self._sync_session.close()

    def __getattr__(self, name):
        if hasattr(self._sync_session, name):
            return getattr(self._sync_session, name)
        return getattr(self._async_session, name)


async def get_db() -> AsyncGenerator[Any, None]:
    """Reusable async/sync database session dependency. Yields a hybrid SyncAsyncSessionWrapper."""
    async_sess = AsyncSessionLocal()
    sync_sess = SyncSessionLocal()
    wrapper = SyncAsyncSessionWrapper(async_sess, sync_sess)
    try:
        yield wrapper
    finally:
        await wrapper.aclose()


async def verify_database_connection(
    max_retries: int = 5, retry_interval: float = 2.0, timeout: float = 5.0
) -> bool:
    """
    Resilient looping connection-retry mechanism to handle transient database
    unavailability during system boot (R-6.1 & R-4.1).
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "verify_database_connection_attempt",
                attempt=attempt,
                max_retries=max_retries,
            )
            async with engine.connect() as conn:
                await asyncio.wait_for(
                    conn.execute(text("SELECT 1")), timeout=timeout
                )
            logger.info("verify_database_connection_success")
            return True
        except Exception as exc:
            logger.warning(
                "verify_database_connection_failed",
                attempt=attempt,
                error=str(exc),
            )
            if attempt < max_retries:
                await asyncio.sleep(retry_interval)
    logger.error("verify_database_connection_exhausted")
    return False
