-- Phase 7: Enterprise Features - Workspace Tables Migration
-- This migration adds multi-user workspace support to DevForge

-- 1. Create Workspace table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    avatar_url VARCHAR(1024),
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_archived BOOLEAN DEFAULT FALSE NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL
);

CREATE INDEX ix_workspaces_owner_id_created_at ON workspaces(owner_id, created_at);
CREATE INDEX ix_workspaces_is_deleted_created_at ON workspaces(is_deleted, created_at);

-- 2. Create WorkspaceRole table
CREATE TABLE IF NOT EXISTS workspace_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role_type VARCHAR(50),
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_custom BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX ix_workspace_roles_workspace_id_name ON workspace_roles(workspace_id, name);

-- 3. Create Permission table (global permission catalog)
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX ix_permissions_category_name ON permissions(category, name);

-- 4. Create RolePermission join table
CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES workspace_roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX ix_role_permissions_role_id_permission_id ON role_permissions(role_id, permission_id);

-- 5. Create WorkspaceMember table
CREATE TABLE IF NOT EXISTS workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES workspace_roles(id) ON DELETE RESTRICT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    invited_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE UNIQUE INDEX ix_workspace_members_workspace_id_user_id ON workspace_members(workspace_id, user_id);
CREATE INDEX ix_workspace_members_user_id_created_at ON workspace_members(user_id, joined_at);
CREATE INDEX ix_workspace_members_is_active ON workspace_members(is_active);

-- 6. Create WorkspaceSettings table
CREATE TABLE IF NOT EXISTS workspace_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL UNIQUE REFERENCES workspaces(id) ON DELETE CASCADE,
    rate_limit_requests_per_minute INTEGER DEFAULT 100 NOT NULL,
    rate_limit_tasks_per_day INTEGER DEFAULT 1000 NOT NULL,
    rate_limit_conversations_per_day INTEGER DEFAULT 500 NOT NULL,
    api_keys_enabled BOOLEAN DEFAULT TRUE NOT NULL,
    features_enabled JSONB DEFAULT '{}'::jsonb NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX ix_workspace_settings_workspace_id ON workspace_settings(workspace_id);

-- 7. Create WorkspaceAuditLog table
CREATE TABLE IF NOT EXISTS workspace_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    changes JSONB,
    reason VARCHAR(500),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX ix_workspace_audit_logs_workspace_id_created_at ON workspace_audit_logs(workspace_id, created_at);
CREATE INDEX ix_workspace_audit_logs_user_id_created_at ON workspace_audit_logs(user_id, created_at);
CREATE INDEX ix_workspace_audit_logs_action_created_at ON workspace_audit_logs(action, created_at);
CREATE INDEX ix_workspace_audit_logs_entity_type_entity_id ON workspace_audit_logs(entity_type, entity_id);

-- 8. Create WorkspaceInvitation table
CREATE TABLE IF NOT EXISTS workspace_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    invited_by_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES workspace_roles(id) ON DELETE RESTRICT,
    invitation_token VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    accepted_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    accepted_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX ix_workspace_invitations_workspace_id_email_status ON workspace_invitations(workspace_id, email, status);
CREATE INDEX ix_workspace_invitations_created_at ON workspace_invitations(created_at);
CREATE INDEX ix_workspace_invitations_token ON workspace_invitations(invitation_token);

-- 9. Add workspace_id FK to existing tables (nullable for backward compatibility)
ALTER TABLE users
ADD COLUMN default_workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;

ALTER TABLE conversations
ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;

ALTER TABLE repositories
ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;

ALTER TABLE tasks
ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;

ALTER TABLE audit_logs
ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;

ALTER TABLE configs
ADD COLUMN workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL;

-- 10. Create indexes on new FKs for performance
CREATE INDEX ix_users_default_workspace_id ON users(default_workspace_id);
CREATE INDEX ix_conversations_workspace_id ON conversations(workspace_id);
CREATE INDEX ix_conversations_user_id_workspace_id ON conversations(user_id, workspace_id);
CREATE INDEX ix_repositories_workspace_id ON repositories(workspace_id);
CREATE INDEX ix_tasks_workspace_id ON tasks(workspace_id);
CREATE INDEX ix_tasks_user_id_workspace_id ON tasks(user_id, workspace_id);
CREATE INDEX ix_audit_logs_workspace_id ON audit_logs(workspace_id);
CREATE INDEX ix_configs_workspace_id ON configs(workspace_id);

-- 11. Insert global permission catalog
INSERT INTO permissions (id, name, description, category) VALUES
-- Workspace permissions
('550e8400-e29b-41d4-a716-446655440001', 'workspace.create', 'Create new workspaces', 'workspace'),
('550e8400-e29b-41d4-a716-446655440002', 'workspace.delete', 'Delete workspaces', 'workspace'),
('550e8400-e29b-41d4-a716-446655440003', 'workspace.archive', 'Archive workspaces', 'workspace'),
('550e8400-e29b-41d4-a716-446655440004', 'workspace.edit', 'Edit workspace settings', 'workspace'),

-- Members permissions
('550e8400-e29b-41d4-a716-446655440011', 'members.invite', 'Invite users to workspace', 'members'),
('550e8400-e29b-41d4-a716-446655440012', 'members.remove', 'Remove members from workspace', 'members'),
('550e8400-e29b-41d4-a716-446655440013', 'members.update_role', 'Update member roles', 'members'),
('550e8400-e29b-41d4-a716-446655440014', 'members.view', 'View workspace members', 'members'),

-- Conversations permissions
('550e8400-e29b-41d4-a716-446655440021', 'conversations.create', 'Create conversations', 'conversations'),
('550e8400-e29b-41d4-a716-446655440022', 'conversations.edit', 'Edit conversations', 'conversations'),
('550e8400-e29b-41d4-a716-446655440023', 'conversations.delete', 'Delete conversations', 'conversations'),
('550e8400-e29b-41d4-a716-446655440024', 'conversations.view', 'View conversations', 'conversations'),

-- Tasks permissions
('550e8400-e29b-41d4-a716-446655440031', 'tasks.create', 'Create tasks', 'tasks'),
('550e8400-e29b-41d4-a716-446655440032', 'tasks.edit', 'Edit tasks', 'tasks'),
('550e8400-e29b-41d4-a716-446655440033', 'tasks.execute', 'Execute tasks', 'tasks'),
('550e8400-e29b-41d4-a716-446655440034', 'tasks.delete', 'Delete tasks', 'tasks'),
('550e8400-e29b-41d4-a716-446655440035', 'tasks.view', 'View tasks', 'tasks'),

-- Repositories permissions
('550e8400-e29b-41d4-a716-446655440041', 'repositories.connect', 'Connect repositories', 'repositories'),
('550e8400-e29b-41d4-a716-446655440042', 'repositories.manage', 'Manage repositories', 'repositories'),
('550e8400-e29b-41d4-a716-446655440043', 'repositories.view', 'View repositories', 'repositories'),

-- Audit permissions
('550e8400-e29b-41d4-a716-446655440051', 'audit.view', 'View audit logs', 'audit'),
('550e8400-e29b-41d4-a716-446655440052', 'audit.export', 'Export audit logs', 'audit'),

-- Settings permissions
('550e8400-e29b-41d4-a716-446655440061', 'settings.edit', 'Edit workspace settings', 'settings'),
('550e8400-e29b-41d4-a716-446655440062', 'settings.manage', 'Manage workspace configuration', 'settings');
