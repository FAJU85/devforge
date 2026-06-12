/**
 * WebSocket Client - real-time communication with backend
 */

export type WebSocketEventType =
  | 'message'
  | 'update'
  | 'error'
  | 'notification'
  | 'sync'
  | 'status';

export interface WebSocketMessage<T = any> {
  type: WebSocketEventType;
  data: T;
  timestamp: number;
  id?: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  debug?: boolean;
}

export type EventListener<T = any> = (message: WebSocketMessage<T>) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private config: Required<Omit<WebSocketConfig, 'url'>>;
  private listeners = new Map<WebSocketEventType, Set<EventListener>>();
  private reconnectAttempt = 0;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageId = 0;
  private stats = {
    connected: false,
    messagesReceived: 0,
    messagesSent: 0,
    reconnects: 0,
    errors: 0,
  };

  constructor(config: WebSocketConfig) {
    this.url = config.url;
    this.config = {
      reconnectAttempts: config.reconnectAttempts ?? 5,
      reconnectDelay: config.reconnectDelay ?? 3000,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      debug: config.debug ?? false,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.log('Connected to WebSocket server');
          this.stats.connected = true;
          this.reconnectAttempt = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          this.log('WebSocket error:', error);
          this.stats.errors++;
          reject(error);
        };

        this.ws.onclose = () => {
          this.log('Disconnected from WebSocket server');
          this.stats.connected = false;
          this.stopHeartbeat();
          this.attemptReconnect();
        };
      } catch (error) {
        this.log('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stats.connected = false;
  }

  /**
   * Send message to server
   */
  send<T>(type: WebSocketEventType, data: T): string {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    const id = `msg-${++this.messageId}`;
    const message: WebSocketMessage<T> = {
      type,
      data,
      timestamp: Date.now(),
      id,
    };

    this.ws.send(JSON.stringify(message));
    this.stats.messagesSent++;
    this.log('Message sent:', message);

    return id;
  }

  /**
   * Subscribe to event type
   */
  on<T = any>(type: WebSocketEventType, listener: EventListener<T>): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }

    this.listeners.get(type)!.add(listener as EventListener);

    // Return unsubscribe function
    return () => {
      this.listeners.get(type)?.delete(listener as EventListener);
    };
  }

  /**
   * Subscribe to single event
   */
  once<T = any>(type: WebSocketEventType, listener: EventListener<T>): () => void {
    const wrappedListener: EventListener = (message) => {
      listener(message);
      unsubscribe();
    };

    const unsubscribe = this.on(type, wrappedListener as EventListener<T>);
    return unsubscribe;
  }

  /**
   * Unsubscribe from event type
   */
  off(type: WebSocketEventType, listener?: EventListener): void {
    if (!listener) {
      this.listeners.delete(type);
    } else {
      this.listeners.get(type)?.delete(listener);
    }
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.stats.connected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get WebSocket statistics
   */
  getStats() {
    return {
      ...this.stats,
      url: this.url,
      readyState: this.ws?.readyState,
    };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = {
      connected: this.stats.connected,
      messagesReceived: 0,
      messagesSent: 0,
      reconnects: 0,
      errors: 0,
    };
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      this.stats.messagesReceived++;
      this.log('Message received:', message);

      // Emit to listeners
      const listeners = this.listeners.get(message.type);
      if (listeners) {
        listeners.forEach((listener) => listener(message));
      }
    } catch (error) {
      this.log('Failed to parse message:', error);
      this.stats.errors++;
    }
  }

  /**
   * Attempt to reconnect
   */
  private async attemptReconnect(): Promise<void> {
    if (this.reconnectAttempt >= this.config.reconnectAttempts) {
      this.log('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempt++;
    this.stats.reconnects++;

    const delay = this.config.reconnectDelay * this.reconnectAttempt;
    this.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempt})`);

    await new Promise((resolve) => setTimeout(resolve, delay));

    try {
      await this.connect();
    } catch (error) {
      this.log('Reconnection failed:', error);
      this.attemptReconnect();
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send('message', { type: 'heartbeat' });
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Log debug message
   */
  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[WebSocket]', ...args);
    }
  }

  /**
   * Get listener count for event type
   */
  getListenerCount(type?: WebSocketEventType): number {
    if (type) {
      return this.listeners.get(type)?.size ?? 0;
    }

    let total = 0;
    for (const listeners of this.listeners.values()) {
      total += listeners.size;
    }
    return total;
  }

  /**
   * Clear all listeners
   */
  clearListeners(): void {
    this.listeners.clear();
  }
}

/**
 * Global WebSocket instance
 */
let globalWsClient: WebSocketClient | null = null;

/**
 * Get or create global WebSocket client
 */
export function getWebSocketClient(config?: WebSocketConfig): WebSocketClient {
  if (!globalWsClient && config) {
    globalWsClient = new WebSocketClient(config);
  }

  if (!globalWsClient) {
    throw new Error('WebSocket client not initialized. Provide config.');
  }

  return globalWsClient;
}
