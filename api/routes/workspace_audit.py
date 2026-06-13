#!/usr/bin/env python3
"""
Workspace Audit Routes - Phase 7.4 Advanced Audit Logging

Endpoints for viewing and exporting audit logs.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from api.services.database_service import get_db
from api.services.workspace_audit_service import WorkspaceAuditService
from api.services.workspace_service import WorkspaceService
from api.services.role_permission_service import RolePermissionService
from api.services.auth_service import get_current_user_from_request

router = APIRouter(prefix="/api/workspaces", tags=["workspace-audit"])


class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: UUID
    workspace_id: UUID
    user_id: UUID
    action: str
    entity_type: str
    entity_id: str
    changes: Optional[Dict[str, Any]]
    reason: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogsListResponse(BaseModel):
    """List of audit logs"""
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


class ActivityResponse(BaseModel):
    """Activity item for dashboard"""
    id: str
    timestamp: datetime
    user_name: str
    user_login: str
    action: str
    entity_type: str
    entity_id: str
    description: str


class RecentActivitiesResponse(BaseModel):
    """Recent activities list"""
    activities: List[ActivityResponse]
    count: int


class ActionSummaryResponse(BaseModel):
    """Summary of actions in workspace"""
    workspace_id: UUID
    period_days: int
    action_counts: Dict[str, int]


@router.get("/{workspace_id}/audit-logs", response_model=AuditLogsListResponse)
async def get_audit_logs(
    request: Request,
    workspace_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    user_id: Optional[UUID] = None,
    entity_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db=Depends(get_db)
):
    """
    Get audit logs for a workspace with optional filtering.

    Args:
        request: Request context
        workspace_id: Workspace ID
        limit: Max logs to return (1-1000)
        offset: Pagination offset
        action: Filter by action type
        user_id: Filter by user ID
        entity_type: Filter by entity type
        start_date: Filter logs after this date (ISO format)
        end_date: Filter logs before this date (ISO format)
        db: Database session

    Returns:
        Audit logs with filters applied

    Raises:
        401: Not authenticated
        403: Not a member or insufficient permissions
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check membership
    if not (WorkspaceService.is_member(db, workspace_id, user.id) or WorkspaceService.is_owner(db, workspace_id, user.id)):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    # Check audit.view permission
    has_permission = RolePermissionService.check_permission(
        db, workspace_id, user.id, RolePermissionService.PERMISSION_AUDIT_VIEW
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied: audit.view required")

    logs, total = WorkspaceAuditService.get_audit_logs(
        db,
        workspace_id,
        limit=limit,
        offset=offset,
        action_filter=action,
        user_id_filter=user_id,
        entity_type_filter=entity_type,
        start_date=start_date,
        end_date=end_date
    )

    return AuditLogsListResponse(
        logs=[AuditLogResponse.from_orm(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{workspace_id}/audit-activities", response_model=RecentActivitiesResponse)
async def get_recent_activities(
    request: Request,
    workspace_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get recent activities for dashboard display.

    Args:
        request: Request context
        workspace_id: Workspace ID
        limit: Max activities (1-100)
        db: Database session

    Returns:
        Recent activities

    Raises:
        401: Not authenticated
        403: Not a member or insufficient permissions
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not (WorkspaceService.is_member(db, workspace_id, user.id) or WorkspaceService.is_owner(db, workspace_id, user.id)):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    has_permission = RolePermissionService.check_permission(
        db, workspace_id, user.id, RolePermissionService.PERMISSION_AUDIT_VIEW
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied: audit.view required")

    activities = WorkspaceAuditService.get_recent_activities(db, workspace_id, limit=limit)

    return RecentActivitiesResponse(
        activities=[ActivityResponse(**a) for a in activities],
        count=len(activities)
    )


@router.get("/{workspace_id}/audit-summary", response_model=ActionSummaryResponse)
async def get_audit_summary(
    request: Request,
    workspace_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db=Depends(get_db)
):
    """
    Get summary of actions in workspace (for dashboard).

    Args:
        request: Request context
        workspace_id: Workspace ID
        days: Look back N days
        db: Database session

    Returns:
        Action counts by type

    Raises:
        401: Not authenticated
        403: Not a member or insufficient permissions
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not (WorkspaceService.is_member(db, workspace_id, user.id) or WorkspaceService.is_owner(db, workspace_id, user.id)):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    has_permission = RolePermissionService.check_permission(
        db, workspace_id, user.id, RolePermissionService.PERMISSION_AUDIT_VIEW
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied: audit.view required")

    action_counts = WorkspaceAuditService.get_action_summary(db, workspace_id, days=days)

    return ActionSummaryResponse(
        workspace_id=workspace_id,
        period_days=days,
        action_counts=action_counts
    )


@router.post("/{workspace_id}/audit-export")
async def export_audit_logs(
    request: Request,
    workspace_id: UUID,
    format: str = Query("csv", regex="^(csv|json)$"),
    action: Optional[str] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db=Depends(get_db)
):
    """
    Export audit logs in CSV or JSON format.

    Args:
        request: Request context
        workspace_id: Workspace ID
        format: Export format (csv or json)
        action: Optional action filter
        user_id: Optional user filter
        start_date: Optional start date
        end_date: Optional end date
        db: Database session

    Returns:
        File download

    Raises:
        401: Not authenticated
        403: Not a member or insufficient permissions
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not (WorkspaceService.is_member(db, workspace_id, user.id) or WorkspaceService.is_owner(db, workspace_id, user.id)):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    has_permission = RolePermissionService.check_permission(
        db, workspace_id, user.id, RolePermissionService.PERMISSION_AUDIT_EXPORT
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied: audit.export required")

    if format == "csv":
        content = WorkspaceAuditService.export_to_csv(
            db,
            workspace_id,
            action_filter=action,
            user_id_filter=user_id,
            start_date=start_date,
            end_date=end_date
        )
        media_type = "text/csv"
        filename = f"audit-logs-{workspace_id}.csv"
    else:  # json
        content = WorkspaceAuditService.export_to_json(
            db,
            workspace_id,
            action_filter=action,
            user_id_filter=user_id,
            start_date=start_date,
            end_date=end_date
        )
        media_type = "application/json"
        filename = f"audit-logs-{workspace_id}.json"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
