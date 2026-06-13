/**
 * Phase 8.6: Agent Workflow Visualization Component
 * Displays workflow progress and agent interaction
 */

import React, { useEffect } from 'react';
import { useAgentWorkflow } from '@/hooks/useAgentWorkflow';
import { Workflow, AgentState } from '@/stores/agentStore';

interface Props {
  workflowId?: string;
}

export const AgentWorkflow: React.FC<Props> = ({ workflowId }) => {
  const { activeWorkflow, setActiveWorkflow, workflows } = useAgentWorkflow();

  const workflow = workflowId
    ? workflows.find((w) => w.workflow_id === workflowId)
    : activeWorkflow;

  useEffect(() => {
    if (workflowId && !workflow) {
      // Workflow not found, might need to fetch it
      console.warn(`Workflow ${workflowId} not found in store`);
    }
  }, [workflowId, workflow]);

  if (!workflow) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">
          {workflowId ? `Workflow ${workflowId} not found` : 'No workflow selected'}
        </p>
      </div>
    );
  }

  const isRunning = workflow.status === 'running' || workflow.status === 'queued';
  const isCompleted = workflow.status === 'completed';

  return (
    <div className="space-y-6 p-6">
      {/* Workflow Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {workflow.workflow_type === 'fine_tuning'
                ? 'Fine-Tuning Workflow'
                : 'Optimization Workflow'}
            </h2>
            <p className="text-gray-600 mt-1">ID: {workflow.workflow_id}</p>
          </div>
          <StatusBadge status={workflow.status} />
        </div>

        <div className="mt-6 grid grid-cols-4 gap-4">
          <InfoCard label="Status" value={workflow.status} />
          <InfoCard
            label="Duration"
            value={
              workflow.duration_seconds
                ? `${workflow.duration_seconds.toFixed(1)}s`
                : 'In progress...'
            }
          />
          <InfoCard label="Messages" value={workflow.messages.length.toString()} />
          <InfoCard label="Agents" value={Object.keys(workflow.agent_states).length.toString()} />
        </div>
      </div>

      {/* Agent States */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Status</h3>
        <div className="grid grid-cols-2 gap-4">
          {Object.values(workflow.agent_states).map((agent) => (
            <AgentCard key={agent.agent_id} agent={agent} />
          ))}
        </div>
      </div>

      {/* Conversation */}
      <AgentChat messages={workflow.messages} />

      {/* Results */}
      {isCompleted && workflow.final_result && (
        <WorkflowResults results={workflow.final_result} />
      )}

      {/* Error Message */}
      {workflow.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h4 className="text-red-900 font-semibold">Error</h4>
          <p className="text-red-800 mt-2">{workflow.error_message}</p>
        </div>
      )}
    </div>
  );
};

interface StatusBadgeProps {
  status: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const colors: Record<string, string> = {
    queued: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`px-4 py-2 rounded-full font-semibold text-sm ${colors[status] || colors.queued}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

interface InfoCardProps {
  label: string;
  value: string;
}

const InfoCard: React.FC<InfoCardProps> = ({ label, value }) => (
  <div className="bg-gray-50 rounded p-4">
    <p className="text-gray-600 text-sm">{label}</p>
    <p className="text-gray-900 font-semibold text-lg mt-1">{value}</p>
  </div>
);

interface AgentCardProps {
  agent: AgentState;
}

const AgentCard: React.FC<AgentCardProps> = ({ agent }) => (
  <div className="border rounded-lg p-4">
    <div className="flex items-center justify-between mb-3">
      <h4 className="font-semibold text-gray-900">{agent.agent_name}</h4>
      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
        {agent.role}
      </span>
    </div>

    <div className="space-y-2">
      <div>
        <p className="text-xs text-gray-600">Status</p>
        <p className="text-sm font-medium text-gray-900">{agent.status}</p>
      </div>

      {agent.current_task && (
        <div>
          <p className="text-xs text-gray-600">Current Task</p>
          <p className="text-sm font-medium text-gray-900">{agent.current_task}</p>
        </div>
      )}

      {agent.task_progress > 0 && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs text-gray-600">Progress</p>
            <p className="text-xs font-medium text-gray-600">{Math.round(agent.task_progress * 100)}%</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${agent.task_progress * 100}%` }}
            />
          </div>
        </div>
      )}

      <p className="text-xs text-gray-600 mt-2">
        Messages: {agent.message_count}
      </p>
    </div>
  </div>
);

interface ChatProps {
  messages: Array<{
    agent_id: string;
    agent_name: string;
    message_type: string;
    content: string;
    timestamp: string;
  }>;
}

const AgentChat: React.FC<ChatProps> = ({ messages }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Conversation</h3>

    <div className="space-y-4 max-h-96 overflow-y-auto">
      {messages.length === 0 ? (
        <p className="text-gray-600 text-center py-8">No messages yet</p>
      ) : (
        messages.map((msg, idx) => (
          <ChatMessage key={idx} message={msg} />
        ))
      )}
    </div>
  </div>
);

const ChatMessage: React.FC<{ message: any }> = ({ message }) => (
  <div className="border-l-4 border-blue-500 pl-4 py-2">
    <div className="flex items-center justify-between mb-1">
      <span className="font-semibold text-gray-900">{message.agent_name}</span>
      <span className="text-xs text-gray-500">
        {new Date(message.timestamp).toLocaleTimeString()}
      </span>
    </div>
    <div className="flex items-center gap-2 mb-2">
      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
        {message.message_type}
      </span>
    </div>
    <p className="text-gray-800">{message.content}</p>
  </div>
);

interface ResultsProps {
  results: Record<string, any>;
}

const WorkflowResults: React.FC<ResultsProps> = ({ results }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Results</h3>

    {results.recommendations && (
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-3">Recommendations</h4>
        <ul className="space-y-2">
          {Array.isArray(results.recommendations) &&
            results.recommendations.map((rec: any, idx: number) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="text-green-600 font-bold">✓</span>
                <span className="text-gray-700">
                  {typeof rec === 'string' ? rec : rec.recommendation || JSON.stringify(rec)}
                </span>
              </li>
            ))}
        </ul>
      </div>
    )}

    {results.priority_actions && (
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 mb-3">Priority Actions</h4>
        <ol className="space-y-2">
          {results.priority_actions.map((action: string, idx: number) => (
            <li key={idx} className="flex items-start gap-3">
              <span className="font-bold text-blue-600">{idx + 1}.</span>
              <span className="text-gray-700">{action}</span>
            </li>
          ))}
        </ol>
      </div>
    )}

    <details className="border-t pt-4">
      <summary className="cursor-pointer font-semibold text-gray-900">
        View Full Results
      </summary>
      <pre className="bg-gray-50 p-4 rounded mt-4 overflow-auto text-xs">
        {JSON.stringify(results, null, 2)}
      </pre>
    </details>
  </div>
);
