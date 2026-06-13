/**
 * WebSocket Service
 * High-level service for managing WebSocket connections and subscriptions
 */

import { WebSocketClient, WebSocketConfig } from '../api/websocketClient';

export type TaskEventType =
  | 'task_created'
  | 'task_started'
  | 'task_progress'
  | 'task_completed'
  | 'task_failed';

export interface TaskStatusMessage {
  event: TaskEventType;
  task_id: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface RepositoryUpdateMessage {
  event: 'repo_scan_progress' | 'repo_scan_complete' | 'file_loaded';
  repo_id: string;
  data: Record<string, any>;
  timestamp: string;
}

export class WebSocketService {
  private client: WebSocketClient | null = null;
  private config: WebSocketConfig;
  private taskListeners = new Map<string, Set<(msg: TaskStatusMessage) => void>>();
  private repoListeners = new Map<string, Set<(msg: RepositoryUpdateMessage) => void>>();
  private isInitialized = false;

  constructor(config: WebSocketConfig) {
    this.config = config;
  }

  /**
   * Initialize WebSocket connection
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    this.client = new WebSocketClient(this.config);
    await this.client.connect();

    // Setup message handlers
    this.client.on('message', (message) => {
      this.handleMessage(message.data);
    });

    this.isInitialized = true;
  }

  /**
   * Close WebSocket connection
   */
  disconnect(): void {
    if (this.client) {
      this.client.disconnect();
      this.isInitialized = false;
    }
  }

  /**
   * Subscribe to task updates
   */
  subscribeToTask(
    taskId: string,
    callback: (message: TaskStatusMessage) => void
  ): () => void {
    if (!this.taskListeners.has(taskId)) {
      this.taskListeners.set(taskId, new Set());
    }

    this.taskListeners.get(taskId)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.taskListeners.get(taskId)?.delete(callback);
    };
  }

  /**
   * Subscribe to repository updates
   */
  subscribeToRepository(
    repoId: string,
    callback: (message: RepositoryUpdateMessage) => void
  ): () => void {
    if (!this.repoListeners.has(repoId)) {
      this.repoListeners.set(repoId, new Set());
    }

    this.repoListeners.get(repoId)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.repoListeners.get(repoId)?.delete(callback);
    };
  }

  /**
   * Send subscription request for task
   */
  async subscribeTask(taskId: string): Promise<void> {
    if (!this.client || !this.client.isConnected()) {
      throw new Error('WebSocket not connected');
    }

    this.client.send('message', {
      type: 'subscribe_task',
      task_id: taskId,
    });
  }

  /**
   * Send subscription request for repository
   */
  async subscribeRepository(repoId: string): Promise<void> {
    if (!this.client || !this.client.isConnected()) {
      throw new Error('WebSocket not connected');
    }

    this.client.send('message', {
      type: 'subscribe_repo',
      repo_id: repoId,
    });
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: any): void {
    // Handle task progress messages
    if (data.type === 'task_progress' || data.event?.startsWith('task_')) {
      const taskId = data.task_id;
      if (taskId && this.taskListeners.has(taskId)) {
        const message: TaskStatusMessage = {
          event: data.event || 'task_progress',
          task_id: taskId,
          status: data.status,
          progress: data.progress,
          message: data.message,
          timestamp: data.timestamp || new Date().toISOString(),
          metadata: data.metadata,
        };

        this.taskListeners.get(taskId)!.forEach((callback) => {
          try {
            callback(message);
          } catch (error) {
            console.error('Error in task listener:', error);
          }
        });
      }
    }

    // Handle repository messages
    if (data.event?.startsWith('repo_') || data.event === 'file_loaded') {
      const repoId = data.repo_id;
      if (repoId && this.repoListeners.has(repoId)) {
        const message: RepositoryUpdateMessage = {
          event: data.event,
          repo_id: repoId,
          data: data.data || data,
          timestamp: data.timestamp || new Date().toISOString(),
        };

        this.repoListeners.get(repoId)!.forEach((callback) => {
          try {
            callback(message);
          } catch (error) {
            console.error('Error in repository listener:', error);
          }
        });
      }
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.client?.isConnected() ?? false;
  }

  /**
   * Get connection stats
   */
  getStats() {
    return this.client?.getStats();
  }

  /**
   * Clear all listeners
   */
  clearListeners(): void {
    this.taskListeners.clear();
    this.repoListeners.clear();
  }
}

// Global service instance
let globalService: WebSocketService | null = null;

/**
 * Get or create global WebSocket service
 */
export function getWebSocketService(config?: WebSocketConfig): WebSocketService {
  if (!globalService && config) {
    globalService = new WebSocketService(config);
  }

  if (!globalService) {
    throw new Error('WebSocket service not initialized. Provide config.');
  }

  return globalService;
}

export default WebSocketService;
