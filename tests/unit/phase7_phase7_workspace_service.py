#!/usr/bin/env python3
"""
Unit Tests for Workspace Service - Phase 7.1 Multi-User Workspaces
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models_v2 import Base as BaseV2, User
from db.models_workspace_v1 import (
    Base as BaseWorkspace,
    Workspace, WorkspaceMember, WorkspaceRole, Permission,
    RolePermission, WorkspaceSettings, WorkspaceInvitation,
    WorkspaceRoleEnum, PermissionCategoryEnum, InvitationStatusEnum
)
from api.services.workspace_service import WorkspaceService


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    BaseV2.metadata.create_all(engine)
    BaseWorkspace.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        id=uuid4(),
        github_id=12345,
        github_login="testuser",
        github_avatar_url="https://example.com/avatar.jpg",
        github_name="Test User",
        github_email="test@example.com"
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_permissions(test_db):
    """Create test permissions."""
    permissions = []
    categories = [
        (PermissionCategoryEnum.WORKSPACE, "workspace.create"),
        (PermissionCategoryEnum.MEMBERS, "members.invite"),
        (PermissionCategoryEnum.CONVERSATIONS, "conversations.create"),
        (PermissionCategoryEnum.TASKS, "tasks.create"),
        (PermissionCategoryEnum.AUDIT, "audit.view"),
    ]

    for category, name in categories:
        perm = Permission(
            id=uuid4(),
            name=name,
            description=f"Permission for {name}",
            category=category
        )
        test_db.add(perm)
        permissions.append(perm)

    test_db.commit()
    return permissions


class TestWorkspaceCreation:
    """Test workspace creation functionality."""

    def test_create_workspace_success(self, test_db, test_user, test_permissions):
        """Test successful workspace creation."""
        workspace = WorkspaceService.create_workspace(
            test_db,
            owner_id=test_user.id,
            name="Test Workspace",
            description="A test workspace",
            is_default=True
        )

        assert workspace is not None
        assert workspace.name == "Test Workspace"
        assert workspace.owner_id == test_user.id
        assert workspace.is_default is True
        assert workspace.is_deleted is False

        # Check that default roles were created
        roles = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id
        ).all()
        assert len(roles) == 4  # Owner, Admin, Developer, Viewer

        # Check that owner is a member
        member = test_db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == test_user.id
        ).first()
        assert member is not None
        assert member.is_active is True

        # Check that workspace settings were created
        settings = test_db.query(WorkspaceSettings).filter(
            WorkspaceSettings.workspace_id == workspace.id
        ).first()
        assert settings is not None

    def test_create_workspace_invalid_owner(self, test_db):
        """Test workspace creation with non-existent owner."""
        with pytest.raises(ValueError):
            WorkspaceService.create_workspace(
                test_db,
                owner_id=uuid4(),
                name="Test Workspace"
            )


class TestWorkspaceRetrieval:
    """Test workspace retrieval functionality."""

    def test_get_workspace(self, test_db, test_user, test_permissions):
        """Test getting a workspace by ID."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        retrieved = WorkspaceService.get_workspace(test_db, workspace.id)
        assert retrieved is not None
        assert retrieved.id == workspace.id
        assert retrieved.name == "Test Workspace"

    def test_get_deleted_workspace_returns_none(self, test_db, test_user, test_permissions):
        """Test that deleted workspaces are not returned."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        WorkspaceService.delete_workspace(test_db, workspace.id)

        retrieved = WorkspaceService.get_workspace(test_db, workspace.id)
        assert retrieved is None

    def test_list_user_workspaces(self, test_db, test_user, test_permissions):
        """Test listing workspaces for a user."""
        ws1 = WorkspaceService.create_workspace(
            test_db, test_user.id, "Workspace 1"
        )
        ws2 = WorkspaceService.create_workspace(
            test_db, test_user.id, "Workspace 2"
        )

        workspaces = WorkspaceService.list_user_workspaces(test_db, test_user.id)

        assert len(workspaces) == 2
        assert any(w.id == ws1.id for w in workspaces)
        assert any(w.id == ws2.id for w in workspaces)


class TestWorkspaceMembership:
    """Test workspace membership functionality."""

    def test_add_member(self, test_db, test_user, test_permissions):
        """Test adding a member to a workspace."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        # Create another user
        new_user = User(
            id=uuid4(),
            github_id=54321,
            github_login="newuser",
            github_email="new@example.com"
        )
        test_db.add(new_user)
        test_db.commit()

        # Get developer role
        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        member = WorkspaceService.add_member(
            test_db,
            workspace.id,
            new_user.id,
            dev_role.id,
            invited_by_id=test_user.id
        )

        assert member is not None
        assert member.user_id == new_user.id
        assert member.role_id == dev_role.id
        assert member.is_active is True

    def test_add_duplicate_member_fails(self, test_db, test_user, test_permissions):
        """Test that adding duplicate member fails."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        new_user = User(
            id=uuid4(),
            github_id=54321,
            github_login="newuser",
            github_email="new@example.com"
        )
        test_db.add(new_user)
        test_db.commit()

        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        WorkspaceService.add_member(
            test_db, workspace.id, new_user.id, dev_role.id
        )

        with pytest.raises(ValueError):
            WorkspaceService.add_member(
                test_db, workspace.id, new_user.id, dev_role.id
            )

    def test_remove_member(self, test_db, test_user, test_permissions):
        """Test removing a member from a workspace."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        new_user = User(
            id=uuid4(),
            github_id=54321,
            github_login="newuser",
            github_email="new@example.com"
        )
        test_db.add(new_user)
        test_db.commit()

        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        WorkspaceService.add_member(
            test_db, workspace.id, new_user.id, dev_role.id
        )

        member = WorkspaceService.remove_member(test_db, workspace.id, new_user.id)

        assert member.is_active is False

    def test_remove_owner_fails(self, test_db, test_user, test_permissions):
        """Test that removing owner fails."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        with pytest.raises(ValueError):
            WorkspaceService.remove_member(test_db, workspace.id, test_user.id)


class TestWorkspaceRoles:
    """Test workspace role functionality."""

    def test_update_member_role(self, test_db, test_user, test_permissions):
        """Test updating a member's role."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        new_user = User(
            id=uuid4(),
            github_id=54321,
            github_login="newuser",
            github_email="new@example.com"
        )
        test_db.add(new_user)
        test_db.commit()

        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        admin_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.ADMIN
        ).first()

        WorkspaceService.add_member(
            test_db, workspace.id, new_user.id, dev_role.id
        )

        member = WorkspaceService.update_member_role(
            test_db, workspace.id, new_user.id, admin_role.id
        )

        assert member.role_id == admin_role.id

    def test_get_user_role(self, test_db, test_user, test_permissions):
        """Test getting a user's role in a workspace."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        role = WorkspaceService.get_user_role(test_db, workspace.id, test_user.id)

        assert role is not None
        assert role.role_type == WorkspaceRoleEnum.OWNER


class TestWorkspaceInvitations:
    """Test workspace invitation functionality."""

    def test_invite_user(self, test_db, test_user, test_permissions):
        """Test sending an invitation."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        invitation = WorkspaceService.invite_user(
            test_db,
            workspace.id,
            "invite@example.com",
            dev_role.id,
            test_user.id
        )

        assert invitation is not None
        assert invitation.email == "invite@example.com"
        assert invitation.status == InvitationStatusEnum.PENDING
        assert invitation.expires_at > datetime.utcnow()

    def test_accept_invitation(self, test_db, test_user, test_permissions):
        """Test accepting an invitation."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        new_user = User(
            id=uuid4(),
            github_id=54321,
            github_login="newuser",
            github_email="new@example.com"
        )
        test_db.add(new_user)
        test_db.commit()

        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        invitation = WorkspaceService.invite_user(
            test_db,
            workspace.id,
            new_user.github_email,
            dev_role.id,
            test_user.id
        )

        member = WorkspaceService.accept_invitation(
            test_db,
            invitation.invitation_token,
            new_user.id
        )

        assert member.user_id == new_user.id
        assert member.workspace_id == workspace.id

        # Check invitation was marked as accepted
        test_db.refresh(invitation)
        assert invitation.status == InvitationStatusEnum.ACCEPTED
        assert invitation.accepted_by_id == new_user.id

    def test_accept_expired_invitation_fails(self, test_db, test_user, test_permissions):
        """Test that accepting expired invitation fails."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        dev_role = test_db.query(WorkspaceRole).filter(
            WorkspaceRole.workspace_id == workspace.id,
            WorkspaceRole.role_type == WorkspaceRoleEnum.DEVELOPER
        ).first()

        # Create expired invitation
        invitation = WorkspaceInvitation(
            id=uuid4(),
            workspace_id=workspace.id,
            email="expire@example.com",
            invited_by_id=test_user.id,
            role_id=dev_role.id,
            invitation_token=str(uuid4()),
            status=InvitationStatusEnum.PENDING,
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        test_db.add(invitation)
        test_db.commit()

        new_user = User(
            id=uuid4(),
            github_id=54321,
            github_login="newuser",
            github_email="new@example.com"
        )
        test_db.add(new_user)
        test_db.commit()

        with pytest.raises(ValueError):
            WorkspaceService.accept_invitation(
                test_db,
                invitation.invitation_token,
                new_user.id
            )


class TestWorkspaceUtilities:
    """Test workspace utility functions."""

    def test_is_owner(self, test_db, test_user, test_permissions):
        """Test owner check."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        assert WorkspaceService.is_owner(test_db, workspace.id, test_user.id) is True

    def test_is_member(self, test_db, test_user, test_permissions):
        """Test member check."""
        workspace = WorkspaceService.create_workspace(
            test_db, test_user.id, "Test Workspace"
        )

        # Owner is also a member
        assert WorkspaceService.is_member(test_db, workspace.id, test_user.id) is True

        # Non-member
        other_user = User(
            id=uuid4(),
            github_id=99999,
            github_login="other",
            github_email="other@example.com"
        )
        test_db.add(other_user)
        test_db.commit()

        assert WorkspaceService.is_member(test_db, workspace.id, other_user.id) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
