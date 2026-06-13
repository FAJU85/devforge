/**
 * Phase 8.6: Agent Orchestration Store
 * Manages agent workflow state in the frontend
 */

import { create } from 'zustand';

export interface AgentMessage {
  agent_id: string;
  agent_name: string;
  message_type: 'query' | 'response' | 'analysis' | 'recommendation' | 'decision' | 'error';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface AgentState {
  agent_id: string;
  agent_name: string;
  role: string;
  status: 'idle' | 'thinking' | 'acting' | 'waiting' | 'complete' | 'error';
  current_task?: string;
  task_progress: number;
  last_action?: string;
  message_count: number;
}

export interface Workflow {
  workflow_id: string;
  workflow_type: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  messages: AgentMessage[];
  agent_states: Record<string, AgentState>;
  initial_request?: Record<string, unknown>;
  final_result?: Record<string, unknown>;
}

export interface WorkflowResults {
  workflow_id: string;
  workflow_type: string;
  initial_request: Record<string, unknown>;
  final_result?: Record<string, unknown>;
  agent_states: Record<string, AgentState>;
  conversation_history: AgentMessage[];
  created_at: string;
  completed_at?: string;
}

interface AgentStoreState {
  // Workflows
  workflows: Map<string, Workflow>;
  activeWorkflowId: string | null;

  // UI State
  isLoading: boolean;
  error: string | null;

  // Actions
  createWorkflow: (workflow_id: string, workflow_type: string) => void;
  updateWorkflow: (workflow_id: string, updates: Partial<Workflow>) => void;
  addMessage: (workflow_id: string, message: AgentMessage) => void;
  updateAgentState: (workflow_id: string, agent_id: string, state: AgentState) => void;
  setActiveWorkflow: (workflow_id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  getWorkflow: (workflow_id: string) => Workflow | undefined;
  getActiveWorkflow: () => Workflow | undefined;
  getAllWorkflows: () => Workflow[];
  clearWorkflows: () => void;

  // Poll for updates
  pollWorkflow: (workflow_id: string) => Promise<void>;
}

export const useAgentStore = create<AgentStoreState>((set, get) => ({
  workflows: new Map(),
  activeWorkflowId: null,
  isLoading: false,
  error: null,

  createWorkflow: (workflow_id: string, workflow_type: string) => {
    const workflow: Workflow = {
      workflow_id,
      workflow_type,
      status: 'queued',
      created_at: new Date().toISOString(),
      messages: [],
      agent_states: {},
    };

    set((state) => {
      const newWorkflows = new Map(state.workflows);
      newWorkflows.set(workflow_id, workflow);
      return { workflows: newWorkflows, activeWorkflowId: workflow_id };
    });
  },

  updateWorkflow: (workflow_id: string, updates: Partial<Workflow>) => {
    set((state) => {
      const newWorkflows = new Map(state.workflows);
      const workflow = newWorkflows.get(workflow_id);
      if (workflow) {
        newWorkflows.set(workflow_id, { ...workflow, ...updates });
      }
      return { workflows: newWorkflows };
    });
  },

  addMessage: (workflow_id: string, message: AgentMessage) => {
    set((state) => {
      const newWorkflows = new Map(state.workflows);
      const workflow = newWorkflows.get(workflow_id);
      if (workflow) {
        newWorkflows.set(workflow_id, {
          ...workflow,
          messages: [...workflow.messages, message],
        });
      }
      return { workflows: newWorkflows };
    });
  },

  updateAgentState: (workflow_id: string, agent_id: string, state: AgentState) => {
    set((state) => {
      const newWorkflows = new Map(state.workflows);
      const workflow = newWorkflows.get(workflow_id);
      if (workflow) {
        newWorkflows.set(workflow_id, {
          ...workflow,
          agent_states: {
            ...workflow.agent_states,
            [agent_id]: state,
          },
        });
      }
      return { workflows: newWorkflows };
    });
  },

  setActiveWorkflow: (workflow_id: string | null) => {
    set({ activeWorkflowId: workflow_id });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  getWorkflow: (workflow_id: string) => {
    return get().workflows.get(workflow_id);
  },

  getActiveWorkflow: () => {
    const { activeWorkflowId, workflows } = get();
    return activeWorkflowId ? workflows.get(activeWorkflowId) : undefined;
  },

  getAllWorkflows: () => {
    return Array.from(get().workflows.values());
  },

  clearWorkflows: () => {
    set({ workflows: new Map(), activeWorkflowId: null });
  },

  pollWorkflow: async (workflow_id: string) => {
    try {
      const response = await fetch(`/api/agents/orchestrate/${workflow_id}`);
      if (response.ok) {
        const status = await response.json();
        get().updateWorkflow(workflow_id, {
          status: status.status,
          completed_at: status.completed_at,
          duration_seconds: status.duration_seconds,
          error_message: status.error_message,
        });

        // Fetch full results if completed
        if (status.status === 'completed') {
          const resultsResponse = await fetch(
            `/api/agents/orchestrate/${workflow_id}/results`
          );
          if (resultsResponse.ok) {
            const results: WorkflowResults = await resultsResponse.json();
            get().updateWorkflow(workflow_id, {
              messages: results.conversation_history,
              agent_states: results.agent_states,
              final_result: results.final_result,
            });
          }
        }
      }
    } catch (error) {
      console.error(`Error polling workflow ${workflow_id}:`, error);
      get().setError(String(error));
    }
  },
}));
