/**
 * Workspace Store - Phase 7.1 Multi-User Workspaces
 *
 * Zustand store for managing workspace state and switching.
 */

import { create } from 'zustand';
import {
  Workspace,
  WorkspaceMember,
  WorkspaceRole,
  WorkspaceContextState,
  CreateWorkspacePayload,
  UpdateWorkspacePayload,
} from '../types/workspace';

interface WorkspaceStoreActions {
  // Workspace operations
  fetchWorkspaces: () => Promise<void>;
  createWorkspace: (payload: CreateWorkspacePayload) => Promise<Workspace>;
  setActiveWorkspace: (workspace: Workspace) => void;
  switchWorkspace: (workspaceId: string) => Promise<void>;
  updateActiveWorkspace: (payload: UpdateWorkspacePayload) => Promise<void>;
  deleteActiveWorkspace: () => Promise<void>;
  leaveWorkspace: (workspaceId: string) => Promise<void>;

  // Member operations
  fetchMembers: () => Promise<void>;
  addMember: (userId: string, roleId: string) => Promise<WorkspaceMember>;
  removeMember: (userId: string) => Promise<void>;
  updateMemberRole: (userId: string, roleId: string) => Promise<void>;

  // Utilities
  getActiveWorkspaceId: () => string | null;
  isWorkspaceOwner: (userId: string) => boolean;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

type WorkspaceStore = WorkspaceContextState & WorkspaceStoreActions;

const initialState: WorkspaceContextState = {
  activeWorkspace: null,
  workspaces: [],
  members: [],
  currentMemberRole: null,
  invitations: [],
  settings: null,
  loading: false,
  error: null,
};

export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  ...initialState,

  // Workspace operations
  fetchWorkspaces: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch('/api/workspaces');
      if (!response.ok) {
        throw new Error(`Failed to fetch workspaces: ${response.statusText}`);
      }
      const data = await response.json();

      set({
        workspaces: data.workspaces,
        loading: false,
      });

      // Set first workspace as active if none is selected
      const state = get();
      if (!state.activeWorkspace && data.workspaces.length > 0) {
        // Try to find default workspace
        const defaultWorkspace = data.workspaces.find((w: Workspace) => w.is_default);
        set({ activeWorkspace: defaultWorkspace || data.workspaces[0] });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  createWorkspace: async (payload: CreateWorkspacePayload) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch('/api/workspaces', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Failed to create workspace: ${response.statusText}`);
      }

      const workspace = await response.json();

      set((state) => ({
        workspaces: [...state.workspaces, workspace],
        loading: false,
      }));

      return workspace;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  setActiveWorkspace: (workspace: Workspace) => {
    set({ activeWorkspace: workspace });
  },

  switchWorkspace: async (workspaceId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/workspaces/${workspaceId}/switch`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to switch workspace: ${response.statusText}`);
      }

      const workspace = await response.json();
      set({ activeWorkspace: workspace, loading: false });

      // Persist to localStorage
      localStorage.setItem('activeWorkspaceId', workspaceId);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  updateActiveWorkspace: async (payload: UpdateWorkspacePayload) => {
    const state = get();
    if (!state.activeWorkspace) {
      throw new Error('No active workspace');
    }

    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/workspaces/${state.activeWorkspace.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Failed to update workspace: ${response.statusText}`);
      }

      const updated = await response.json();
      set({
        activeWorkspace: updated,
        workspaces: state.workspaces.map((w) => (w.id === updated.id ? updated : w)),
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  deleteActiveWorkspace: async () => {
    const state = get();
    if (!state.activeWorkspace) {
      throw new Error('No active workspace');
    }

    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/workspaces/${state.activeWorkspace.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete workspace: ${response.statusText}`);
      }

      set({
        activeWorkspace: null,
        workspaces: state.workspaces.filter((w) => w.id !== state.activeWorkspace!.id),
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  leaveWorkspace: async (workspaceId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/workspaces/${workspaceId}/leave`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Failed to leave workspace: ${response.statusText}`);
      }

      set((state) => ({
        workspaces: state.workspaces.filter((w) => w.id !== workspaceId),
        activeWorkspace:
          state.activeWorkspace?.id === workspaceId ? null : state.activeWorkspace,
        loading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  // Member operations
  fetchMembers: async () => {
    const state = get();
    if (!state.activeWorkspace) {
      return;
    }

    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/workspaces/${state.activeWorkspace.id}/members`);

      if (!response.ok) {
        throw new Error(`Failed to fetch members: ${response.statusText}`);
      }

      const data = await response.json();
      set({ members: data.members, loading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
    }
  },

  addMember: async (userId: string, roleId: string) => {
    const state = get();
    if (!state.activeWorkspace) {
      throw new Error('No active workspace');
    }

    set({ loading: true, error: null });
    try {
      const response = await fetch(`/api/workspaces/${state.activeWorkspace.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, role_id: roleId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add member: ${response.statusText}`);
      }

      const member = await response.json();
      set((s) => ({
        members: [...s.members, member],
        loading: false,
      }));

      return member;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  removeMember: async (userId: string) => {
    const state = get();
    if (!state.activeWorkspace) {
      throw new Error('No active workspace');
    }

    set({ loading: true, error: null });
    try {
      const response = await fetch(
        `/api/workspaces/${state.activeWorkspace.id}/members/${userId}`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error(`Failed to remove member: ${response.statusText}`);
      }

      set((s) => ({
        members: s.members.filter((m) => m.user_id !== userId),
        loading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  updateMemberRole: async (userId: string, roleId: string) => {
    const state = get();
    if (!state.activeWorkspace) {
      throw new Error('No active workspace');
    }

    set({ loading: true, error: null });
    try {
      const response = await fetch(
        `/api/workspaces/${state.activeWorkspace.id}/members/${userId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role_id: roleId }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to update member role: ${response.statusText}`);
      }

      const updated = await response.json();
      set((s) => ({
        members: s.members.map((m) => (m.user_id === userId ? updated : m)),
        loading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      set({ error: message, loading: false });
      throw error;
    }
  },

  // Utilities
  getActiveWorkspaceId: () => {
    return get().activeWorkspace?.id || null;
  },

  isWorkspaceOwner: (userId: string) => {
    const state = get();
    return state.activeWorkspace?.owner_id === userId;
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ loading });
  },

  reset: () => {
    set(initialState);
  },
}));
