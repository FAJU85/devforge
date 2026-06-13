'use client';

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import WebSocketService, { TaskStatusMessage } from '../../services/websocketService';

interface TaskProgressMonitorProps {
  taskId: string;
  userId: string;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export default function TaskProgressMonitor({
  taskId,
  userId,
  onComplete,
  onError,
}: TaskProgressMonitorProps) {
  const [status, setStatus] = useState<'pending' | 'running' | 'completed' | 'failed'>('pending');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Initialize WebSocket
  const wsUrl = typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${userId}`
    : 'ws://localhost:3000/ws/default';

  const { isConnected, on } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
  });

  // Setup task progress listener
  useEffect(() => {
    const unsubscribe = on('task_progress', (message) => {
      const data = message.data as any;

      if (data.task_id === taskId) {
        setStatus(data.status);
        setProgress(data.progress);
        setMessage(data.message);

        if (data.status === 'running' && !startTime) {
          setStartTime(new Date());
        }

        if (data.status === 'completed') {
          onComplete?.(data);
        } else if (data.status === 'failed') {
          const errorMessage = data.error || 'Task failed';
          setError(errorMessage);
          onError?.(errorMessage);
        }
      }
    });

    return () => {
      unsubscribe?.();
    };
  }, [taskId, on, startTime, onComplete, onError]);

  // Track elapsed time
  useEffect(() => {
    if (status === 'running' && startTime) {
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime.getTime()) / 1000));
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [status, startTime]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getStatusColor = (): string => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-900';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900';
      case 'running':
        return 'bg-blue-100 dark:bg-blue-900';
      default:
        return 'bg-gray-100 dark:bg-gray-800';
    }
  };

  const getStatusIcon = (): string => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'failed':
        return '✗';
      case 'running':
        return '⏳';
      default:
        return '○';
    }
  };

  return (
    <div className={`rounded-lg p-6 ${getStatusColor()}`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{getStatusIcon()}</span>
            <div>
              <h3 className="text-lg font-semibold capitalize">{status}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Task ID: {taskId.slice(0, 8)}...
              </p>
            </div>
          </div>
          {isConnected && (
            <div className="flex items-center gap-2 text-xs font-medium">
              <div className="h-2 w-2 rounded-full bg-green-600 animate-pulse" />
              Live
            </div>
          )}
        </div>

        {/* Message */}
        {message && (
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{message}</p>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-100 p-3 text-red-800 dark:bg-red-900 dark:text-red-200">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Progress Bar */}
        {status !== 'pending' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">Progress</span>
              <span className="text-xs font-medium">{progress}%</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-gray-300 dark:bg-gray-600">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
          {startTime && (
            <span>Elapsed: {formatTime(elapsedTime)}</span>
          )}
          {status === 'completed' && (
            <span className="text-green-600 dark:text-green-400">Completed successfully</span>
          )}
          {status === 'failed' && (
            <span className="text-red-600 dark:text-red-400">Failed with error</span>
          )}
        </div>
      </div>
    </div>
  );
}
