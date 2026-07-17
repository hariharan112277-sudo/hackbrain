"""
Track B Async Database Wrapper — Phase 0 Remediation
Provides dependency-injected AsyncSession for realtime_ai modules.
Must NOT import or use app/realtime_ai/utils/db.py (deprecated).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal


async def get_track_b_session() -> AsyncSession:
    """Yield an async session drawn from the centralized Track A pool."""
    async with AsyncSessionLocal() as session:
        yield session
