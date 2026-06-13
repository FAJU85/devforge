#!/usr/bin/env python3
"""
Workspace Settings Routes - Phase 7.3 Workspace Settings & Isolation

Endpoints for managing per-workspace configuration and settings.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json

from api.services.database_service import get_db
from api.services.workspace_service import WorkspaceService
from api.services.auth_service import get_current_user_from_request
from api.services.role_permission_service import RolePermissionService
from db.models_workspace_v1 import WorkspaceSettings

router = APIRouter(prefix="/api/workspaces", tags=["workspace-settings"])


class WorkspaceSettingsResponse(BaseModel):
    """Workspace settings response"""
    id: UUID
    workspace_id: UUID
    rate_limit_requests_per_minute: int
    rate_limit_tasks_per_day: int
    rate_limit_conversations_per_day: int
    api_keys_enabled: bool
    features_enabled: Dict[str, bool]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateWorkspaceSettingsRequest(BaseModel):
    """Update workspace settings request"""
    rate_limit_requests_per_minute: Optional[int] = Field(None, ge=1, le=10000)
    rate_limit_tasks_per_day: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_conversations_per_day: Optional[int] = Field(None, ge=1, le=100000)
    api_keys_enabled: Optional[bool] = None
    features_enabled: Optional[Dict[str, bool]] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkspaceExportResponse(BaseModel):
    """Workspace export response"""
    workspace_id: UUID
    export_date: datetime
    format: str  # "json" or "csv"
    data_summary: Dict[str, int]  # Counts of different entity types


@router.get("/{workspace_id}/settings", response_model=WorkspaceSettingsResponse)
async def get_workspace_settings(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Get workspace settings and configuration.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        Workspace settings

    Raises:
        401: Not authenticated
        403: Not a member of workspace
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

    settings = db.query(WorkspaceSettings).filter(
        WorkspaceSettings.workspace_id == workspace_id
    ).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return WorkspaceSettingsResponse.from_orm(settings)


@router.patch("/{workspace_id}/settings", response_model=WorkspaceSettingsResponse)
async def update_workspace_settings(
    request: Request,
    workspace_id: UUID,
    payload: UpdateWorkspaceSettingsRequest,
    db=Depends(get_db)
):
    """
    Update workspace settings (owner/admin only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        payload: Settings to update
        db: Database session

    Returns:
        Updated settings

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Workspace or settings not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission
    has_permission = RolePermissionService.check_permission(
        db, workspace_id, user.id, RolePermissionService.PERMISSION_SETTINGS_EDIT
    )
    if not has_permission:
        raise HTTPException(status_code=403, detail="Permission denied: settings.edit required")

    settings = db.query(WorkspaceSettings).filter(
        WorkspaceSettings.workspace_id == workspace_id
    ).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    # Update fields
    if payload.rate_limit_requests_per_minute is not None:
        settings.rate_limit_requests_per_minute = payload.rate_limit_requests_per_minute
    if payload.rate_limit_tasks_per_day is not None:
        settings.rate_limit_tasks_per_day = payload.rate_limit_tasks_per_day
    if payload.rate_limit_conversations_per_day is not None:
        settings.rate_limit_conversations_per_day = payload.rate_limit_conversations_per_day
    if payload.api_keys_enabled is not None:
        settings.api_keys_enabled = payload.api_keys_enabled
    if payload.features_enabled is not None:
        settings.features_enabled = payload.features_enabled
    if payload.metadata is not None:
        settings.metadata = payload.metadata

    settings.updated_at = datetime.utcnow()
    db.commit()

    return WorkspaceSettingsResponse.from_orm(settings)


@router.post("/{workspace_id}/export", response_model=WorkspaceExportResponse, status_code=202)
async def export_workspace(
    request: Request,
    workspace_id: UUID,
    format: str = "json",
    db=Depends(get_db)
):
    """
    Export workspace data (conversations, tasks, configurations).

    Note: This is an async operation that returns immediately with status 202.
    In production, a background task would handle the actual export and
    notify the user when ready for download.

    Args:
        request: Request context
        workspace_id: Workspace ID
        format: Export format (json or csv)
        db: Database session

    Returns:
        Export status response

    Raises:
        401: Not authenticated
        403: Not workspace owner
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can export workspace")

    # TODO: Trigger background export task
    # For now, return placeholder response

    return WorkspaceExportResponse(
        workspace_id=workspace_id,
        export_date=datetime.utcnow(),
        format=format,
        data_summary={
            "conversations": 0,
            "tasks": 0,
            "repositories": 0,
            "members": 0,
            "audit_logs": 0
        }
    )


@router.post("/{workspace_id}/archive", status_code=200)
async def archive_workspace(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Archive a workspace (owner only).

    Archived workspaces are read-only and don't count toward limits.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        Success message

    Raises:
        401: Not authenticated
        403: Not workspace owner
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can archive workspace")

    workspace.is_archived = True
    workspace.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Workspace archived successfully",
        "workspace_id": str(workspace_id),
        "is_archived": True
    }


@router.post("/{workspace_id}/unarchive", status_code=200)
async def unarchive_workspace(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Unarchive a workspace (owner only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        Success message

    Raises:
        401: Not authenticated
        403: Not workspace owner
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can unarchive workspace")

    workspace.is_archived = False
    workspace.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Workspace unarchived successfully",
        "workspace_id": str(workspace_id),
        "is_archived": False
    }


@router.get("/{workspace_id}/data-usage", status_code=200)
async def get_workspace_data_usage(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Get data usage statistics for a workspace.

    Returns counts of conversations, tasks, repositories, etc.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        Data usage stats

    Raises:
        401: Not authenticated
        403: Not a member of workspace
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

    # Count entities in workspace
    from db.models_v2 import Conversation, Task, Repository

    conversation_count = db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id,
        Conversation.is_deleted == False
    ).count()

    task_count = db.query(Task).filter(
        Task.workspace_id == workspace_id,
        Task.is_deleted == False
    ).count()

    repository_count = db.query(Repository).filter(
        Repository.workspace_id == workspace_id,
        Repository.is_deleted == False
    ).count()

    member_count = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.is_active == True
    ).count()

    from db.models_workspace_v1 import WorkspaceMember
    audit_count = db.query(WorkspaceAuditLog).filter(
        WorkspaceAuditLog.workspace_id == workspace_id
    ).count()

    from db.models_workspace_v1 import WorkspaceAuditLog
    return {
        "workspace_id": str(workspace_id),
        "conversations": conversation_count,
        "tasks": task_count,
        "repositories": repository_count,
        "members": member_count,
        "audit_logs": audit_count,
        "storage_estimate_mb": (conversation_count * 0.1) + (audit_count * 0.01)  # Rough estimate
    }
