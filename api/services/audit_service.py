"""Audit Service - PHASE 6.4 - Logging & Audit Trail"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
from uuid import UUID
from db.database import SessionLocal, get_db_context
from db.models import AuditLog, ActionEnum

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing immutable audit trails"""

    def __init__(self):
        self.session = None

    def _get_db(self) -> Session:
        """Get database session"""
        if self.session is None:
            self.session = SessionLocal()
        return self.session

    def log_action(
        self,
        user_id: UUID,
        entity_type: str,
        entity_id: str,
        action: ActionEnum,
        changes: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Log an action to the audit trail"""
        try:
            db = self._get_db()
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
            logger.info(f"Audit logged: {entity_type} {entity_id} {action.value}")
            return True
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
            try:
                db.rollback()
            except:
                pass
            return False

    def log_config_change(
        self,
        user_id: UUID,
        config_key: str,
        old_value: Any,
        new_value: Any,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Log a configuration change"""
        return self.log_action(
            user_id=user_id,
            entity_type="Config",
            entity_id=str(user_id),
            action=ActionEnum.CONFIG_CHANGE,
            changes={
                "key": config_key,
                "old_value": old_value,
                "new_value": new_value
            },
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_api_key_access(
        self,
        user_id: UUID,
        provider: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Log API key access or rotation"""
        return self.log_action(
            user_id=user_id,
            entity_type="APIKey",
            entity_id=f"{provider}_key",
            action=ActionEnum.API_KEY_ACCESS,
            changes={"provider": provider, "action": action},
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_task_execution(
        self,
        user_id: UUID,
        task_id: UUID,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> bool:
        """Log task execution"""
        return self.log_action(
            user_id=user_id,
            entity_type="Task",
            entity_id=str(task_id),
            action=ActionEnum.TASK_EXECUTION,
            changes={
                "status": status,
                "result": result,
                "error": error
            }
        )

    def log_conversation_delete(
        self,
        user_id: UUID,
        conversation_id: UUID,
        reason: Optional[str] = None
    ) -> bool:
        """Log conversation deletion"""
        return self.log_action(
            user_id=user_id,
            entity_type="Conversation",
            entity_id=str(conversation_id),
            action=ActionEnum.CONVERSATION_DELETE,
            reason=reason
        )

    def get_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a specific entity"""
        try:
            db = self._get_db()
            logs = db.query(AuditLog).filter(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == str(entity_id)
                )
            ).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

            return [
                {
                    "id": str(log.id),
                    "user_id": str(log.user_id),
                    "action": log.action.value if log.action else None,
                    "changes": log.changes,
                    "reason": log.reason,
                    "timestamp": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {e}")
            return []

    def get_user_audit_trail(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all audit events for a user"""
        try:
            db = self._get_db()
            logs = db.query(AuditLog).filter(
                AuditLog.user_id == user_id
            ).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

            return [
                {
                    "id": str(log.id),
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "action": log.action.value if log.action else None,
                    "changes": log.changes,
                    "timestamp": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error retrieving user audit trail: {e}")
            return []

    def cleanup(self):
        """Close database session"""
        if self.session:
            try:
                self.session.close()
            except:
                pass


# Global instance
audit_service = AuditService()
