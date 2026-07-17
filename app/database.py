"""
Database Engine & Async Session Management
Track A (Database Layer) — Phase 0 & Phase 1 Remediation

Configures SQLAlchemy 2.0 async engine against PostgreSQL and provides
reusable AsyncSession generators injected into request lifecycles.
Replaces synchronous session factory from Stage 1.
Re-exports canonical engine definitions from app.core.database.engine.
"""

from app.core.database.engine import (
    DATABASE_URL,
    AsyncSessionLocal,
    SyncSessionLocal,
    SyncAsyncSessionWrapper,
    Base,
    engine,
    get_db,
    verify_database_connection,
)

# Compatibility alias for repositories expecting SessionLocal name
SessionLocal = AsyncSessionLocal
