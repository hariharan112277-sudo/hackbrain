"""Track A Core Database — Phase 0 Contract Mirror."""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()
# Note: Actual engine instantiated in shared/app/database.py for contract alignment.
