"""Database connection, session, and initialization."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from db.models import Base

# Configuration
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://devforge:devforge@localhost:5432/devforge"
)

# Optional pool settings
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "10"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "3600"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "20"))
DB_POOL_PRE_PING = os.environ.get("DB_POOL_PRE_PING", "true").lower() == "true"

# Create engine with connection pooling
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
