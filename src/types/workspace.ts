/**
 * Workspace Domain Types - Phase 7.1 Multi-User Workspaces
 *
 * TypeScript types and interfaces for workspace management.
 */

export interface Workspace {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  avatar_url?: string;
  is_default: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceListResponse {
  workspaces: Workspace[];
  count: number;
}

export interface WorkspaceRole {
  id: string;
  name: string;
  description?: string;
  role_type?: 'owner' | 'admin' | 'developer' | 'viewer';
  is_custom: boolean;
}

export interface WorkspaceMember {
  id: string;
  user_id: string;
  role: WorkspaceRole;
  joined_at: string;
  is_active: boolean;
}

export interface MembersListResponse {
  members: WorkspaceMember[];
  count: number;
}

export interface WorkspaceInvitation {
  id: string;
  workspace_id: string;
  email: string;
  status: 'pending' | 'accepted' | 'rejected' | 'expired';
  created_at: string;
  expires_at: string;
}

export interface InvitationsListResponse {
  invitations: WorkspaceInvitation[];
  count: number;
}

export interface WorkspaceSettings {
  id: string;
  workspace_id: string;
  rate_limit_requests_per_minute: number;
  rate_limit_tasks_per_day: number;
  rate_limit_conversations_per_day: number;
  api_keys_enabled: boolean;
  features_enabled: Record<string, boolean>;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkspacePayload {
  name: string;
  description?: string;
}

export interface UpdateWorkspacePayload {
  name?: string;
  description?: string;
  avatar_url?: string;
}

export interface AddMemberPayload {
  user_id: string;
  role_id: string;
}

export interface UpdateMemberRolePayload {
  role_id: string;
}

export interface InviteUserPayload {
  email: string;
  role_id: string;
}

export interface AcceptInvitationPayload {
  invitation_token: string;
}

export interface WorkspaceContextState {
  activeWorkspace: Workspace | null;
  workspaces: Workspace[];
  members: WorkspaceMember[];
  currentMemberRole: WorkspaceRole | null;
  invitations: WorkspaceInvitation[];
  settings: WorkspaceSettings | null;
  loading: boolean;
  error: string | null;
}

export interface WorkspacePermissionState {
  userPermissions: Set<string>;
  userRole: WorkspaceRole | null;
  isOwner: boolean;
  isAdmin: boolean;
  isDeveloper: boolean;
  isViewer: boolean;
  loading: boolean;
}
