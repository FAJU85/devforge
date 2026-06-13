#!/usr/bin/env python3
"""
Role-Based Access Control (RBAC) Service - Phase 7.2 RBAC

Provides permission checking, role assignment, and permission catalog management.
"""

from typing import Set, List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from db.models_workspace_v1 import (
    WorkspaceRole, Permission, RolePermission,
    WorkspaceMember, WorkspaceRoleEnum, PermissionCategoryEnum
)

logger = logging.getLogger(__name__)


class RolePermissionService:
    """Service for managing roles and permissions in workspaces."""

    # Predefined permission names
    PERMISSION_WORKSPACE_CREATE = "workspace.create"
    PERMISSION_WORKSPACE_DELETE = "workspace.delete"
    PERMISSION_WORKSPACE_ARCHIVE = "workspace.archive"
    PERMISSION_WORKSPACE_EDIT = "workspace.edit"

    PERMISSION_MEMBERS_INVITE = "members.invite"
    PERMISSION_MEMBERS_REMOVE = "members.remove"
    PERMISSION_MEMBERS_UPDATE_ROLE = "members.update_role"
    PERMISSION_MEMBERS_VIEW = "members.view"

    PERMISSION_CONVERSATIONS_CREATE = "conversations.create"
    PERMISSION_CONVERSATIONS_EDIT = "conversations.edit"
    PERMISSION_CONVERSATIONS_DELETE = "conversations.delete"
    PERMISSION_CONVERSATIONS_VIEW = "conversations.view"

    PERMISSION_TASKS_CREATE = "tasks.create"
    PERMISSION_TASKS_EDIT = "tasks.edit"
    PERMISSION_TASKS_EXECUTE = "tasks.execute"
    PERMISSION_TASKS_DELETE = "tasks.delete"
    PERMISSION_TASKS_VIEW = "tasks.view"

    PERMISSION_REPOSITORIES_CONNECT = "repositories.connect"
    PERMISSION_REPOSITORIES_MANAGE = "repositories.manage"
    PERMISSION_REPOSITORIES_VIEW = "repositories.view"

    PERMISSION_AUDIT_VIEW = "audit.view"
    PERMISSION_AUDIT_EXPORT = "audit.export"

    PERMISSION_SETTINGS_EDIT = "settings.edit"
    PERMISSION_SETTINGS_MANAGE = "settings.manage"

    @staticmethod
    def check_permission(
        db: Session,
        workspace_id: UUID,
        user_id: UUID,
        permission_name: str
    ) -> bool:
        """
        Check if a user has a specific permission in a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID
            permission_name: Permission name (e.g., "workspace.create")

        Returns:
            True if user has permission, False otherwise
        """
        # Get user's membership and role in workspace
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        if not member:
            return False

        # Get role and its permissions
        role = member.role
        if not role:
            return False

        # Check if permission exists in role
        has_permission = db.query(RolePermission).join(
            Permission,
            RolePermission.permission_id == Permission.id
        ).filter(
            RolePermission.role_id == role.id,
            Permission.name == permission_name
        ).first() is not None

        return has_permission

    @staticmethod
    def get_user_permissions(
        db: Session,
        workspace_id: UUID,
        user_id: UUID
    ) -> Set[str]:
        """
        Get all permissions for a user in a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID

        Returns:
            Set of permission names
        """
        # Get user's membership and role in workspace
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        if not member:
            return set()

        # Get all permissions for the user's role
        permissions = db.query(Permission).join(
            RolePermission,
            Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id == member.role_id
        ).all()

        return {perm.name for perm in permissions}

    @staticmethod
    def get_user_role(
        db: Session,
        workspace_id: UUID,
        user_id: UUID
    ) -> Optional[WorkspaceRole]:
        """
        Get the role of a user in a workspace.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID

        Returns:
            WorkspaceRole or None
        """
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        return member.role if member else None

    @staticmethod
    def get_role_permissions(
        db: Session,
        role_id: UUID
    ) -> Set[str]:
        """
        Get all permissions for a role.

        Args:
            db: Database session
            role_id: Role ID

        Returns:
            Set of permission names
        """
        permissions = db.query(Permission).join(
            RolePermission,
            Permission.id == RolePermission.permission_id
        ).filter(
            RolePermission.role_id == role_id
        ).all()

        return {perm.name for perm in permissions}

    @staticmethod
    def grant_permission_to_role(
        db: Session,
        role_id: UUID,
        permission_id: UUID
    ) -> RolePermission:
        """
        Grant a permission to a role.

        Args:
            db: Database session
            role_id: Role ID
            permission_id: Permission ID

        Returns:
            Created RolePermission instance

        Raises:
            ValueError: If role or permission not found, or already granted
        """
        role = db.query(WorkspaceRole).filter(
            WorkspaceRole.id == role_id
        ).first()
        if not role:
            raise ValueError(f"Role {role_id} not found")

        permission = db.query(Permission).filter(
            Permission.id == permission_id
        ).first()
        if not permission:
            raise ValueError(f"Permission {permission_id} not found")

        # Check if already granted
        existing = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        if existing:
            raise ValueError(f"Permission already granted to role")

        role_perm = RolePermission(
            role_id=role_id,
            permission_id=permission_id
        )
        db.add(role_perm)
        db.commit()

        logger.info(f"Granted permission {permission.name} to role {role_id}")
        return role_perm

    @staticmethod
    def revoke_permission_from_role(
        db: Session,
        role_id: UUID,
        permission_id: UUID
    ) -> None:
        """
        Revoke a permission from a role.

        Args:
            db: Database session
            role_id: Role ID
            permission_id: Permission ID

        Raises:
            ValueError: If role permission not found
        """
        role_perm = db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        if not role_perm:
            raise ValueError(f"Permission not granted to role")

        db.delete(role_perm)
        db.commit()

        logger.info(f"Revoked permission from role {role_id}")

    @staticmethod
    def get_permission_by_name(
        db: Session,
        name: str
    ) -> Optional[Permission]:
        """Get a permission by name."""
        return db.query(Permission).filter(
            Permission.name == name
        ).first()

    @staticmethod
    def list_permissions(
        db: Session,
        category: Optional[str] = None
    ) -> List[Permission]:
        """
        List all permissions, optionally filtered by category.

        Args:
            db: Database session
            category: Optional category filter

        Returns:
            List of Permission instances
        """
        query = db.query(Permission)

        if category:
            query = query.filter(Permission.category == category)

        return query.all()

    @staticmethod
    def is_owner(
        db: Session,
        workspace_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if user is workspace owner.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID

        Returns:
            True if user is owner
        """
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        if not member or not member.role:
            return False

        return member.role.role_type == WorkspaceRoleEnum.OWNER

    @staticmethod
    def is_admin(
        db: Session,
        workspace_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if user is admin (owner or admin role).

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID

        Returns:
            True if user is owner or admin
        """
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        if not member or not member.role:
            return False

        return member.role.role_type in [
            WorkspaceRoleEnum.OWNER,
            WorkspaceRoleEnum.ADMIN
        ]

    @staticmethod
    def is_developer(
        db: Session,
        workspace_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if user is developer or higher.

        Args:
            db: Database session
            workspace_id: Workspace ID
            user_id: User ID

        Returns:
            True if user is developer or higher
        """
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        if not member or not member.role:
            return False

        return member.role.role_type in [
            WorkspaceRoleEnum.OWNER,
            WorkspaceRoleEnum.ADMIN,
            WorkspaceRoleEnum.DEVELOPER
        ]

    @staticmethod
    def get_role_hierarchy_level(role: Optional[WorkspaceRole]) -> int:
        """
        Get hierarchy level of a role (for comparison).

        Args:
            role: WorkspaceRole instance

        Returns:
            Hierarchy level: 0=Owner, 1=Admin, 2=Developer, 3=Viewer, -1=Unknown
        """
        if not role:
            return -1

        role_levels = {
            WorkspaceRoleEnum.OWNER: 0,
            WorkspaceRoleEnum.ADMIN: 1,
            WorkspaceRoleEnum.DEVELOPER: 2,
            WorkspaceRoleEnum.VIEWER: 3,
        }

        return role_levels.get(role.role_type, -1)

    @staticmethod
    def can_manage_user(
        db: Session,
        workspace_id: UUID,
        manager_user_id: UUID,
        target_user_id: UUID
    ) -> bool:
        """
        Check if manager can manage target user (hierarchy-based).

        Args:
            db: Database session
            workspace_id: Workspace ID
            manager_user_id: User ID trying to manage
            target_user_id: User being managed

        Returns:
            True if manager can manage target
        """
        manager_role = RolePermissionService.get_user_role(
            db, workspace_id, manager_user_id
        )
        target_role = RolePermissionService.get_user_role(
            db, workspace_id, target_user_id
        )

        manager_level = RolePermissionService.get_role_hierarchy_level(manager_role)
        target_level = RolePermissionService.get_role_hierarchy_level(target_role)

        # Can manage only if at higher level
        return manager_level < target_level
