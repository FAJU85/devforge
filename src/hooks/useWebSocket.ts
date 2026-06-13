import { useEffect, useRef, useCallback, useState } from 'react';

export type WebSocketEventType =
  | 'task_created'
  | 'task_started'
  | 'task_progress'
  | 'task_completed'
  | 'task_failed'
  | 'message_chunk'
  | 'message_completed'
  | 'error';

export interface WebSocketMessage {
  event: WebSocketEventType;
  timestamp: string;
  data: Record<string, any>;
}

export interface WebSocketHookOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (options: WebSocketHookOptions = {}) => {
  const {
    url = typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
      : 'ws://localhost:3000/ws',
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageHandlersRef = useRef<Map<WebSocketEventType, Set<(msg: WebSocketMessage) => void>>>(
    new Map()
  );

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        setReconnectCount(0);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          const handlers = messageHandlersRef.current.get(message.event);
          if (handlers) {
            handlers.forEach((handler) => handler(message));
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;

        if (reconnectCount < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount((prev) => prev + 1);
            connect();
          }, reconnectInterval);
        } else {
          setError('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Error creating WebSocket:', e);
      setError(e instanceof Error ? e.message : 'Failed to connect');
    }
  }, [url, reconnectInterval, maxReconnectAttempts, reconnectCount]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  const on = useCallback((eventType: WebSocketEventType, handler: (msg: WebSocketMessage) => void) => {
    if (!messageHandlersRef.current.has(eventType)) {
      messageHandlersRef.current.set(eventType, new Set());
    }
    messageHandlersRef.current.get(eventType)!.add(handler);

    return () => {
      const handlers = messageHandlersRef.current.get(eventType);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }, []);

  const off = useCallback((eventType: WebSocketEventType, handler: (msg: WebSocketMessage) => void) => {
    const handlers = messageHandlersRef.current.get(eventType);
    if (handlers) {
      handlers.delete(handler);
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    error,
    reconnectCount,
    connect,
    disconnect,
    on,
    off,
  };
};
