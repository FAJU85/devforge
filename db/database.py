"""Database connection, session, and initialization."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from db.models import Base

# Configuration — fall back to SQLite when PostgreSQL is not available
DB_URL = os.environ.get("DATABASE_URL", "")

if not DB_URL:
    try:
        import psycopg2  # noqa: F401
        DB_URL = "postgresql://devforge:devforge@localhost:5432/devforge"
    except ImportError:
        DB_URL = "sqlite:///./devforge.db"

# Only apply pool settings for non-SQLite databases
_is_sqlite = DB_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
        echo=os.environ.get("SQLALCHEMY_ECHO", "false").lower() == "true",
    )
else:
    from sqlalchemy.pool import QueuePool
    DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "10"))
    DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "3600"))
    DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
    DB_POOL_PRE_PING = os.environ.get("DB_POOL_PRE_PING", "true").lower() == "true"
    engine = create_engine(
        DB_URL,
        poolclass=QueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_recycle=DB_POOL_RECYCLE,
        pool_pre_ping=DB_POOL_PRE_PING,
        echo=os.environ.get("SQLALCHEMY_ECHO", "false").lower() == "true",
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for DB session (non-async)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def close_db():
    """Close engine connection pool."""
    engine.dispose()
