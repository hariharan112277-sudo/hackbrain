"""
DatabaseConnectionManager manages connection lifecycles, connection pooling,
and explicit application context control hooks for the database layer.
"""

import time
from typing import Generator, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, DBAPIError

from database.config import db_settings
from database.logger import get_industrial_logger
from database.exceptions import ConnectionError, IOBDatabaseError

logger = get_industrial_logger("database.connection")


class DatabaseConnectionManager:
    """Provides thread-safe transactional session factories and infrastructure engines."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_url: Optional[str] = None):
        target_url = db_url or db_settings.sqlalchemy_url
        current_url = str(getattr(self, "engine", "").url) if getattr(self, "_initialized", False) else ""

        if getattr(self, "_initialized", False) and not db_url:
            return

        if getattr(self, "_initialized", False) and db_url and target_url == current_url:
            return

        is_sqlite = target_url.startswith("sqlite")

        engine_kwargs = {
            "pool_pre_ping": True
        }
        if not is_sqlite:
            engine_kwargs.update({
                "pool_size": db_settings.POOL_SIZE,
                "max_overflow": db_settings.MAX_OVERFLOW,
                "pool_timeout": db_settings.POOL_TIMEOUT,
                "pool_recycle": db_settings.POOL_RECYCLE,
                "connect_args": {
                    "options": f"-c search_path={db_settings.DB_SCHEMA}",
                    "connect_timeout": 10
                }
            })
        else:
            if ":memory:" in target_url:
                from sqlalchemy.pool import StaticPool
                engine_kwargs["poolclass"] = StaticPool
                engine_kwargs["connect_args"] = {"check_same_thread": False}

        self.engine = create_engine(target_url, **engine_kwargs)

        self.SessionFactory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        self.setup_pool_guards()
        self._initialized = True
        logger.info(f"Database connection engine initialized successfully ({target_url}).")

    def setup_pool_guards(self):
        """Attaches low-level structural event listener check execution monitors to the pool."""
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            logger.debug("Acquired raw baseline database socket connection from pool hierarchy.")

    setuppool_guards = setup_pool_guards

    def check_health(self) -> bool:
        """Executes a diagnostic verification pass against the database cluster."""
        retry_count = 0
        limit = 1 if str(self.engine.url).startswith("sqlite") else db_settings.CONNECT_RETRY_LIMIT
        while retry_count < limit:
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return True
            except (OperationalError, DBAPIError) as ex:
                retry_count += 1
                logger.warning(
                    f"Database cluster verification failure (Attempt {retry_count}/{limit}). Retrying..."
                )
                if not str(self.engine.url).startswith("sqlite"):
                    time.sleep(db_settings.CONNECT_RETRY_DELAY)
        return False

    def get_session(self) -> Session:
        """Returns a non-async thread-safe isolated relational storage context session block."""
        return self.SessionFactory()

    def shutdown(self):
        """Safely drains structural connections and closes the engine pool."""
        try:
            self.engine.dispose()
            logger.info("Engine connection pool infrastructure successfully drained and closed.")
        except Exception as ex:
            raise ConnectionError("Error terminating active engine connections during shutdown sequence.", ex)


# Global connection manager handle
connection_manager = DatabaseConnectionManager()


def get_db_context() -> Generator[Session, None, None]:
    """Context-manager generator token for clean dependency injection frameworks."""
    session = connection_manager.get_session()
    try:
        yield session
    finally:
        session.close()
