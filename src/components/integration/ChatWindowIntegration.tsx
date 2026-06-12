/**
 * ChatWindow Component Integration Example
 * Shows how to integrate useChat hook with the ChatWindow component
 */

import React, { useEffect, useState } from 'react';
import { useChat } from '../hooks/useChat';

interface ChatWindowIntegrationProps {
  apiBaseUrl?: string;
  authToken?: string;
  onError?: (error: Error) => void;
}

export const ChatWindowIntegration: React.FC<ChatWindowIntegrationProps> = ({
  apiBaseUrl = 'http://localhost:3000/api',
  authToken,
  onError,
}) => {
  const chat = useChat(apiBaseUrl);
  const [messageInput, setMessageInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize conversation on mount
  useEffect(() => {
    const initializeChat = async () => {
      try {
        if (!chat.activeConversationId) {
          await chat.createConversation('New Chat');
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error.message);
        onError?.(error);
      }
    };

    initializeChat();
  }, [chat]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!messageInput.trim() || !chat.activeConversationId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await chat.sendMessage(
        chat.activeConversationId,
        messageInput,
        'claude-opus',
        0.7
      );
      setMessageInput('');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      setError(null);
      await chat.createConversation('New Chat');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message);
      onError?.(error);
    }
  };

  const currentMessages = chat.activeConversationId
    ? chat.getConversationMessages(chat.activeConversationId)
    : [];

  return (
    <div className="chat-window-integration">
      {/* Error Display */}
      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Conversation List */}
      <div className="conversation-list">
        <h3>Conversations</h3>
        <button onClick={handleNewConversation} className="btn btn-primary">
          New Conversation
        </button>
        <ul>
          {chat.conversations.map((conv) => (
            <li key={conv.id}>
              <button
                onClick={() => chat.switchConversation(conv.id)}
                className={conv.id === chat.activeConversationId ? 'active' : ''}
              >
                {conv.title}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Messages Display */}
      <div className="messages-container">
        {currentMessages.length === 0 ? (
          <div className="empty-state">
            Start a new conversation or select one from the list
          </div>
        ) : (
          currentMessages.map((msg) => (
            <div key={msg.id} className={`message message-${msg.role}`}>
              <div className="message-content">{msg.content}</div>
              <div className="message-meta">
                {msg.tokens && <span className="tokens">{msg.tokens} tokens</span>}
                {msg.timestamp && (
                  <span className="timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Message Input */}
      <form onSubmit={handleSendMessage} className="message-input-form">
        <textarea
          value={messageInput}
          onChange={(e) => setMessageInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading || !chat.activeConversationId}
          rows={3}
        />
        <button
          type="submit"
          disabled={isLoading || !messageInput.trim() || !chat.activeConversationId}
          className="btn btn-primary"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>

      {/* Stats */}
      <div className="chat-stats">
        <span>Total Tokens: {chat.getTotalTokens()}</span>
        {chat.activeConversationId && (
          <span>
            Conversation Tokens: {chat.getConversationTokens(chat.activeConversationId)}
          </span>
        )}
      </div>
    </div>
  );
};
