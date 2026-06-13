/**
 * Phase 8.6: Agent Orchestrator Component
 * Main control panel for triggering agent workflows
 */

import React, { useState } from 'react';
import { useAgentWorkflow } from '@/hooks/useAgentWorkflow';

interface Props {
  onWorkflowCreated?: (workflowId: string, type: string) => void;
}

export const AgentOrchestrator: React.FC<Props> = ({ onWorkflowCreated }) => {
  const { startFineTuning, startOptimization, isLoading, error } = useAgentWorkflow();

  // Fine-tuning form
  const [fineTuningForm, setFineTuningForm] = useState({
    task_type: 'bug_detection',
    model: 'gpt-3.5-turbo',
    learning_rate: 2e-5,
    batch_size: 32,
    num_epochs: 3,
  });

  // Optimization form
  const [optimizationForm, setOptimizationForm] = useState({
    load_test_id: 'lt_latest',
  });

  const handleFineTuning = async () => {
    try {
      const workflowId = await startFineTuning({
        task_type: fineTuningForm.task_type,
        model: fineTuningForm.model,
        parameters: {
          learning_rate: fineTuningForm.learning_rate,
          batch_size: fineTuningForm.batch_size,
          num_epochs: fineTuningForm.num_epochs,
        },
      });
      onWorkflowCreated?.(workflowId, 'fine_tuning');
    } catch (err) {
      console.error('Failed to start fine-tuning:', err);
    }
  };

  const handleOptimization = async () => {
    try {
      const workflowId = await startOptimization({
        load_test_id: optimizationForm.load_test_id,
      });
      onWorkflowCreated?.(workflowId, 'optimization');
    } catch (err) {
      console.error('Failed to start optimization:', err);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">
            Agent Orchestrator
          </h2>
          <p className="text-gray-600 mt-2">
            Trigger multi-agent workflows for fine-tuning and optimization
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 m-6 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-6 p-6">
          {/* Fine-Tuning Workflow */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Fine-Tuning Workflow
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Task Type
              </label>
              <select
                value={fineTuningForm.task_type}
                onChange={(e) =>
                  setFineTuningForm({
                    ...fineTuningForm,
                    task_type: e.target.value,
                  })
                }
                className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="bug_detection">Bug Detection</option>
                <option value="code_optimization">Code Optimization</option>
                <option value="performance_prediction">Performance Prediction</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Model
              </label>
              <select
                value={fineTuningForm.model}
                onChange={(e) =>
                  setFineTuningForm({
                    ...fineTuningForm,
                    model: e.target.value,
                  })
                }
                className="mt-1 block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="gpt-4">GPT-4</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                <option value="llama-2-70b">Llama 2 70B</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Learning Rate
              </label>
              <input
                type="number"
                value={fineTuningForm.learning_rate}
                onChange={(e) =>
                  setFineTuningForm({
                    ...fineTuningForm,
                    learning_rate: parseFloat(e.target.value),
                  })
                }
                step="0.00001"
                className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Batch Size
              </label>
              <input
                type="number"
                value={fineTuningForm.batch_size}
                onChange={(e) =>
                  setFineTuningForm({
                    ...fineTuningForm,
                    batch_size: parseInt(e.target.value),
                  })
                }
                className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Number of Epochs
              </label>
              <input
                type="number"
                value={fineTuningForm.num_epochs}
                onChange={(e) =>
                  setFineTuningForm({
                    ...fineTuningForm,
                    num_epochs: parseInt(e.target.value),
                  })
                }
                min="1"
                max="10"
                className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              />
            </div>

            <button
              onClick={handleFineTuning}
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Starting...' : 'Start Fine-Tuning'}
            </button>
          </div>

          {/* Optimization Workflow */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Optimization Workflow
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Load Test ID
              </label>
              <input
                type="text"
                value={optimizationForm.load_test_id}
                onChange={(e) =>
                  setOptimizationForm({
                    ...optimizationForm,
                    load_test_id: e.target.value,
                  })
                }
                placeholder="e.g., lt_latest"
                className="mt-1 block w-full rounded border-gray-300 shadow-sm"
              />
            </div>

            <div className="bg-blue-50 p-4 rounded">
              <h4 className="font-semibold text-blue-900 mb-2">
                Workflow Steps
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>1. LoadTestAnalyzer: Analyze test results</li>
                <li>2. Identify bottlenecks and patterns</li>
                <li>3. PerformanceAdvisor: Generate recommendations</li>
                <li>4. CodeReviewerAgent: Review optimization code</li>
                <li>5. Reach consensus on best approach</li>
              </ul>
            </div>

            <button
              onClick={handleOptimization}
              disabled={isLoading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {isLoading ? 'Starting...' : 'Start Optimization'}
            </button>
          </div>
        </div>
      </div>

      {/* Available Models */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Available Models for Fine-Tuning
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <ModelCard
            name="GPT-3.5 Turbo"
            provider="OpenAI"
            cost="$0.0015 per 1K tokens"
            maxTokens={4096}
          />
          <ModelCard
            name="GPT-4"
            provider="OpenAI"
            cost="$0.03 per 1K tokens"
            maxTokens={8192}
          />
          <ModelCard
            name="Claude 3 Sonnet"
            provider="Anthropic"
            cost="$0.003 per 1K tokens"
            maxTokens={200000}
          />
          <ModelCard
            name="Llama 2 70B"
            provider="Meta"
            cost="$0.001 per 1K tokens"
            maxTokens={4096}
          />
        </div>
      </div>
    </div>
  );
};

interface ModelCardProps {
  name: string;
  provider: string;
  cost: string;
  maxTokens: number;
}

const ModelCard: React.FC<ModelCardProps> = ({
  name,
  provider,
  cost,
  maxTokens,
}) => (
  <div className="border rounded-lg p-4">
    <h4 className="font-semibold text-gray-900">{name}</h4>
    <p className="text-sm text-gray-600">{provider}</p>
    <p className="text-sm text-blue-600 mt-2">{cost}</p>
    <p className="text-xs text-gray-500 mt-1">Max tokens: {maxTokens.toLocaleString()}</p>
  </div>
);
