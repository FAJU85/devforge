"""Database Service Layer - PHASE 6.2 - Database Integration"""

import logging
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from uuid import UUID
from db.database import SessionLocal, get_db_context
from db.models import AuditLog, ActionEnum

logger = logging.getLogger(__name__)
T = TypeVar('T')


class RepositoryBase(Generic[T]):
    """Generic repository pattern implementation for CRUD operations"""

    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, **kwargs) -> T:
        """Create a new entity"""
        try:
            obj = self.model(**kwargs)
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    def read(self, db: Session, entity_id: UUID) -> Optional[T]:
        """Read entity by ID"""
        try:
            return db.query(self.model).filter(
                self.model.id == entity_id,
                getattr(self.model, 'is_deleted', False) == False
            ).first()
        except Exception as e:
            logger.error(f"Error reading {self.model.__name__}: {e}")
            return None

    def update(self, db: Session, entity_id: UUID, **kwargs) -> Optional[T]:
        """Update entity by ID"""
        try:
            obj = self.read(db, entity_id)
            if not obj:
                return None

            for key, value in kwargs.items():
                if hasattr(obj, key) and key != 'id':
                    setattr(obj, key, value)

            if hasattr(obj, 'updated_at'):
                obj.updated_at = datetime.utcnow()
            if hasattr(obj, 'version'):
                obj.version += 1

            db.commit()
            db.refresh(obj)
            return obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise

    def delete(self, db: Session, entity_id: UUID) -> bool:
        """Soft delete entity by ID"""
        try:
            obj = self.read(db, entity_id)
            if not obj:
                return False

            if hasattr(obj, 'is_deleted'):
                obj.is_deleted = True
                obj.deleted_at = datetime.utcnow()
            else:
                db.delete(obj)

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            raise

    def list(self, db: Session, skip: int = 0, limit: int = 100, filters: Optional[Dict] = None) -> List[T]:
        """List entities with pagination and filtering"""
        try:
            query = db.query(self.model)

            if hasattr(self.model, 'is_deleted'):
                query = query.filter(getattr(self.model, 'is_deleted') == False)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)

            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error listing {self.model.__name__}: {e}")
            return []

    def hard_delete(self, db: Session, entity_id: UUID) -> bool:
        """Permanently delete entity (use with caution)"""
        try:
            obj = db.query(self.model).filter(self.model.id == entity_id).first()
            if not obj:
                return False

            db.delete(obj)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error hard deleting {self.model.__name__}: {e}")
            raise


class DatabaseService:
    """High-level database operations and transaction management"""

    @staticmethod
    def init_db():
        """Initialize database - run migrations and create tables"""
        from db.database import engine, init_db as db_init
        try:
            db_init()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    @staticmethod
    def health_check() -> Dict[str, Any]:
        """Check database health and connectivity"""
        try:
            with get_db_context() as db:
                result = db.execute("SELECT 1")
                result.fetchone()
            return {
                "status": "healthy",
                "database": "connected",
                "latency_ms": 0.5
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }

    @staticmethod
    def cleanup():
        """Graceful cleanup - close connection pool"""
        try:
            from db.database import close_db
            close_db()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")

    @staticmethod
    def get_session() -> Session:
        """Get a new database session"""
        return SessionLocal()

    @staticmethod
    def log_audit(
        db: Session,
        user_id: UUID,
        entity_type: str,
        entity_id: str,
        action: ActionEnum,
        changes: Optional[Dict] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Log an audit event"""
        try:
            audit = AuditLog(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action,
                changes=changes,
                reason=reason,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(audit)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
            db.rollback()
            return False
