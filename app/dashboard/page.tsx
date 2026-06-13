import React from 'react';
import { LayoutDashboard, Zap, Bug, TestTube2, Globe } from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
            Agent Dashboard
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">
            Manage and monitor AI-powered web automation
          </p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-[#76cd1d] text-black rounded-lg font-semibold hover:bg-[#63b50f] transition">
            New Task
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={<Zap className="w-6 h-6" />}
          label="Active Tasks"
          value="12"
          trend="+3 this hour"
          trendUp={true}
        />
        <StatCard
          icon={<TestTube2 className="w-6 h-6" />}
          label="Tests Generated"
          value="1,247"
          trend="+45 today"
          trendUp={true}
        />
        <StatCard
          icon={<Bug className="w-6 h-6" />}
          label="Bugs Found"
          value="89"
          trend="+12 this week"
          trendUp={false}
        />
        <StatCard
          icon={<Globe className="w-6 h-6" />}
          label="Sites Scanned"
          value="34"
          trend="All healthy"
          trendUp={true}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Tasks */}
        <div className="lg:col-span-2">
          <RecentTasks />
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <QuickActions />
          <SystemStatus />
        </div>
      </div>

      {/* Agent Performance */}
      <AgentPerformance />
    </div>
  );
}

function StatCard({ icon, label, value, trend, trendUp }) {
  return (
    <div className="dev-card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">
            {label}
          </p>
          <p className="text-3xl font-bold text-slate-900 dark:text-white mt-2">
            {value}
          </p>
          <p className={`text-xs mt-2 ${trendUp ? 'text-green-600' : 'text-orange-600'}`}>
            {trend}
          </p>
        </div>
        <div className="text-[#76cd1d] dark:text-[#76cd1d]">
          {icon}
        </div>
      </div>
    </div>
  );
}

function RecentTasks() {
  const tasks = [
    {
      id: 'task-001',
      type: 'Browser Automation',
      description: 'Navigate example.com',
      status: 'completed',
      progress: 100,
      time: '2 min ago'
    },
    {
      id: 'task-002',
      type: 'Test Generation',
      description: 'Generate login tests',
      status: 'running',
      progress: 65,
      time: 'Running'
    },
    {
      id: 'task-003',
      type: 'Bug Detection',
      description: 'Scan for bugs',
      status: 'pending',
      progress: 0,
      time: 'Queued'
    },
    {
      id: 'task-004',
      type: 'Web Task',
      description: 'Search and extract data',
      status: 'completed',
      progress: 100,
      time: '15 min ago'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'failed':
        return 'text-red-600';
      case 'pending':
        return 'text-orange-600';
      default:
        return 'text-slate-600';
    }
  };

  const getStatusBg = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30';
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900/30';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/30';
      case 'pending':
        return 'bg-orange-100 dark:bg-orange-900/30';
      default:
        return 'bg-slate-100 dark:bg-slate-900/30';
    }
  };

  return (
    <div className="dev-card">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
        <LayoutDashboard className="w-5 h-5" />
        Recent Tasks
      </h2>
      <div className="space-y-3">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-[#76cd1d] transition"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="font-medium text-slate-900 dark:text-white">
                  {task.type}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {task.description}
                </p>
              </div>
              <span
                className={`px-2 py-1 rounded text-xs font-semibold ${getStatusColor(
                  task.status
                )} ${getStatusBg(task.status)}`}
              >
                {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-[#76cd1d] h-full transition-all"
                  style={{ width: `${task.progress}%` }}
                />
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                {task.time}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuickActions() {
  const actions = [
    {
      icon: <Zap className="w-5 h-5" />,
      label: 'Browser Task',
      color: 'bg-blue-500'
    },
    {
      icon: <TestTube2 className="w-5 h-5" />,
      label: 'Generate Test',
      color: 'bg-green-500'
    },
    {
      icon: <Bug className="w-5 h-5" />,
      label: 'Scan for Bugs',
      color: 'bg-red-500'
    },
    {
      icon: <Globe className="w-5 h-5" />,
      label: 'Web Task',
      color: 'bg-purple-500'
    }
  ];

  return (
    <div className="dev-card">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        Quick Actions
      </h3>
      <div className="space-y-2">
        {actions.map((action, idx) => (
          <button
            key={idx}
            className="w-full flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition text-slate-900 dark:text-white font-medium"
          >
            <div className={`${action.color} text-white p-2 rounded-lg`}>
              {action.icon}
            </div>
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SystemStatus() {
  return (
    <div className="dev-card">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        System Status
      </h3>
      <div className="space-y-3">
        <StatusItem label="Agent API" status="online" />
        <StatusItem label="Browser API" status="online" />
        <StatusItem label="Task Orchestrator" status="online" />
        <StatusItem label="PostgreSQL" status="online" />
        <StatusItem label="Milvus Vector DB" status="online" />
        <StatusItem label="MinIO Storage" status="online" />
      </div>
    </div>
  );
}

function StatusItem({ label, status }) {
  const isOnline = status === 'online';
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-600 dark:text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}
        />
        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
          {isOnline ? 'Online' : 'Offline'}
        </span>
      </div>
    </div>
  );
}

function AgentPerformance() {
  return (
    <div className="dev-card">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-6">
        Agent Performance
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <PerformanceMetric
          agent="Browser Agent"
          tasksCompleted={247}
          avgTime="12s"
          successRate="98%"
        />
        <PerformanceMetric
          agent="Test Generator"
          tasksCompleted={156}
          avgTime="8.5s"
          successRate="99.5%"
        />
        <PerformanceMetric
          agent="Bug Detector"
          tasksCompleted={89}
          avgTime="45s"
          successRate="95%"
        />
        <PerformanceMetric
          agent="Web Task Agent"
          tasksCompleted="34"
          avgTime="23s"
          successRate="96%"
        />
      </div>
    </div>
  );
}

function PerformanceMetric({ agent, tasksCompleted, avgTime, successRate }) {
  return (
    <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
      <p className="font-semibold text-slate-900 dark:text-white text-sm mb-3">
        {agent}
      </p>
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-slate-600 dark:text-slate-400">Tasks</span>
          <span className="font-semibold text-slate-900 dark:text-white">
            {tasksCompleted}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-600 dark:text-slate-400">Avg Time</span>
          <span className="font-semibold text-slate-900 dark:text-white">
            {avgTime}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-600 dark:text-slate-400">Success</span>
          <span className="font-semibold text-green-600">{successRate}</span>
        </div>
      </div>
    </div>
  );
}
