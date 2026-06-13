'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface StreamingChatProps {
  userId: string;
  onError?: (error: string) => void;
}

export default function StreamingChat({ userId, onError }: StreamingChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize WebSocket
  const wsUrl = typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${userId}`
    : 'ws://localhost:3000/ws/default';

  const { isConnected, on } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
  });

  // Setup message streaming listener
  useEffect(() => {
    const unsubscribe = on('message_chunk', (message) => {
      const data = message.data as any;

      if (data.message_id && streamingId === data.message_id) {
        setMessages((prev) => {
          const updated = [...prev];
          const lastMessage = updated[updated.length - 1];

          if (lastMessage && lastMessage.isStreaming) {
            lastMessage.content += data.chunk;
          }

          return updated;
        });
      }
    });

    return () => {
      unsubscribe?.();
    };
  }, [streamingId, on]);

  // Setup message completion listener
  useEffect(() => {
    const unsubscribe = on('message_completed', (message) => {
      const data = message.data as any;

      if (data.message_id && streamingId === data.message_id) {
        setMessages((prev) => {
          const updated = [...prev];
          const lastMessage = updated[updated.length - 1];

          if (lastMessage && lastMessage.isStreaming) {
            lastMessage.isStreaming = false;
          }

          return updated;
        });

        setStreamingId(null);
        setIsLoading(false);
      }
    });

    return () => {
      unsubscribe?.();
    };
  }, [streamingId, on]);

  // Setup error listener
  useEffect(() => {
    const unsubscribe = on('error', (message) => {
      const data = message.data as any;
      const error = data.error || 'Unknown error occurred';
      onError?.(error);
      setIsLoading(false);
    });

    return () => {
      unsubscribe?.();
    };
  }, [on, onError]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = useCallback(async () => {
    if (!input.trim() || isLoading || !isConnected) {
      return;
    }

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    // Add streaming assistant message
    const assistantMessageId = `msg-${Date.now()}-assistant`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setStreamingId(assistantMessageId);
    setIsLoading(true);

    try {
      // Send message via REST API for processing
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          message_id: assistantMessageId,
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      onError?.(errorMessage);
      setIsLoading(false);
      setStreamingId(null);
    }
  }, [input, isLoading, isConnected, onError]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 p-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center text-gray-600 dark:text-gray-400">
              <p className="text-lg font-medium mb-2">Start a conversation</p>
              <p className="text-sm">Messages will stream in real-time</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                }`}
              >
                <p className="break-words text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.isStreaming && (
                  <span className="ml-2 inline-block h-2 w-2 animate-pulse rounded-full bg-current" />
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Connection Status */}
      <div className="border-t border-gray-200 bg-white px-6 py-2 dark:border-gray-700 dark:bg-gray-900">
        {!isConnected && (
          <p className="text-xs text-yellow-600 dark:text-yellow-400">
            Connecting to server...
          </p>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={isLoading || !isConnected}
            className="dev-input flex-1 resize-none"
            rows={3}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !input.trim() || !isConnected}
            className="dev-button-primary self-end"
          >
            {isLoading ? '⏳' : '→'}
          </button>
        </div>
      </div>
    </div>
  );
}
