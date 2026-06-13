#!/usr/bin/env python3
"""
Workspace Service - Phase 7.1 Multi-User Workspaces

Provides workspace CRUD operations, member management, and ownership/membership validation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
import logging

from db.models_workspace_v1 import (
    Workspace, WorkspaceMember, WorkspaceRole, WorkspaceSettings,
    WorkspaceInvitation, Permission, RolePermission, WorkspaceRoleEnum,
    PermissionCategoryEnum, InvitationStatusEnum
)
from db.models_v2 import User

logger = logging.getLogger(__name__)


class WorkspaceService:
    """Service for managing workspaces, members, and roles."""

    @staticmethod
    def create_workspace(
        db: Session,
        owner_id: UUID,
        name: str,
        description: Optional[str] = None,
        is_default: bool = False
    ) -> Workspace:
        """
        Create a new workspace.

        Args:
            db: Database session
            owner_id: User ID of workspace owner
            name: Workspace name
            description: Optional workspace description
            is_default: Whether this is the user's default workspace

        Returns:
            Created Workspace instance

        Raises:
            Exception: If owner doesn't exist
        """
        owner = db.query(User).filter(User.id == owner_id, User.is_deleted == False).first()
        if not owner:
            raise ValueError(f"User {owner_id} not found")

        workspace = Workspace(
            id=uuid4(),
            owner_id=owner_id,
            name=name,
            description=description,
            is_default=is_default,
            is_deleted=False,
            is_archived=False
        )

        db.add(workspace)
        db.flush()

        # Create workspace settings
        settings = WorkspaceSettings(
            id=uuid4(),
            workspace_id=workspace.id
        )
        db.add(settings)
        db.flush()

        # Create default roles (Owner, Admin, Developer, Viewer)
        WorkspaceService._create_default_roles(db, workspace.id)

        # Add owner as member with OWNER role
        owner_role = db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.OWNER
        ).first()

        member = WorkspaceMember(
            id=uuid4(),
            workspace_id=workspace.id,
            user_id=owner_id,
            role_id=owner_role.id,
            joined_at=datetime.utcnow(),
            is_active=True
        )
        db.add(member)
        db.commit()

        logger.info(f"Created workspace {workspace.id} for user {owner_id}")
        return workspace

    @staticmethod
    def _create_default_roles(db: Session, workspace_id: UUID) -> None:
        """Create default roles for a workspace."""
        roles_config = [
            {
                "name": "Owner",
                "role_type": WorkspaceRoleEnum.OWNER,
                "description": "Full control - create, manage, and delete workspace",
                "is_custom": False,
                "is_default": False,
            },
            {
                "name": "Admin",
                "role_type": WorkspaceRoleEnum.ADMIN,
                "description": "Manage members and view audit logs",
                "is_custom": False,
                "is_default": False,
            },
            {
                "name": "Developer",
                "role_type": WorkspaceRoleEnum.DEVELOPER,
                "description": "Create and edit conversations, tasks, and repositories",
                "is_custom": False,
                "is_default": True,  # New members get this role by default
            },
            {
                "name": "Viewer",
                "role_type": WorkspaceRoleEnum.VIEWER,
                "description": "Read-only access to conversations and tasks",
                "is_custom": False,
                "is_default": False,
            },
        ]

        # Get permission catalog
        permissions = db.query(Permission).all()
        role_permission_map = {
            WorkspaceRoleEnum.OWNER: permissions,  # Owner has all permissions
            WorkspaceRoleEnum.ADMIN: [
                p for p in permissions if p.category in [
                    PermissionCategoryEnum.MEMBERS,
                    PermissionCategoryEnum.AUDIT,
                    PermissionCategoryEnum.SETTINGS
                ]
            ],
            WorkspaceRoleEnum.DEVELOPER: [
                p for p in permissions if p.category in [
                    PermissionCategoryEnum.CONVERSATIONS,
                    PermissionCategoryEnum.TASKS,
                    PermissionCategoryEnum.REPOSITORIES,
                    PermissionCategoryEnum.AUDIT
                ]
            ],
            WorkspaceRoleEnum.VIEWER: [
                p for p in permissions if p.category in [
                    PermissionCategoryEnum.AUDIT
                ] and "view" in p.name.lower()
            ],
        }

        for role_config in roles_config:
            role = WorkspaceRole(
                id=uuid4(),
                workspace_id=workspace_id,
                name=role_config["name"],
                role_type=role_config["role_type"],
                description=role_config["description"],
                is_custom=role_config["is_custom"],
                is_default=role_config["is_default"]
            )
            db.add(role)
            db.flush()

            # Grant permissions
            permissions_for_role = role_permission_map.get(role_config["role_type"], [])
            for perm in permissions_for_role:
                role_perm = RolePermission(
                    id=uuid4(),
                    role_id=role.id,
                    permission_id=perm.id
                )
                db.add(role_perm)

        db.flush()

    @staticmethod
    def get_workspace(db: Session, workspace_id: UUID) -> Optional[Workspace]:
        """Get workspace by ID."""
        return db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == False
        ).first()

    @staticmethod
    def list_user_workspaces(db: Session, user_id: UUID) -> List[Workspace]:
        """
        List all workspaces the user is a member of or owns.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of Workspace instances
        """
        # Get workspaces user owns or is a member of
        workspaces = db.query(Workspace).join(
            WorkspaceMember,
            (Workspace.id == WorkspaceMember.workspace_id) | (Workspace.owner_id == user_id)
        ).filter(
            (WorkspaceMember.user_id == user_id) | (Workspace.owner_id == user_id),
            Workspace.is_deleted == False
        ).distinct().all()

        return workspaces

    @staticmethod
    def update_workspace(
        db: Session,
        workspace_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Workspace:
        """Update workspace details."""
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        if avatar_url is not None:
            workspace.avatar_url = avatar_url

        workspace.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Updated workspace {workspace_id}")
        return workspace

    @staticmethod
    def delete_workspace(db: Session, workspace_id: UUID, reason: Optional[str] = None) -> Workspace:
        """
        Soft delete a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID to delete
            reason: Optional reason for deletion

        Returns:
            Deleted Workspace instance
        """
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        workspace.is_deleted = True
        workspace.deleted_at = datetime.utcnow()
        db.commit()

        logger.info(f"Deleted workspace {workspace_id}")
        return workspace

    @staticmethod
    def add_member(
        db: Session,
        workspace_id: UUID,
        user_id: UUID,
        role_id: UUID,
        invited_by_id: Optional[UUID] = None
    ) -> WorkspaceMember:
        """
        Add a user to a workspace with a specific role.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID to add
            role_id: Role ID to assign
            invited_by_id: Optional user ID of the inviter

        Returns:
            Created WorkspaceMember instance

        Raises:
            ValueError: If user or workspace not found, or user already a member
        """
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check if user is already a member
        existing = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()
        if existing:
            raise ValueError(f"User {user_id} is already a member of workspace {workspace_id}")

        # Check role exists
        role = db.query(WorkspaceRole).filter(
            WorkspaceRole.id == role_id,
            WorkspaceRole.workspace_id == workspace_id
        ).first()
        if not role:
            raise ValueError(f"Role {role_id} not found in workspace {workspace_id}")

        member = WorkspaceMember(
            id=uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role_id,
            invited_by_id=invited_by_id,
            is_active=True
        )
        db.add(member)
        db.commit()

        logger.info(f"Added user {user_id} to workspace {workspace_id} with role {role_id}")
        return member

    @staticmethod
    def remove_member(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
        """
        Remove a user from a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID to remove

        Returns:
            Updated WorkspaceMember instance

        Raises:
            ValueError: If member not found, or trying to remove workspace owner
        """
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        # Don't allow removing workspace owner
        if workspace.owner_id == user_id:
            raise ValueError("Cannot remove workspace owner")

        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()
        if not member:
            raise ValueError(f"User {user_id} is not an active member of workspace {workspace_id}")

        member.is_active = False
        db.commit()

        logger.info(f"Removed user {user_id} from workspace {workspace_id}")
        return member

    @staticmethod
    def update_member_role(
        db: Session,
        workspace_id: UUID,
        user_id: UUID,
        new_role_id: UUID
    ) -> WorkspaceMember:
        """
        Update a member's role.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID
            new_role_id: New role ID

        Returns:
            Updated WorkspaceMember instance

        Raises:
            ValueError: If member or role not found, or trying to change owner role
        """
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        if workspace.owner_id == user_id:
            raise ValueError("Cannot change owner role")

        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()
        if not member:
            raise ValueError(f"User {user_id} is not an active member of workspace {workspace_id}")

        role = db.query(WorkspaceRole).filter(
            WorkspaceRole.id == new_role_id,
            WorkspaceRole.workspace_id == workspace_id
        ).first()
        if not role:
            raise ValueError(f"Role {new_role_id} not found in workspace {workspace_id}")

        member.role_id = new_role_id
        db.commit()

        logger.info(f"Updated user {user_id} role in workspace {workspace_id} to {new_role_id}")
        return member

    @staticmethod
    def get_member(db: Session, workspace_id: UUID, user_id: UUID) -> Optional[WorkspaceMember]:
        """Get a workspace member."""
        return db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

    @staticmethod
    def list_members(db: Session, workspace_id: UUID) -> List[WorkspaceMember]:
        """List all active members of a workspace."""
        return db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).all()

    @staticmethod
    def is_owner(db: Session, workspace_id: UUID, user_id: UUID) -> bool:
        """Check if user is the workspace owner."""
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        return workspace is not None and workspace.owner_id == user_id

    @staticmethod
    def is_member(db: Session, workspace_id: UUID, user_id: UUID) -> bool:
        """Check if user is an active member of the workspace."""
        member = WorkspaceService.get_member(db, workspace_id, user_id)
        return member is not None

    @staticmethod
    def get_user_role(db: Session, workspace_id: UUID, user_id: UUID) -> Optional[WorkspaceRole]:
        """Get the role of a user in a workspace."""
        member = WorkspaceService.get_member(db, workspace_id, user_id)
        return member.role if member else None

    @staticmethod
    def invite_user(
        db: Session,
        workspace_id: UUID,
        email: str,
        role_id: UUID,
        invited_by_id: UUID
    ) -> WorkspaceInvitation:
        """
        Create an invitation for a user to join a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            email: Email to invite
            role_id: Role to assign upon acceptance
            invited_by_id: User ID of the inviter

        Returns:
            Created WorkspaceInvitation instance

        Raises:
            ValueError: If workspace or role not found
        """
        workspace = WorkspaceService.get_workspace(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        role = db.query(WorkspaceRole).filter(
            WorkspaceRole.id == role_id,
            WorkspaceRole.workspace_id == workspace_id
        ).first()
        if not role:
            raise ValueError(f"Role {role_id} not found")

        # Check for existing pending invitation
        existing = db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == email,
            WorkspaceInvitation.status == InvitationStatusEnum.PENDING
        ).first()
        if existing:
            raise ValueError(f"Pending invitation already exists for {email}")

        invitation = WorkspaceInvitation(
            id=uuid4(),
            workspace_id=workspace_id,
            email=email,
            role_id=role_id,
            invited_by_id=invited_by_id,
            invitation_token=str(uuid4()),
            status=InvitationStatusEnum.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(invitation)
        db.commit()

        logger.info(f"Created invitation for {email} to workspace {workspace_id}")
        return invitation

    @staticmethod
    def accept_invitation(
        db: Session,
        invitation_token: str,
        user_id: UUID
    ) -> WorkspaceMember:
        """
        Accept an invitation and add user to workspace.

        Args:
            db: Database session
            invitation_token: Invitation token
            user_id: User ID accepting the invitation

        Returns:
            Created WorkspaceMember instance

        Raises:
            ValueError: If invitation not found, expired, or already accepted
        """
        invitation = db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.invitation_token == invitation_token
        ).first()
        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.status != InvitationStatusEnum.PENDING:
            raise ValueError(f"Invitation is {invitation.status}")

        if invitation.expires_at < datetime.utcnow():
            raise ValueError("Invitation has expired")

        # Add user to workspace
        member = WorkspaceService.add_member(
            db,
            invitation.workspace_id,
            user_id,
            invitation.role_id,
            invited_by_id=invitation.invited_by_id
        )

        # Mark invitation as accepted
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.accepted_by_id = user_id
        invitation.accepted_at = datetime.utcnow()
        db.commit()

        logger.info(f"User {user_id} accepted invitation to workspace {invitation.workspace_id}")
        return member

    @staticmethod
    def get_invitation(db: Session, invitation_id: UUID) -> Optional[WorkspaceInvitation]:
        """Get an invitation by ID."""
        return db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.id == invitation_id
        ).first()

    @staticmethod
    def list_pending_invitations(db: Session, workspace_id: UUID) -> List[WorkspaceInvitation]:
        """List pending invitations for a workspace."""
        return db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.status == InvitationStatusEnum.PENDING
        ).all()

    @staticmethod
    def cancel_invitation(db: Session, invitation_id: UUID) -> WorkspaceInvitation:
        """Cancel a pending invitation."""
        invitation = WorkspaceService.get_invitation(db, invitation_id)
        if not invitation:
            raise ValueError(f"Invitation {invitation_id} not found")

        if invitation.status != InvitationStatusEnum.PENDING:
            raise ValueError(f"Cannot cancel invitation with status {invitation.status}")

        invitation.status = InvitationStatusEnum.REJECTED
        db.commit()

        logger.info(f"Cancelled invitation {invitation_id}")
        return invitation
