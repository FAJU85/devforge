'use client';

import { useState, useEffect, useCallback } from 'react';
import RepositoryList from './RepositoryList';
import FileBrowser from './FileBrowser';
import { useWebSocket } from '../../hooks/useWebSocket';

interface Repository {
  id: number;
  name: string;
  full_name: string;
  description: string;
  url: string;
  private: boolean;
  language: string;
  stars: number;
  forks: number;
  updated_at: string;
  default_branch: string;
}

interface RepositoryBrowserProps {
  githubToken: string;
  userId: string;
}

export default function RepositoryBrowser({ githubToken, userId }: RepositoryBrowserProps) {
  const [selectedRepository, setSelectedRepository] = useState<Repository | null>(null);
  const [view, setView] = useState<'list' | 'browser'>('list');
  const [taskStatus, setTaskStatus] = useState<Record<string, any>>({});
  const [wsConnected, setWsConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);

  // Initialize WebSocket connection
  const wsUrl = typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${userId}`
    : 'ws://localhost:3000/ws/default';

  const { isConnected, send, on, off } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
  });

  useEffect(() => {
    setWsConnected(isConnected);
  }, [isConnected]);

  // Setup WebSocket listeners for task status updates
  useEffect(() => {
    const unsubscribe = on('task_progress', (message) => {
      const taskData = message.data as any;
      setTaskStatus((prev) => ({
        ...prev,
        [taskData.task_id]: taskData,
      }));
    });

    return () => {
      unsubscribe?.();
    };
  }, [on]);

  const handleSelectRepository = useCallback((repo: Repository) => {
    setSelectedRepository(repo);
    setView('browser');
  }, []);

  const handleBack = useCallback(() => {
    setView('list');
    setSelectedRepository(null);
  }, []);

  const getOwnerAndRepo = (fullName: string): [string, string] => {
    const [owner, repo] = fullName.split('/');
    return [owner, repo];
  };

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden">
      {/* Status Bar */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Repository Browser</h2>
          <div className="flex items-center gap-4">
            {wsConnected && (
              <div className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400">
                <div className="h-2 w-2 rounded-full bg-green-600 dark:bg-green-400" />
                Connected
              </div>
            )}
            {wsError && (
              <div className="flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
                <div className="h-2 w-2 rounded-full bg-red-600 dark:bg-red-400" />
                {wsError}
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        {view === 'browser' && selectedRepository && (
          <div className="mt-2 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <button
              onClick={handleBack}
              className="text-blue-600 hover:underline dark:text-blue-400"
            >
              Back to Repositories
            </button>
            <span>/</span>
            <span className="font-semibold text-gray-900 dark:text-gray-100">
              {selectedRepository.full_name}
            </span>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {view === 'list' ? (
          <RepositoryList
            token={githubToken}
            onSelectRepository={handleSelectRepository}
          />
        ) : selectedRepository ? (
          <>
            {(() => {
              const [owner, repo] = getOwnerAndRepo(selectedRepository.full_name);
              return (
                <FileBrowser
                  token={githubToken}
                  owner={owner}
                  repo={repo}
                  branch={selectedRepository.default_branch}
                  initialPath=""
                />
              );
            })()}
          </>
        ) : null}
      </div>

      {/* Task Status Indicator */}
      {Object.values(taskStatus).length > 0 && (
        <div className="flex-shrink-0 border-t border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
          <div className="space-y-2">
            {Object.values(taskStatus).map((task: any) => (
              <div
                key={task.task_id}
                className="flex items-center justify-between rounded-lg bg-white p-3 dark:bg-gray-700"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {task.message}
                  </p>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-600">
                    <div
                      className="h-full bg-blue-600 transition-all duration-300"
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </div>
                <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                  {task.progress}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
