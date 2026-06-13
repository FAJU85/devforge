/**
 * Phase 8.6: Agent Workflow Hook
 * Hook for managing agent orchestration workflows
 */

import { useEffect, useCallback, useRef } from 'react';
import { useAgentStore, Workflow } from '@/stores/agentStore';

export interface UseAgentWorkflowOptions {
  autoPolling?: boolean;
  pollingInterval?: number;
}

export const useAgentWorkflow = (options: UseAgentWorkflowOptions = {}) => {
  const {
    autoPolling = true,
    pollingInterval = 2000,
  } = options;

  const {
    workflows,
    activeWorkflowId,
    isLoading,
    error,
    createWorkflow,
    updateWorkflow,
    setActiveWorkflow,
    setLoading,
    setError,
    getActiveWorkflow,
    getAllWorkflows,
    pollWorkflow,
    clearWorkflows,
  } = useAgentStore();

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Start fine-tuning workflow
  const startFineTuning = useCallback(async (params: {
    task_type: string;
    model?: string;
    parameters?: Record<string, unknown>;
    target_metric?: string;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/agents/orchestrate/fine-tune', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error(`Failed to start fine-tuning: ${response.statusText}`);
      }

      const data = await response.json();
      createWorkflow(data.workflow_id, 'fine_tuning');
      setActiveWorkflow(data.workflow_id);

      return data.workflow_id;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [createWorkflow, setActiveWorkflow, setLoading, setError]);

  // Start optimization workflow
  const startOptimization = useCallback(async (params: {
    load_test_id: string;
    metrics_target?: Record<string, number>;
    constraints?: Record<string, unknown>;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/agents/orchestrate/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error(`Failed to start optimization: ${response.statusText}`);
      }

      const data = await response.json();
      createWorkflow(data.workflow_id, 'optimization');
      setActiveWorkflow(data.workflow_id);

      return data.workflow_id;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [createWorkflow, setActiveWorkflow, setLoading, setError]);

  // Get workflow status
  const getWorkflowStatus = useCallback(async (workflow_id: string) => {
    try {
      const response = await fetch(`/api/agents/orchestrate/${workflow_id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch workflow status');
      }
      return await response.json();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    }
  }, [setError]);

  // Get workflow results
  const getWorkflowResults = useCallback(async (workflow_id: string) => {
    try {
      const response = await fetch(`/api/agents/orchestrate/${workflow_id}/results`);
      if (!response.ok) {
        throw new Error('Failed to fetch workflow results');
      }
      return await response.json();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    }
  }, [setError]);

  // Poll active workflow
  useEffect(() => {
    if (!autoPolling || !activeWorkflowId) {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      return;
    }

    const poll = async () => {
      const workflow = getActiveWorkflow();
      if (workflow && (workflow.status === 'running' || workflow.status === 'queued')) {
        await pollWorkflow(activeWorkflowId);
      } else if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };

    // Initial poll
    poll();

    // Set up polling interval
    pollingIntervalRef.current = setInterval(poll, pollingInterval);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [activeWorkflowId, autoPolling, pollingInterval, getActiveWorkflow, pollWorkflow]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  return {
    // State
    workflows: Array.from(workflows.values()),
    activeWorkflow: getActiveWorkflow(),
    isLoading,
    error,

    // Actions
    startFineTuning,
    startOptimization,
    getWorkflowStatus,
    getWorkflowResults,
    setActiveWorkflow,
    clearWorkflows,
    getAllWorkflows,
  };
};
