/**
 * useRealtimeUpdates Hook - real-time synchronization with WebSocket
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketClient, WebSocketMessage, WebSocketEventType } from '../api/websocketClient';

export interface RealtimeConfig {
  url: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  debug?: boolean;
}

export interface UseRealtimeUpdatesReturn {
  // Connection state
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;

  // Connection control
  connect: () => Promise<void>;
  disconnect: () => void;
  reconnect: () => Promise<void>;

  // Event handling
  on: <T = any>(type: WebSocketEventType, listener: (msg: WebSocketMessage<T>) => void) => () => void;
  once: <T = any>(type: WebSocketEventType, listener: (msg: WebSocketMessage<T>) => void) => () => void;
  off: (type: WebSocketEventType, listener?: (msg: WebSocketMessage<any>) => void) => void;

  // Sending messages
  send: <T = any>(type: WebSocketEventType, data: T) => string;

  // Statistics
  getStats: () => any;
  resetStats: () => void;

  // WebSocket client reference
  client: WebSocketClient | null;
}

export function useRealtimeUpdates(config: RealtimeConfig): UseRealtimeUpdatesReturn {
  const clientRef = useRef<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize WebSocket client
  useEffect(() => {
    const client = new WebSocketClient({
      url: config.url,
      reconnectAttempts: config.reconnectAttempts,
      reconnectDelay: config.reconnectDelay,
      debug: config.debug,
    });

    clientRef.current = client;

    // Auto-connect if enabled
    if (config.autoConnect ?? true) {
      const connectAsync = async () => {
        setIsConnecting(true);
        try {
          await client.connect();
          setIsConnected(true);
          setError(null);
        } catch (err) {
          const errMsg = err instanceof Error ? err.message : String(err);
          setError(errMsg);
          setIsConnected(false);
        } finally {
          setIsConnecting(false);
        }
      };

      connectAsync();
    }

    // Setup connection listeners
    const unsubscribeOpen = client.on('status', (msg) => {
      if (msg.data?.type === 'connected') {
        setIsConnected(true);
        setError(null);
      }
    });

    const unsubscribeClose = client.on('status', (msg) => {
      if (msg.data?.type === 'disconnected') {
        setIsConnected(false);
      }
    });

    const unsubscribeError = client.on('error', (msg) => {
      setError(msg.data?.message || 'Connection error');
    });

    // Cleanup
    return () => {
      unsubscribeOpen();
      unsubscribeClose();
      unsubscribeError();
      client.disconnect();
    };
  }, [config.url, config.reconnectAttempts, config.reconnectDelay, config.debug]);

  const connect = useCallback(async () => {
    if (!clientRef.current) {
      throw new Error('WebSocket client not initialized');
    }

    setIsConnecting(true);
    try {
      await clientRef.current.connect();
      setIsConnected(true);
      setError(null);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setError(errMsg);
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      setIsConnected(false);
    }
  }, []);

  const reconnect = useCallback(async () => {
    disconnect();
    await new Promise((resolve) => setTimeout(resolve, 1000));
    await connect();
  }, [connect, disconnect]);

  const on = useCallback(
    <T = any>(type: WebSocketEventType, listener: (msg: WebSocketMessage<T>) => void) => {
      if (!clientRef.current) {
        return () => {};
      }
      return clientRef.current.on(type, listener);
    },
    []
  );

  const once = useCallback(
    <T = any>(type: WebSocketEventType, listener: (msg: WebSocketMessage<T>) => void) => {
      if (!clientRef.current) {
        return () => {};
      }
      return clientRef.current.once(type, listener);
    },
    []
  );

  const off = useCallback(
    (type: WebSocketEventType, listener?: (msg: WebSocketMessage<any>) => void) => {
      if (!clientRef.current) {
        return;
      }
      clientRef.current.off(type, listener);
    },
    []
  );

  const send = useCallback(<T = any>(type: WebSocketEventType, data: T) => {
    if (!clientRef.current) {
      throw new Error('WebSocket not connected');
    }
    return clientRef.current.send(type, data);
  }, []);

  const getStats = useCallback(() => {
    return clientRef.current?.getStats() ?? null;
  }, []);

  const resetStats = useCallback(() => {
    clientRef.current?.resetStats();
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    connect,
    disconnect,
    reconnect,
    on,
    once,
    off,
    send,
    getStats,
    resetStats,
    client: clientRef.current,
  };
}
