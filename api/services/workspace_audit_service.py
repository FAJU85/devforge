#!/usr/bin/env python3
"""
Workspace Audit Service - Phase 7.4 Advanced Audit Logging

Provides immutable audit logging for all workspace actions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import logging
import json

from db.models_workspace_v1 import WorkspaceAuditLog
from db.models_v2 import User

logger = logging.getLogger(__name__)


class WorkspaceAuditService:
    """Service for managing workspace audit logs."""

    @staticmethod
    def log_action(
        db: Session,
        workspace_id: UUID,
        user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: str,
        changes: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> WorkspaceAuditLog:
        """
        Log an action to the workspace audit trail.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID performing the action
            action: Action type (create, update, delete, invite, permission_change, etc.)
            entity_type: Type of entity affected (workspace, member, conversation, task, etc.)
            entity_id: ID of entity affected
            changes: Dict of {old_value, new_value} pairs for updates
            reason: Optional reason for the action
            ip_address: Optional client IP address
            user_agent: Optional client user agent

        Returns:
            Created WorkspaceAuditLog instance
        """
        audit_log = WorkspaceAuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )

        db.add(audit_log)
        db.commit()

        logger.info(
            f"Audit log created: workspace={workspace_id}, user={user_id}, "
            f"action={action}, entity={entity_type}/{entity_id}"
        )

        return audit_log

    @staticmethod
    def get_audit_logs(
        db: Session,
        workspace_id: UUID,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None,
        user_id_filter: Optional[UUID] = None,
        entity_type_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[WorkspaceAuditLog], int]:
        """
        Get audit logs for a workspace with optional filtering.

        Args:
            db: Database session
            workspace_id: Workspace ID
            limit: Max logs to return (default 100, max 1000)
            offset: Pagination offset
            action_filter: Filter by action type
            user_id_filter: Filter by user ID
            entity_type_filter: Filter by entity type
            start_date: Filter logs after this date
            end_date: Filter logs before this date

        Returns:
            Tuple of (logs list, total count)
        """
        # Enforce limits
        limit = min(limit, 1000)
        limit = max(limit, 1)

        query = db.query(WorkspaceAuditLog).filter(
            WorkspaceAuditLog.workspace_id == workspace_id
        )

        if action_filter:
            query = query.filter(WorkspaceAuditLog.action == action_filter)

        if user_id_filter:
            query = query.filter(WorkspaceAuditLog.user_id == user_id_filter)

        if entity_type_filter:
            query = query.filter(WorkspaceAuditLog.entity_type == entity_type_filter)

        if start_date:
            query = query.filter(WorkspaceAuditLog.created_at >= start_date)

        if end_date:
            query = query.filter(WorkspaceAuditLog.created_at <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination and sorting
        logs = query.order_by(desc(WorkspaceAuditLog.created_at)).offset(
            offset
        ).limit(limit).all()

        return logs, total

    @staticmethod
    def get_user_actions(
        db: Session,
        workspace_id: UUID,
        user_id: UUID,
        days: int = 30,
        limit: int = 100
    ) -> List[WorkspaceAuditLog]:
        """
        Get all actions performed by a user in a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID
            days: Look back N days
            limit: Max logs to return

        Returns:
            List of WorkspaceAuditLog instances
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = db.query(WorkspaceAuditLog).filter(
            and_(
                WorkspaceAuditLog.workspace_id == workspace_id,
                WorkspaceAuditLog.user_id == user_id,
                WorkspaceAuditLog.created_at >= start_date
            )
        ).order_by(desc(WorkspaceAuditLog.created_at)).limit(limit).all()

        return logs

    @staticmethod
    def get_entity_history(
        db: Session,
        workspace_id: UUID,
        entity_type: str,
        entity_id: str
    ) -> List[WorkspaceAuditLog]:
        """
        Get all changes to a specific entity.

        Args:
            db: Database session
            workspace_id: Workspace ID
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            List of WorkspaceAuditLog instances
        """
        logs = db.query(WorkspaceAuditLog).filter(
            and_(
                WorkspaceAuditLog.workspace_id == workspace_id,
                WorkspaceAuditLog.entity_type == entity_type,
                WorkspaceAuditLog.entity_id == entity_id
            )
        ).order_by(WorkspaceAuditLog.created_at).all()

        return logs

    @staticmethod
    def export_to_csv(
        db: Session,
        workspace_id: UUID,
        action_filter: Optional[str] = None,
        user_id_filter: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs to CSV format.

        Args:
            db: Database session
            workspace_id: Workspace ID
            action_filter: Optional action filter
            user_id_filter: Optional user filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            CSV string with headers and data
        """
        import csv
        from io import StringIO

        logs, _ = WorkspaceAuditService.get_audit_logs(
            db,
            workspace_id,
            limit=10000,  # Max for export
            action_filter=action_filter,
            user_id_filter=user_id_filter,
            start_date=start_date,
            end_date=end_date
        )

        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "timestamp",
                "user",
                "action",
                "entity_type",
                "entity_id",
                "changes",
                "reason",
                "ip_address",
                "user_agent"
            ]
        )

        writer.writeheader()

        for log in logs:
            user = db.query(User).filter(User.id == log.user_id).first()
            writer.writerow({
                "timestamp": log.created_at.isoformat(),
                "user": user.github_login if user else str(log.user_id),
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "changes": json.dumps(log.changes) if log.changes else "",
                "reason": log.reason or "",
                "ip_address": log.ip_address or "",
                "user_agent": log.user_agent or ""
            })

        return output.getvalue()

    @staticmethod
    def export_to_json(
        db: Session,
        workspace_id: UUID,
        action_filter: Optional[str] = None,
        user_id_filter: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs to JSON format.

        Args:
            db: Database session
            workspace_id: Workspace ID
            action_filter: Optional action filter
            user_id_filter: Optional user filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            JSON string
        """
        logs, total = WorkspaceAuditService.get_audit_logs(
            db,
            workspace_id,
            limit=10000,  # Max for export
            action_filter=action_filter,
            user_id_filter=user_id_filter,
            start_date=start_date,
            end_date=end_date
        )

        data = {
            "workspace_id": str(workspace_id),
            "exported_at": datetime.utcnow().isoformat(),
            "total_count": total,
            "logs": []
        }

        for log in logs:
            user = db.query(User).filter(User.id == log.user_id).first()
            data["logs"].append({
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "user_id": str(log.user_id),
                "user_login": user.github_login if user else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "changes": log.changes,
                "reason": log.reason,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent
            })

        return json.dumps(data, indent=2, default=str)

    @staticmethod
    def get_action_summary(
        db: Session,
        workspace_id: UUID,
        days: int = 30
    ) -> Dict[str, int]:
        """
        Get summary of actions in a workspace (useful for dashboards).

        Args:
            db: Database session
            workspace_id: Workspace ID
            days: Look back N days

        Returns:
            Dict with action counts
        """
        from sqlalchemy import func

        start_date = datetime.utcnow() - timedelta(days=days)

        results = db.query(
            WorkspaceAuditLog.action,
            func.count(WorkspaceAuditLog.id).label("count")
        ).filter(
            and_(
                WorkspaceAuditLog.workspace_id == workspace_id,
                WorkspaceAuditLog.created_at >= start_date
            )
        ).group_by(WorkspaceAuditLog.action).all()

        return {action: count for action, count in results}

    @staticmethod
    def get_recent_activities(
        db: Session,
        workspace_id: UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities for dashboard display.

        Args:
            db: Database session
            workspace_id: Workspace ID
            limit: Max activities to return

        Returns:
            List of activity dicts with formatted info
        """
        logs = db.query(WorkspaceAuditLog).filter(
            WorkspaceAuditLog.workspace_id == workspace_id
        ).order_by(desc(WorkspaceAuditLog.created_at)).limit(limit).all()

        activities = []
        for log in logs:
            user = db.query(User).filter(User.id == log.user_id).first()

            activity = {
                "id": str(log.id),
                "timestamp": log.created_at,
                "user_name": user.github_name if user else "Unknown",
                "user_login": user.github_login if user else "unknown",
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "description": f"{user.github_login if user else 'Unknown'} {log.action} {log.entity_type} {log.entity_id}"
            }
            activities.append(activity)

        return activities

    @staticmethod
    def cleanup_old_logs(
        db: Session,
        workspace_id: UUID,
        retention_days: int = 365
    ) -> int:
        """
        Archive (soft delete) old audit logs beyond retention period.

        Note: Audit logs are immutable, so we soft-delete with a flag
        (actual implementation would need an 'archived' flag on the model).

        Args:
            db: Database session
            workspace_id: Workspace ID
            retention_days: Keep logs newer than N days

        Returns:
            Number of logs archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Count before deletion
        old_logs = db.query(WorkspaceAuditLog).filter(
            and_(
                WorkspaceAuditLog.workspace_id == workspace_id,
                WorkspaceAuditLog.created_at < cutoff_date
            )
        ).count()

        # In production, these would be archived to S3/cold storage
        # For now, we keep immutable logs forever (GDPR considerations)
        logger.info(
            f"Workspace {workspace_id} has {old_logs} logs older than {retention_days} days. "
            "Logs are immutable and kept indefinitely for compliance."
        )

        return old_logs
