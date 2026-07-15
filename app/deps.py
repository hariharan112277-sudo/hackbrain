"""
FastAPI Dependencies — Track A (Database Layer) — Stage 1

Single, canonical import point for the database session dependency.
Routers/services must inject sessions from here::

    from fastapi import Depends
    from app.deps import get_db

    @router.get("/assets")
    def list_assets(db: Session = Depends(get_db)):
        ...

The session lifecycle (create → yield → guaranteed close) is implemented in
``app.database.get_db``; this module simply re-exports it so the API layer
has a stable dependency import path that is decoupled from engine internals.

Note: ``app.core.dependencies`` (service/repository providers, another track's
module) is intentionally NOT re-exported here — import it directly where needed.
"""

from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db

# Convenient annotated alias: `db: DBSession` in route signatures.
DBSession = Annotated[Session, Depends(get_db)]

__all__ = ["get_db", "DBSession"]
