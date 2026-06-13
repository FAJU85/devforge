#!/usr/bin/env python3
"""
Workspace Routes - Phase 7.1 Multi-User Workspaces

Endpoints for creating, managing, and switching workspaces.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from api.services.database_service import get_db
from api.services.workspace_service import WorkspaceService
from api.services.auth_service import get_current_user_from_request

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    """Workspace creation request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class WorkspaceUpdate(BaseModel):
    """Workspace update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=1024)


class WorkspaceResponse(BaseModel):
    """Workspace response model"""
    id: UUID
    owner_id: UUID
    name: str
    description: Optional[str]
    avatar_url: Optional[str]
    is_default: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """List of workspaces"""
    workspaces: List[WorkspaceResponse]
    count: int


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    request: Request,
    payload: WorkspaceCreate,
    db=Depends(get_db)
):
    """
    Create a new workspace.

    Args:
        request: Request context
        payload: Workspace creation payload
        db: Database session

    Returns:
        Created workspace

    Raises:
        401: Not authenticated
        400: Invalid input
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        workspace = WorkspaceService.create_workspace(
            db,
            owner_id=user.id,
            name=payload.name,
            description=payload.description,
            is_default=False
        )
        return WorkspaceResponse.from_orm(workspace)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    request: Request,
    db=Depends(get_db)
):
    """
    List all workspaces the user is a member of or owns.

    Args:
        request: Request context
        db: Database session

    Returns:
        List of workspaces

    Raises:
        401: Not authenticated
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspaces = WorkspaceService.list_user_workspaces(db, user.id)
    return WorkspaceListResponse(
        workspaces=[WorkspaceResponse.from_orm(w) for w in workspaces],
        count=len(workspaces)
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Get workspace details.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        Workspace details

    Raises:
        401: Not authenticated
        403: Not a member of this workspace
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if user is member or owner
    if not (WorkspaceService.is_member(db, workspace_id, user.id) or WorkspaceService.is_owner(db, workspace_id, user.id)):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    return WorkspaceResponse.from_orm(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    request: Request,
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    db=Depends(get_db)
):
    """
    Update workspace details (owner only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        payload: Update payload
        db: Database session

    Returns:
        Updated workspace

    Raises:
        401: Not authenticated
        403: Not the workspace owner
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can update workspace")

    try:
        updated = WorkspaceService.update_workspace(
            db,
            workspace_id,
            name=payload.name,
            description=payload.description,
            avatar_url=payload.avatar_url
        )
        return WorkspaceResponse.from_orm(updated)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Delete a workspace (soft delete, owner only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Raises:
        401: Not authenticated
        403: Not the workspace owner
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can delete workspace")

    try:
        WorkspaceService.delete_workspace(db, workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workspace_id}/leave", status_code=204)
async def leave_workspace(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Leave a workspace (remove self from membership).

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Raises:
        401: Not authenticated
        403: Cannot leave as owner or not a member
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Owner cannot leave workspace")

    try:
        WorkspaceService.remove_member(db, workspace_id, user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workspace_id}/switch", status_code=200)
async def switch_workspace(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Switch active workspace (updates user context).

    Args:
        request: Request context
        workspace_id: Workspace ID to switch to
        db: Database session

    Returns:
        Switched workspace details

    Raises:
        401: Not authenticated
        403: Not a member of this workspace
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

    # Update user's default workspace
    user.default_workspace_id = workspace_id
    db.commit()

    return WorkspaceResponse.from_orm(workspace)
