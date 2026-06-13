/**
 * Chat Store - conversation history, messages, and AI responses
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  tokens?: number;
  timestamp: Date;
  metadata?: {
    model?: string;
    provider?: string;
    responseTime?: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
  model?: string;
  provider?: string;
}

export interface ChatState {
  // Conversations
  conversations: Conversation[];
  currentConversationId: string | null;

  // Current message state
  isLoading: boolean;
  currentInput: string;

  // Actions
  createConversation: (title: string) => string;
  deleteConversation: (id: string) => void;
  setCurrentConversation: (id: string | null) => void;

  // Messages
  addMessage: (conversationId: string, message: ChatMessage) => void;
  removeMessage: (conversationId: string, messageId: string) => void;
  clearMessages: (conversationId: string) => void;

  // Input
  setCurrentInput: (input: string) => void;
  setLoading: (loading: boolean) => void;

  // Getters
  getCurrentConversation: () => Conversation | undefined;
  getConversationMessages: (id: string) => ChatMessage[];
  getTotalTokens: (id: string) => number;
}

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        conversations: [],
        currentConversationId: null,
        isLoading: false,
        currentInput: '',

        createConversation: (title) => {
          const id = `conv-${Date.now()}`;
          const newConversation: Conversation = {
            id,
            title,
            messages: [],
            createdAt: new Date(),
            updatedAt: new Date(),
          };

          set((state) => ({
            conversations: [...state.conversations, newConversation],
            currentConversationId: id,
          }));

          return id;
        },

        deleteConversation: (id) =>
          set((state) => ({
            conversations: state.conversations.filter((c) => c.id !== id),
            currentConversationId: state.currentConversationId === id ? null : state.currentConversationId,
          })),

        setCurrentConversation: (id) =>
          set({
            currentConversationId: id,
            currentInput: '',
          }),

        addMessage: (conversationId, message) =>
          set((state) => ({
            conversations: state.conversations.map((conv) =>
              conv.id === conversationId
                ? {
                    ...conv,
                    messages: [...conv.messages, message],
                    updatedAt: new Date(),
                  }
                : conv
            ),
          })),

        removeMessage: (conversationId, messageId) =>
          set((state) => ({
            conversations: state.conversations.map((conv) =>
              conv.id === conversationId
                ? {
                    ...conv,
                    messages: conv.messages.filter((m) => m.id !== messageId),
                    updatedAt: new Date(),
                  }
                : conv
            ),
          })),

        clearMessages: (conversationId) =>
          set((state) => ({
            conversations: state.conversations.map((conv) =>
              conv.id === conversationId
                ? {
                    ...conv,
                    messages: [],
                    updatedAt: new Date(),
                  }
                : conv
            ),
          })),

        setCurrentInput: (input) => set({ currentInput: input }),

        setLoading: (loading) => set({ isLoading: loading }),

        getCurrentConversation: () => {
          const state = get();
          return state.conversations.find((c) => c.id === state.currentConversationId);
        },

        getConversationMessages: (id) => {
          const state = get();
          const conv = state.conversations.find((c) => c.id === id);
          return conv?.messages || [];
        },

        getTotalTokens: (id) => {
          const state = get();
          const conv = state.conversations.find((c) => c.id === id);
          return conv?.messages.reduce((sum, msg) => sum + (msg.tokens || 0), 0) || 0;
        },
      }),
      {
        name: 'chat-store',
        version: 1,
      }
    ),
    { name: 'ChatStore' }
  )
);
