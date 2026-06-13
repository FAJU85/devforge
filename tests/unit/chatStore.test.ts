import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useChatStore, ChatMessage, Conversation } from '../../src/stores/chatStore';

describe('Chat Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    const store = useChatStore.getState();
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isLoading: false,
      currentInput: '',
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useChatStore.getState();
      expect(state.conversations).toEqual([]);
      expect(state.currentConversationId).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.currentInput).toBe('');
    });
  });

  describe('Conversation Management', () => {
    it('should create a conversation', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test Chat');

      expect(convId).toMatch(/^conv-\d+$/);
      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().currentConversationId).toBe(convId);
    });

    it('should create conversation with correct properties', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('My Conversation');
      const conversation = useChatStore.getState().conversations[0];

      expect(conversation.id).toBe(convId);
      expect(conversation.title).toBe('My Conversation');
      expect(conversation.messages).toEqual([]);
      expect(conversation.createdAt).toBeInstanceOf(Date);
      expect(conversation.updatedAt).toBeInstanceOf(Date);
    });

    it('should set current conversation', () => {
      const state = useChatStore.getState();
      const convId1 = state.createConversation('First');
      const convId2 = state.createConversation('Second');

      state.setCurrentConversation(convId1);
      expect(useChatStore.getState().currentConversationId).toBe(convId1);

      state.setCurrentConversation(convId2);
      expect(useChatStore.getState().currentConversationId).toBe(convId2);
    });

    it('should clear input when setting conversation', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      state.setCurrentInput('Some text');
      expect(useChatStore.getState().currentInput).toBe('Some text');

      state.setCurrentConversation(convId);
      expect(useChatStore.getState().currentInput).toBe('');
    });

    it('should delete a conversation', () => {
      const state = useChatStore.getState();
      const convId1 = state.createConversation('First');
      const convId2 = state.createConversation('Second');

      expect(useChatStore.getState().conversations).toHaveLength(2);

      state.deleteConversation(convId1);
      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().conversations[0].id).toBe(convId2);
    });

    it('should clear current conversation ID when deleting active conversation', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      expect(useChatStore.getState().currentConversationId).toBe(convId);

      state.deleteConversation(convId);
      expect(useChatStore.getState().currentConversationId).toBeNull();
    });

    it('should not clear current conversation ID when deleting inactive conversation', () => {
      const state = useChatStore.getState();
      const convId1 = state.createConversation('First');
      const convId2 = state.createConversation('Second');

      state.setCurrentConversation(convId1);
      state.deleteConversation(convId2);

      expect(useChatStore.getState().currentConversationId).toBe(convId1);
    });
  });

  describe('Message Management', () => {
    let conversationId: string;

    beforeEach(() => {
      const state = useChatStore.getState();
      conversationId = state.createConversation('Test Chat');
    });

    it('should add a message to conversation', () => {
      const state = useChatStore.getState();
      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      state.addMessage(conversationId, message);

      const messages = useChatStore.getState().getConversationMessages(conversationId);
      expect(messages).toHaveLength(1);
      expect(messages[0].content).toBe('Hello');
    });

    it('should add multiple messages', () => {
      const state = useChatStore.getState();
      const msg1: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };
      const msg2: ChatMessage = {
        id: 'msg-2',
        role: 'assistant',
        content: 'Hi there!',
        timestamp: new Date(),
      };

      state.addMessage(conversationId, msg1);
      state.addMessage(conversationId, msg2);

      const messages = useChatStore.getState().getConversationMessages(conversationId);
      expect(messages).toHaveLength(2);
      expect(messages[0].role).toBe('user');
      expect(messages[1].role).toBe('assistant');
    });

    it('should update conversation timestamp when adding message', () => {
      const state = useChatStore.getState();
      const initialConv = useChatStore.getState().conversations[0];
      const initialTime = initialConv.updatedAt;

      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Test',
        timestamp: new Date(),
      };

      // Add small delay to ensure time difference
      state.addMessage(conversationId, message);

      const updatedConv = useChatStore.getState().conversations[0];
      expect(updatedConv.updatedAt.getTime()).toBeGreaterThanOrEqual(initialTime.getTime());
    });

    it('should remove a message', () => {
      const state = useChatStore.getState();
      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      state.addMessage(conversationId, message);
      expect(useChatStore.getState().getConversationMessages(conversationId)).toHaveLength(1);

      state.removeMessage(conversationId, 'msg-1');
      expect(useChatStore.getState().getConversationMessages(conversationId)).toHaveLength(0);
    });

    it('should clear all messages from conversation', () => {
      const state = useChatStore.getState();
      const msg1: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };
      const msg2: ChatMessage = {
        id: 'msg-2',
        role: 'assistant',
        content: 'Hi!',
        timestamp: new Date(),
      };

      state.addMessage(conversationId, msg1);
      state.addMessage(conversationId, msg2);
      expect(useChatStore.getState().getConversationMessages(conversationId)).toHaveLength(2);

      state.clearMessages(conversationId);
      expect(useChatStore.getState().getConversationMessages(conversationId)).toHaveLength(0);
    });

    it('should not affect other conversations when modifying one', () => {
      const state = useChatStore.getState();
      const convId2 = state.createConversation('Second Chat');

      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      state.addMessage(conversationId, message);

      expect(useChatStore.getState().getConversationMessages(conversationId)).toHaveLength(1);
      expect(useChatStore.getState().getConversationMessages(convId2)).toHaveLength(0);
    });
  });

  describe('Input Management', () => {
    it('should set current input', () => {
      const state = useChatStore.getState();
      state.setCurrentInput('Hello world');

      expect(useChatStore.getState().currentInput).toBe('Hello world');
    });

    it('should clear input', () => {
      const state = useChatStore.getState();
      state.setCurrentInput('Some text');
      state.setCurrentInput('');

      expect(useChatStore.getState().currentInput).toBe('');
    });

    it('should handle empty string input', () => {
      const state = useChatStore.getState();
      state.setCurrentInput('');

      expect(useChatStore.getState().currentInput).toBe('');
    });

    it('should handle multiline input', () => {
      const state = useChatStore.getState();
      const multiline = 'Line 1\nLine 2\nLine 3';
      state.setCurrentInput(multiline);

      expect(useChatStore.getState().currentInput).toBe(multiline);
    });
  });

  describe('Loading State', () => {
    it('should set loading state', () => {
      const state = useChatStore.getState();
      state.setLoading(true);

      expect(useChatStore.getState().isLoading).toBe(true);

      state.setLoading(false);
      expect(useChatStore.getState().isLoading).toBe(false);
    });

    it('should toggle loading state', () => {
      const state = useChatStore.getState();
      expect(useChatStore.getState().isLoading).toBe(false);

      state.setLoading(true);
      expect(useChatStore.getState().isLoading).toBe(true);

      state.setLoading(false);
      expect(useChatStore.getState().isLoading).toBe(false);
    });
  });

  describe('Getters', () => {
    it('should get current conversation', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      const current = state.getCurrentConversation();
      expect(current).toBeDefined();
      expect(current?.id).toBe(convId);
      expect(current?.title).toBe('Test');
    });

    it('should return undefined for non-existent current conversation', () => {
      const state = useChatStore.getState();
      const current = state.getCurrentConversation();

      expect(current).toBeUndefined();
    });

    it('should get conversation messages', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      state.addMessage(convId, message);
      const messages = state.getConversationMessages(convId);

      expect(messages).toHaveLength(1);
      expect(messages[0].id).toBe('msg-1');
    });

    it('should return empty array for non-existent conversation messages', () => {
      const state = useChatStore.getState();
      const messages = state.getConversationMessages('non-existent');

      expect(messages).toEqual([]);
    });

    it('should calculate total tokens for conversation', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      const msg1: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        tokens: 2,
        timestamp: new Date(),
      };

      const msg2: ChatMessage = {
        id: 'msg-2',
        role: 'assistant',
        content: 'Hi there!',
        tokens: 3,
        timestamp: new Date(),
      };

      state.addMessage(convId, msg1);
      state.addMessage(convId, msg2);

      const totalTokens = state.getTotalTokens(convId);
      expect(totalTokens).toBe(5);
    });

    it('should return 0 tokens for messages without token count', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      state.addMessage(convId, message);
      const totalTokens = state.getTotalTokens(convId);

      expect(totalTokens).toBe(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle adding message to non-existent conversation', () => {
      const state = useChatStore.getState();
      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
      };

      // Should not throw
      state.addMessage('non-existent', message);
      expect(useChatStore.getState().conversations).toHaveLength(0);
    });

    it('should handle removing message from non-existent conversation', () => {
      const state = useChatStore.getState();

      // Should not throw
      state.removeMessage('non-existent', 'msg-1');
      expect(useChatStore.getState().conversations).toHaveLength(0);
    });

    it('should handle empty conversation title', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('');

      const conversation = useChatStore.getState().conversations[0];
      expect(conversation.title).toBe('');
    });

    it('should handle special characters in messages', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: '<script>alert("xss")</script>',
        timestamp: new Date(),
      };

      state.addMessage(convId, message);
      const messages = state.getConversationMessages(convId);

      expect(messages[0].content).toBe('<script>alert("xss")</script>');
    });

    it('should handle null and undefined in message metadata', () => {
      const state = useChatStore.getState();
      const convId = state.createConversation('Test');

      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Hello',
        timestamp: new Date(),
        metadata: {
          model: undefined,
          provider: null as any,
        },
      };

      state.addMessage(convId, message);
      const messages = state.getConversationMessages(convId);

      expect(messages[0].metadata?.model).toBeUndefined();
    });
  });

  describe('Multiple Concurrent Operations', () => {
    it('should handle multiple conversations with messages', () => {
      const state = useChatStore.getState();
      const conv1 = state.createConversation('Chat 1');
      const conv2 = state.createConversation('Chat 2');
      const conv3 = state.createConversation('Chat 3');

      expect(useChatStore.getState().conversations).toHaveLength(3);

      const msg1: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Message 1',
        timestamp: new Date(),
      };

      const msg2: ChatMessage = {
        id: 'msg-2',
        role: 'assistant',
        content: 'Message 2',
        timestamp: new Date(),
      };

      state.addMessage(conv1, msg1);
      state.addMessage(conv2, msg2);

      expect(state.getConversationMessages(conv1)).toHaveLength(1);
      expect(state.getConversationMessages(conv2)).toHaveLength(1);
      expect(state.getConversationMessages(conv3)).toHaveLength(0);
    });
  });
});
