"""
Database Engine & Session Management
Track A (Database Layer) — Stage 1

Configures the SQLAlchemy engine against the live PostgreSQL instance and
provides the reusable session generator injected into request lifecycles.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Configure SQLAlchemy engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Reusable database session dependency.
    Always yields a session and ensures it is closed after the request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
