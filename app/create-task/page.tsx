import React from 'react';
import { ArrowLeft } from 'lucide-react';

export default function CreateTaskPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition">
          <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
            Create New Task
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">
            Choose an agent and configure your task
          </p>
        </div>
      </div>

      {/* Agent Selection */}
      <div className="dev-card">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Select Agent
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AgentOption
            title="Browser Agent"
            description="Navigate websites and interact with elements"
            icon="🌐"
            selected={true}
          />
          <AgentOption
            title="Test Generator"
            description="Generate tests from natural language"
            icon="✓"
          />
          <AgentOption
            title="Bug Detector"
            description="Scan for bugs and issues"
            icon="🐛"
          />
          <AgentOption
            title="Web Task Agent"
            description="Execute general web automation tasks"
            icon="⚙️"
          />
        </div>
      </div>

      {/* Configuration */}
      <div className="dev-card">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">
          Task Configuration
        </h2>
        <div className="space-y-5">
          {/* Task Description */}
          <div>
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Task Description *
            </label>
            <textarea
              placeholder="Describe what you want the agent to do..."
              className="w-full p-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:border-[#76cd1d]"
              rows={4}
            />
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Be specific about what you want to achieve
            </p>
          </div>

          {/* URL */}
          <div>
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Target URL
            </label>
            <input
              type="url"
              placeholder="https://example.com"
              className="w-full p-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-500 focus:outline-none focus:border-[#76cd1d]"
            />
          </div>

          {/* Framework Selection (for Test Generator) */}
          <div>
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Test Framework
            </label>
            <select className="w-full p-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:border-[#76cd1d]">
              <option>pytest</option>
              <option>unittest</option>
              <option>playwright</option>
              <option>selenium</option>
            </select>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
              Priority
            </label>
            <div className="flex gap-3">
              {['Low', 'Medium', 'High', 'Critical'].map((priority) => (
                <label key={priority} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="priority"
                    value={priority}
                    defaultChecked={priority === 'Medium'}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {priority}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Advanced Options */}
          <details className="cursor-pointer">
            <summary className="text-sm font-medium text-slate-900 dark:text-white py-2 hover:text-[#76cd1d] transition">
              Advanced Options
            </summary>
            <div className="space-y-4 mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
              <div>
                <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
                  Max Steps
                </label>
                <input
                  type="number"
                  defaultValue="50"
                  className="w-full p-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-900 dark:text-white mb-2">
                  Timeout (seconds)
                </label>
                <input
                  type="number"
                  defaultValue="300"
                  className="w-full p-3 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>
            </div>
          </details>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button className="px-6 py-2 rounded-lg font-semibold text-slate-900 dark:text-white bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 transition">
          Cancel
        </button>
        <button className="px-6 py-2 rounded-lg font-semibold bg-[#76cd1d] text-black hover:bg-[#63b50f] transition flex items-center gap-2">
          <span>Create Task</span>
          <span className="text-lg">→</span>
        </button>
      </div>
    </div>
  );
}

function AgentOption({ title, description, icon, selected = false }) {
  return (
    <button
      className={`p-4 rounded-lg border-2 text-left transition ${
        selected
          ? 'border-[#76cd1d] bg-[#76cd1d]/10 dark:bg-[#76cd1d]/20'
          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        {selected && (
          <div className="w-5 h-5 rounded-full bg-[#76cd1d] flex items-center justify-center">
            <span className="text-white text-xs font-bold">✓</span>
          </div>
        )}
      </div>
      <h3 className="font-semibold text-slate-900 dark:text-white mb-1">
        {title}
      </h3>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        {description}
      </p>
    </button>
  );
}
