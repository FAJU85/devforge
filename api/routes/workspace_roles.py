#!/usr/bin/env python3
"""
Workspace Roles & Permissions Routes - Phase 7.2 RBAC

Endpoints for managing roles and checking permissions in workspaces.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Set, Optional
from uuid import UUID
from datetime import datetime

from api.services.database_service import get_db
from api.services.role_permission_service import RolePermissionService
from api.services.workspace_service import WorkspaceService
from api.services.auth_service import get_current_user_from_request

router = APIRouter(prefix="/api/workspaces", tags=["workspace-roles"])


class PermissionResponse(BaseModel):
    """Permission response"""
    id: UUID
    name: str
    description: Optional[str]
    category: str

    class Config:
        from_attributes = True


class PermissionsListResponse(BaseModel):
    """List of permissions"""
    permissions: List[PermissionResponse]
    count: int


class UserPermissionsResponse(BaseModel):
    """User's permissions in a workspace"""
    user_id: UUID
    workspace_id: UUID
    permissions: Set[str]
    role: Optional[dict]


class RoleDetailsResponse(BaseModel):
    """Role with permissions"""
    id: UUID
    name: str
    description: Optional[str]
    role_type: Optional[str]
    is_custom: bool
    permissions: List[PermissionResponse]

    class Config:
        from_attributes = True


class GrantPermissionRequest(BaseModel):
    """Grant permission request"""
    permission_id: UUID


class RevokePermissionRequest(BaseModel):
    """Revoke permission request"""
    permission_id: UUID


@router.get("/{workspace_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    Get all permissions for the current user in a workspace.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        User's permissions in workspace

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

    permissions = RolePermissionService.get_user_permissions(db, workspace_id, user.id)
    role = RolePermissionService.get_user_role(db, workspace_id, user.id)

    return UserPermissionsResponse(
        user_id=user.id,
        workspace_id=workspace_id,
        permissions=permissions,
        role={
            "id": str(role.id),
            "name": role.name,
            "role_type": role.role_type.value if role.role_type else None
        } if role else None
    )


@router.get("/permissions", response_model=PermissionsListResponse)
async def list_all_permissions(
    request: Request,
    category: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Get global permission catalog.

    Args:
        request: Request context
        category: Optional category filter
        db: Database session

    Returns:
        List of available permissions

    Raises:
        401: Not authenticated
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    permissions = RolePermissionService.list_permissions(db, category)

    return PermissionsListResponse(
        permissions=[PermissionResponse.from_orm(p) for p in permissions],
        count=len(permissions)
    )


@router.get("/{workspace_id}/roles", response_model=List[RoleDetailsResponse])
async def list_workspace_roles(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    List all roles in a workspace with their permissions.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        List of roles with permissions

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

    # Get all roles for workspace
    from db.models_workspace_v1 import WorkspaceRole
    roles = db.query(WorkspaceRole).filter(
        WorkspaceRole.workspace_id == workspace_id
    ).all()

    role_details = []
    for role in roles:
        permissions = RolePermissionService.get_role_permissions(db, role.id)
        permission_objs = [
            db.query(db.model.Permission).filter(
                db.model.Permission.name == perm_name
            ).first()
            for perm_name in permissions
        ]
        permission_objs = [p for p in permission_objs if p]  # Filter out None

        role_details.append(RoleDetailsResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            role_type=role.role_type.value if role.role_type else None,
            is_custom=role.is_custom,
            permissions=[PermissionResponse.from_orm(p) for p in permission_objs]
        ))

    return role_details


@router.post("/{workspace_id}/roles/{role_id}/permissions", status_code=201)
async def grant_permission(
    request: Request,
    workspace_id: UUID,
    role_id: UUID,
    payload: GrantPermissionRequest,
    db=Depends(get_db)
):
    """
    Grant a permission to a role (owner only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        role_id: Role ID
        payload: Permission ID to grant
        db: Database session

    Returns:
        Success message

    Raises:
        401: Not authenticated
        403: Not workspace owner or permission already granted
        404: Workspace or role not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can manage roles")

    try:
        RolePermissionService.grant_permission_to_role(db, role_id, payload.permission_id)
        return {"message": "Permission granted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{workspace_id}/roles/{role_id}/permissions/{permission_id}", status_code=204)
async def revoke_permission(
    request: Request,
    workspace_id: UUID,
    role_id: UUID,
    permission_id: UUID,
    db=Depends(get_db)
):
    """
    Revoke a permission from a role (owner only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        role_id: Role ID
        permission_id: Permission ID to revoke
        db: Database session

    Raises:
        401: Not authenticated
        403: Not workspace owner
        404: Workspace, role, or permission not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can manage roles")

    try:
        RolePermissionService.revoke_permission_from_role(db, role_id, permission_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
