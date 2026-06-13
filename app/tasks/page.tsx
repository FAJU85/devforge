import React from 'react';
import {
  Clock,
  CheckCircle,
  AlertCircle,
  Filter,
  Download,
  Trash2,
  Eye
} from 'lucide-react';

export default function TasksPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
            Tasks
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            View and manage all agent tasks
          </p>
        </div>
        <button className="px-4 py-2 bg-[#76cd1d] text-black rounded-lg font-semibold hover:bg-[#63b50f] transition">
          + New Task
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <FilterButton label="All Tasks" active={true} />
        <FilterButton label="Running" count={3} />
        <FilterButton label="Completed" count={45} />
        <FilterButton label="Failed" count={2} />
        <FilterButton label="Pending" count={8} />
      </div>

      {/* Tasks Table */}
      <TasksTable />
    </div>
  );
}

function FilterButton({ label, active = false, count = 0 }) {
  return (
    <button
      className={`px-4 py-2 rounded-lg font-medium transition flex items-center gap-2 ${
        active
          ? 'bg-[#76cd1d] text-black'
          : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700'
      }`}
    >
      {label}
      {count > 0 && (
        <span className="bg-slate-300 dark:bg-slate-600 px-2 py-0.5 rounded-full text-xs font-bold">
          {count}
        </span>
      )}
    </button>
  );
}

function TasksTable() {
  const tasks = [
    {
      id: 'TASK-2024-001',
      type: 'Browser Automation',
      description: 'Navigate to example.com and take screenshot',
      status: 'completed',
      created: '2 hours ago',
      duration: '2m 15s',
      agent: 'BrowserAgent',
      result: 'Screenshot captured successfully'
    },
    {
      id: 'TASK-2024-002',
      type: 'Test Generation',
      description: 'Generate login tests for login.example.com',
      status: 'completed',
      created: '1 hour ago',
      duration: '8.5s',
      agent: 'TestGenerationAgent',
      result: '5 tests generated'
    },
    {
      id: 'TASK-2024-003',
      type: 'Bug Detection',
      description: 'Scan example.com for bugs',
      status: 'running',
      created: '15 minutes ago',
      duration: '10m 30s',
      agent: 'BugDetectionAgent',
      result: '3 bugs found so far...'
    },
    {
      id: 'TASK-2024-004',
      type: 'Web Task',
      description: 'Search for AI on Google',
      status: 'completed',
      created: '45 minutes ago',
      duration: '1m 5s',
      agent: 'WebTaskAgent',
      result: 'Found 1.2B results'
    },
    {
      id: 'TASK-2024-005',
      type: 'Test Generation',
      description: 'Generate signup tests',
      status: 'pending',
      created: '30 minutes ago',
      duration: 'Waiting...',
      agent: 'TestGenerationAgent',
      result: 'Queued for execution'
    },
    {
      id: 'TASK-2024-006',
      type: 'Browser Automation',
      description: 'Fill registration form',
      status: 'failed',
      created: '1 hour ago',
      duration: '45s',
      agent: 'BrowserAgent',
      result: 'Timeout: Element not found'
    }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-orange-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusBgColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30';
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900/30';
      case 'pending':
        return 'bg-orange-100 dark:bg-orange-900/30';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30';
    }
  };

  const getStatusTextColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 dark:text-green-400';
      case 'running':
        return 'text-blue-700 dark:text-blue-400';
      case 'pending':
        return 'text-orange-700 dark:text-orange-400';
      case 'failed':
        return 'text-red-700 dark:text-red-400';
    }
  };

  return (
    <div className="dev-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Task ID
              </th>
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Description
              </th>
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Agent
              </th>
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Status
              </th>
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Duration
              </th>
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Result
              </th>
              <th className="text-left px-6 py-3 font-semibold text-slate-900 dark:text-white">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr
                key={task.id}
                className="border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition"
              >
                <td className="px-6 py-4">
                  <code className="text-sm font-mono text-[#76cd1d]">
                    {task.id}
                  </code>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm">
                    <p className="font-medium text-slate-900 dark:text-white">
                      {task.type}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      {task.description}
                    </p>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                  {task.agent}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(task.status)}
                    <span
                      className={`text-xs font-semibold px-2 py-1 rounded ${getStatusBgColor(
                        task.status
                      )} ${getStatusTextColor(task.status)}`}
                    >
                      {task.status.charAt(0).toUpperCase() +
                        task.status.slice(1)}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                  {task.duration}
                </td>
                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400 max-w-xs">
                  {task.result}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition">
                      <Eye className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    </button>
                    <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition">
                      <Download className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    </button>
                    <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition">
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
