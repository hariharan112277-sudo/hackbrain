"""
Database Engine & Async Session Management
Track A (Database Layer) — Phase 0 Remediation

Configures SQLAlchemy 2.0 async engine against PostgreSQL and provides
reusable AsyncSession generators injected into request lifecycles.
Replaces synchronous session factory from Stage 1.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Canonical async driver string; falls back to postgresql+asyncpg
DATABASE_URL = settings.DATABASE_URL or "postgresql+asyncpg://postgres:postgres@localhost:5432/iob"
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
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

Base = declarative_base()


async def get_db():
    """
    Reusable async database session dependency.
    Always yields an AsyncSession and ensures it is closed after the request lifecycle.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
