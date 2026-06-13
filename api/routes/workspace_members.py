#!/usr/bin/env python3
"""
Workspace Members Routes - Phase 7.1 Multi-User Workspaces

Endpoints for managing workspace members and invitations.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from api.services.database_service import get_db
from api.services.workspace_service import WorkspaceService
from api.services.auth_service import get_current_user_from_request

router = APIRouter(prefix="/api/workspaces", tags=["workspace-members"])


class WorkspaceRoleResponse(BaseModel):
    """Workspace role response"""
    id: UUID
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    """Workspace member response"""
    id: UUID
    user_id: UUID
    role: WorkspaceRoleResponse
    joined_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class MembersListResponse(BaseModel):
    """List of members"""
    members: List[MemberResponse]
    count: int


class AddMemberRequest(BaseModel):
    """Add member request"""
    user_id: UUID
    role_id: UUID


class UpdateMemberRoleRequest(BaseModel):
    """Update member role request"""
    role_id: UUID


class InviteUserRequest(BaseModel):
    """Invite user request"""
    email: EmailStr
    role_id: UUID


class InvitationResponse(BaseModel):
    """Workspace invitation response"""
    id: UUID
    workspace_id: UUID
    email: str
    status: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class InvitationsListResponse(BaseModel):
    """List of invitations"""
    invitations: List[InvitationResponse]
    count: int


class AcceptInvitationRequest(BaseModel):
    """Accept invitation request"""
    invitation_token: str


@router.get("/{workspace_id}/members", response_model=MembersListResponse)
async def list_members(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    List all members of a workspace.

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        List of workspace members

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

    members = WorkspaceService.list_members(db, workspace_id)
    return MembersListResponse(
        members=[MemberResponse(
            id=m.id,
            user_id=m.user_id,
            role=WorkspaceRoleResponse.from_orm(m.role),
            joined_at=m.joined_at,
            is_active=m.is_active
        ) for m in members],
        count=len(members)
    )


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(
    request: Request,
    workspace_id: UUID,
    payload: AddMemberRequest,
    db=Depends(get_db)
):
    """
    Add a member to a workspace (owner/admin only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        payload: Add member payload
        db: Database session

    Returns:
        Added member

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Workspace, user, or role not found
        409: User already a member
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can add members")

    try:
        member = WorkspaceService.add_member(
            db,
            workspace_id,
            payload.user_id,
            payload.role_id,
            invited_by_id=user.id
        )
        return MemberResponse(
            id=member.id,
            user_id=member.user_id,
            role=WorkspaceRoleResponse.from_orm(member.role),
            joined_at=member.joined_at,
            is_active=member.is_active
        )
    except ValueError as e:
        if "already a member" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{workspace_id}/members/{user_id}", response_model=MemberResponse)
async def update_member_role(
    request: Request,
    workspace_id: UUID,
    user_id: UUID,
    payload: UpdateMemberRoleRequest,
    db=Depends(get_db)
):
    """
    Update a member's role (owner/admin only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        user_id: User ID to update
        payload: Update payload
        db: Database session

    Returns:
        Updated member

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Workspace, member, or role not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can update member roles")

    try:
        member = WorkspaceService.update_member_role(
            db,
            workspace_id,
            user_id,
            payload.role_id
        )
        return MemberResponse(
            id=member.id,
            user_id=member.user_id,
            role=WorkspaceRoleResponse.from_orm(member.role),
            joined_at=member.joined_at,
            is_active=member.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    request: Request,
    workspace_id: UUID,
    user_id: UUID,
    db=Depends(get_db)
):
    """
    Remove a member from a workspace (owner only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        user_id: User ID to remove
        db: Database session

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Workspace or member not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can remove members")

    try:
        WorkspaceService.remove_member(db, workspace_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{workspace_id}/invitations", response_model=InvitationResponse, status_code=201)
async def invite_user(
    request: Request,
    workspace_id: UUID,
    payload: InviteUserRequest,
    db=Depends(get_db)
):
    """
    Send an invitation to join a workspace (owner/admin only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        payload: Invitation payload
        db: Database session

    Returns:
        Created invitation

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Workspace or role not found
        409: Pending invitation already exists
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can send invitations")

    try:
        invitation = WorkspaceService.invite_user(
            db,
            workspace_id,
            payload.email,
            payload.role_id,
            user.id
        )
        return InvitationResponse.from_orm(invitation)
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{workspace_id}/invitations", response_model=InvitationsListResponse)
async def list_invitations(
    request: Request,
    workspace_id: UUID,
    db=Depends(get_db)
):
    """
    List pending invitations for a workspace (owner/admin only).

    Args:
        request: Request context
        workspace_id: Workspace ID
        db: Database session

    Returns:
        List of pending invitations

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Workspace not found
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    workspace = WorkspaceService.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if not WorkspaceService.is_owner(db, workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can view invitations")

    invitations = WorkspaceService.list_pending_invitations(db, workspace_id)
    return InvitationsListResponse(
        invitations=[InvitationResponse.from_orm(inv) for inv in invitations],
        count=len(invitations)
    )


@router.post("/invitations/accept", status_code=200)
async def accept_invitation(
    request: Request,
    payload: AcceptInvitationRequest,
    db=Depends(get_db)
):
    """
    Accept an invitation and join a workspace.

    Args:
        request: Request context
        payload: Acceptance payload with invitation token
        db: Database session

    Returns:
        Confirmation message

    Raises:
        401: Not authenticated
        400: Invalid, expired, or already accepted invitation
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        member = WorkspaceService.accept_invitation(
            db,
            payload.invitation_token,
            user.id
        )
        return {
            "message": "Invitation accepted successfully",
            "workspace_id": str(member.workspace_id),
            "role_id": str(member.role_id)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/invitations/{invitation_id}", status_code=204)
async def cancel_invitation(
    request: Request,
    invitation_id: UUID,
    db=Depends(get_db)
):
    """
    Cancel a pending invitation (owner only).

    Args:
        request: Request context
        invitation_id: Invitation ID
        db: Database session

    Raises:
        401: Not authenticated
        403: Insufficient permissions
        404: Invitation not found or not pending
    """
    user = await get_current_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    invitation = WorkspaceService.get_invitation(db, invitation_id)
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    workspace = WorkspaceService.get_workspace(db, invitation.workspace_id)
    if not workspace or not WorkspaceService.is_owner(db, invitation.workspace_id, user.id):
        raise HTTPException(status_code=403, detail="Only workspace owner can cancel invitations")

    try:
        WorkspaceService.cancel_invitation(db, invitation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
