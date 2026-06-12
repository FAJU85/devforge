/**
 * useChat Hook - custom hook for chat operations
 */

import { useCallback } from 'react';
import { useChatStore } from '../stores/chatStore';
import { useStatsStore } from '../stores/statsStore';
import { ChatService } from '../services/chatService';

export interface UseChatReturn {
  // State
  conversations: ReturnType<typeof useChatStore>['conversations'];
  activeConversationId: ReturnType<typeof useChatStore>['activeConversationId'];
  messages: ReturnType<typeof useChatStore>['messages'];

  // Actions
  createConversation: (title?: string) => Promise<string>;
  deleteConversation: (conversationId: string) => Promise<boolean>;
  switchConversation: (conversationId: string) => void;
  clearConversations: () => void;

  // Messages
  sendMessage: (conversationId: string, content: string, model?: string) => Promise<any>;
  addMessage: (conversationId: string, message: any) => string;
  getConversationMessages: (conversationId: string) => any[];

  // Stats
  getTotalTokens: () => number;
  getConversationTokens: (conversationId: string) => number;
}

export function useChat(apiBaseUrl: string = 'http://localhost:3000/api'): UseChatReturn {
  const chatStore = useChatStore();
  const statsStore = useStatsStore();
  const chatService = new ChatService(apiBaseUrl);

  const createConversation = useCallback(
    async (title?: string) => {
      try {
        return await chatService.createConversation(title);
      } catch (error) {
        console.error('Failed to create conversation:', error);
        throw error;
      }
    },
    [chatService]
  );

  const deleteConversation = useCallback(
    async (conversationId: string) => {
      try {
        return await chatService.deleteConversation(conversationId);
      } catch (error) {
        console.error('Failed to delete conversation:', error);
        throw error;
      }
    },
    [chatService]
  );

  const switchConversation = useCallback(
    (conversationId: string) => {
      chatStore.setActiveConversation(conversationId);
    },
    [chatStore]
  );

  const clearConversations = useCallback(() => {
    chatStore.clearConversations();
  }, [chatStore]);

  const sendMessage = useCallback(
    async (conversationId: string, content: string, model?: string) => {
      try {
        return await chatService.sendMessage(conversationId, content, model);
      } catch (error) {
        console.error('Failed to send message:', error);
        throw error;
      }
    },
    [chatService]
  );

  const addMessage = useCallback(
    (conversationId: string, message: any) => {
      return chatStore.addMessage(conversationId, message);
    },
    [chatStore]
  );

  const getConversationMessages = useCallback(
    (conversationId: string) => {
      return chatStore.getConversationMessages(conversationId);
    },
    [chatStore]
  );

  const getTotalTokens = useCallback(() => {
    return statsStore.totalTokens;
  }, [statsStore]);

  const getConversationTokens = useCallback(
    (conversationId: string) => {
      return chatStore.getTotalTokens(conversationId);
    },
    [chatStore]
  );

  return {
    conversations: chatStore.conversations,
    activeConversationId: chatStore.activeConversationId,
    messages: chatStore.messages,
    createConversation,
    deleteConversation,
    switchConversation,
    clearConversations,
    sendMessage,
    addMessage,
    getConversationMessages,
    getTotalTokens,
    getConversationTokens,
  };
}
