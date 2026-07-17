"""
DEPRECATED — Track B Database Session Factory (Violation IOB-001)
This file represents the structural violation identified in Phase 0.
It MUST NOT be used in production. It is preserved for audit and contract
reconciliation purposes only.

Violation: Custom, independent database session factory that bypasses
centralized connection pooling parameters of Track A.
Status: DEPRECATED — replaced by shared async session dependency.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Deprecated sync factory — event-loop blocking hazard during high load.
_DEPRECATED_ENGINE = create_engine("postgresql://localhost/iob")
_DEPRECATED_SESSION = sessionmaker(bind=_DEPRECATED_ENGINE)
