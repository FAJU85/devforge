"""DevForge Workspace Models (Phase 7: Enterprise Features)

Provides multi-user workspaces with role-based access control, member management,
and workspace isolation for conversations, tasks, repositories, and configurations.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Text, Index, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

Base = declarative_base()


class WorkspaceRoleEnum(str, enum.Enum):
    """Predefined workspace roles"""
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class PermissionCategoryEnum(str, enum.Enum):
    """Permission categories for organization"""
    WORKSPACE = "workspace"
    MEMBERS = "members"
    CONVERSATIONS = "conversations"
    TASKS = "tasks"
    REPOSITORIES = "repositories"
    AUDIT = "audit"
    SETTINGS = "settings"


class InvitationStatusEnum(str, enum.Enum):
    """Workspace invitation status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Workspace(Base):
    """Multi-user workspace container for organizing users, conversations, tasks, and configurations."""
    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_owner_id_created_at", "owner_id", "created_at"),
        Index("ix_workspaces_is_deleted_created_at", "is_deleted", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)  # Default workspace for owner
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_workspaces")
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    roles = relationship("WorkspaceRole", back_populates="workspace", cascade="all, delete-orphan")
    settings = relationship("WorkspaceSettings", back_populates="workspace", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("WorkspaceAuditLog", back_populates="workspace", cascade="all, delete-orphan")
    invitations = relationship("WorkspaceInvitation", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    """User membership in a workspace with role assignment."""
    __tablename__ = "workspace_members"
    __table_args__ = (
        Index("ix_workspace_members_workspace_id_user_id", "workspace_id", "user_id", unique=True),
        Index("ix_workspace_members_user_id_created_at", "user_id", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("workspace_roles.id", ondelete="RESTRICT"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], backref="workspace_memberships")
    role = relationship("WorkspaceRole", back_populates="members")
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class WorkspaceRole(Base):
    """Workspace-specific role with granular permissions."""
    __tablename__ = "workspace_roles"
    __table_args__ = (
        Index("ix_workspace_roles_workspace_id_name", "workspace_id", "name", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    role_type = Column(Enum(WorkspaceRoleEnum), nullable=True)  # NULL for custom roles, specific enum for predefined
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)  # For new members, e.g., DEVELOPER
    is_custom = Column(Boolean, default=False, nullable=False)  # Distinguish custom vs. built-in roles
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="roles")
    members = relationship("WorkspaceMember", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """Global permission catalog - defines all possible permissions across all workspaces."""
    __tablename__ = "permissions"
    __table_args__ = (
        Index("ix_permissions_category_name", "category", "name", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)  # e.g., "workspace.create", "members.invite"
    description = Column(Text, nullable=True)
    category = Column(Enum(PermissionCategoryEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    """Maps permissions to roles - join table for role-permission relationship."""
    __tablename__ = "role_permissions"
    __table_args__ = (
        Index("ix_role_permissions_role_id_permission_id", "role_id", "permission_id", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("workspace_roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    role = relationship("WorkspaceRole", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class WorkspaceSettings(Base):
    """Per-workspace configuration settings and preferences."""
    __tablename__ = "workspace_settings"
    __table_args__ = (
        Index("ix_workspace_settings_workspace_id", "workspace_id", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Rate limiting per workspace
    rate_limit_requests_per_minute = Column(Integer, default=100, nullable=False)
    rate_limit_tasks_per_day = Column(Integer, default=1000, nullable=False)
    rate_limit_conversations_per_day = Column(Integer, default=500, nullable=False)

    # API key management
    api_keys_enabled = Column(Boolean, default=True, nullable=False)

    # Feature toggles per workspace
    features_enabled = Column(JSON, default=dict, nullable=False)  # {feature_name: enabled}

    # Custom metadata
    metadata = Column(JSON, default=dict, nullable=False)  # {key: value} for custom settings

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="settings")


class WorkspaceAuditLog(Base):
    """Workspace-scoped audit trail - immutable record of all actions in a workspace."""
    __tablename__ = "workspace_audit_logs"
    __table_args__ = (
        Index("ix_workspace_audit_logs_workspace_id_created_at", "workspace_id", "created_at"),
        Index("ix_workspace_audit_logs_user_id_created_at", "user_id", "created_at"),
        Index("ix_workspace_audit_logs_action_created_at", "action", "created_at"),
        Index("ix_workspace_audit_logs_entity_type_entity_id", "entity_type", "entity_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Action details
    action = Column(String(50), nullable=False)  # 'create', 'update', 'delete', 'invite', 'permission_change'
    entity_type = Column(String(50), nullable=False)  # 'workspace', 'member', 'conversation', 'task'
    entity_id = Column(String(255), nullable=False)  # UUID as string for flexibility

    # Change details
    changes = Column(JSON, nullable=True)  # {old_value, new_value} pairs
    reason = Column(String(500), nullable=True)  # Why the change was made

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    # Immutable - no updated_at

    # Relationships
    workspace = relationship("Workspace", back_populates="audit_logs")
    user = relationship("User", backref="workspace_audit_logs")


class WorkspaceInvitation(Base):
    """Email-based invitation to join a workspace."""
    __tablename__ = "workspace_invitations"
    __table_args__ = (
        Index("ix_workspace_invitations_workspace_id_email_status", "workspace_id", "email", "status"),
        Index("ix_workspace_invitations_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("workspace_roles.id", ondelete="RESTRICT"), nullable=False)

    # Invitation token for accepting without logging in
    invitation_token = Column(String(255), unique=True, nullable=False, index=True)

    status = Column(Enum(InvitationStatusEnum), default=InvitationStatusEnum.PENDING, nullable=False)
    accepted_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)  # Invitations expire after 30 days

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])
    role = relationship("WorkspaceRole")
    accepted_by = relationship("User", foreign_keys=[accepted_by_id])
