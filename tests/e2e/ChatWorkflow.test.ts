import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useChatStore } from '../../src/stores/chatStore';
import { useConfigStore } from '../../src/stores/configStore';
import { useContextStore } from '../../src/stores/contextStore';
import { useStatsStore } from '../../src/stores/statsStore';
import { useMemoryStore } from '../../src/stores/memoryStore';
import { useUIStore } from '../../src/stores/uiStore';

describe('Chat Workflow E2E Tests', () => {
  beforeEach(() => {
    // Reset all stores
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isLoading: false,
      currentInput: '',
    });

    useConfigStore.setState({
      providers: [],
      activeProviderId: null,
      models: [],
      activeModelId: null,
      temperature: 0.7,
      maxTokens: 2000,
      topP: 1,
      topK: 0,
      featureFlags: {
        canaryDeployment: false,
        betaFeatures: false,
        autoSave: true,
        diffViewer: true,
        batchOperations: true,
      },
    });

    useContextStore.setState({
      files: [],
      totalTokens: 0,
      maxTokens: 8000,
      references: [],
      createdAt: new Date(),
      lastUpdated: new Date(),
    });

    useMemoryStore.setState({
      memories: [],
      conversationMemories: [],
      recentContext: [],
      maxRecentContext: 20,
    });

    useStatsStore.setState({
      dailyMetrics: [],
      modelStats: [],
      totalMessages: 0,
      totalTokens: 0,
      totalCost: 0,
      periodStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      periodEnd: new Date(),
    });

    useUIStore.setState({
      toasts: [],
      showSettingsModal: false,
      showCommandPalette: false,
      showDiffViewer: false,
      showWritePanel: false,
      showBatchPanel: false,
      sidebarCollapsed: false,
      showContextPanel: true,
      theme: 'dark',
    });
  });

  describe('Basic Chat Flow', () => {
    it('should complete basic chat workflow', () => {
      const chatState = useChatStore.getState();
      const configState = useConfigStore.getState();
      const statsState = useStatsStore.getState();
      const uiState = useUIStore.getState();

      // Setup configuration
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
        apiKey: 'sk-test',
      });

      configState.addModel({
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      });

      expect(useConfigStore.getState().isConfigurationValid()).toBe(true);

      // Create conversation
      const convId = chatState.createConversation('First Chat');
      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().currentConversationId).toBe(convId);

      // Add user message
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: 'Hello, how can you help?',
        tokens: 10,
        timestamp: new Date(),
      });

      // Simulate loading
      chatState.setLoading(true);
      expect(useChatStore.getState().isLoading).toBe(true);

      // Add assistant response
      chatState.addMessage(convId, {
        id: 'msg-2',
        role: 'assistant',
        content: 'I can help with code reviews and explanations.',
        tokens: 15,
        timestamp: new Date(),
      });

      chatState.setLoading(false);

      // Record usage
      statsState.recordUsage({
        tokensUsed: 25,
        messagesCount: 2,
        modelUsed: 'gpt-4',
        cost: 0.001,
      });

      // Show notification
      const toastId = uiState.addToast({
        message: 'Chat completed successfully',
        type: 'success',
        duration: 3000,
      });

      expect(useChatStore.getState().getConversationMessages(convId)).toHaveLength(2);
      expect(useStatsStore.getState().totalMessages).toBe(2);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });
  });

  describe('Multiple Conversation Workflow', () => {
    it('should manage multiple conversations independently', () => {
      const chatState = useChatStore.getState();

      // Create first conversation
      const conv1 = chatState.createConversation('Project Discussion');
      chatState.addMessage(conv1, {
        id: 'msg-1',
        role: 'user',
        content: 'Explain architecture',
        tokens: 5,
        timestamp: new Date(),
      });

      // Create second conversation
      const conv2 = chatState.createConversation('Bug Report');
      chatState.addMessage(conv2, {
        id: 'msg-2',
        role: 'user',
        content: 'I found a bug',
        tokens: 4,
        timestamp: new Date(),
      });

      // Switch to first conversation
      chatState.setCurrentConversation(conv1);
      expect(useChatStore.getState().currentConversationId).toBe(conv1);
      expect(useChatStore.getState().getConversationMessages(conv1)).toHaveLength(1);
      expect(useChatStore.getState().getConversationMessages(conv2)).toHaveLength(1);

      // Add to first conversation
      chatState.addMessage(conv1, {
        id: 'msg-3',
        role: 'assistant',
        content: 'Architecture overview...',
        tokens: 10,
        timestamp: new Date(),
      });

      expect(useChatStore.getState().getConversationMessages(conv1)).toHaveLength(2);
      expect(useChatStore.getState().getConversationMessages(conv2)).toHaveLength(1);

      // Switch and delete
      chatState.setCurrentConversation(conv2);
      chatState.deleteConversation(conv2);

      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().currentConversationId).toBe(conv1);
    });
  });

  describe('Chat with Context Workflow', () => {
    it('should integrate chat with file context', () => {
      const chatState = useChatStore.getState();
      const contextState = useContextStore.getState();
      const statsState = useStatsStore.getState();

      // Create conversation
      const convId = chatState.createConversation('Code Review');

      // Add context files
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        content: 'export function main() { return "hello"; }',
        tokens: 100,
        language: 'typescript',
      });

      contextState.addFile({
        id: 'file-2',
        path: '/src/utils.ts',
        name: 'utils.ts',
        tokens: 200,
        language: 'typescript',
      });

      expect(useContextStore.getState().totalTokens).toBe(300);

      // User asks about context
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: 'Review the code in context',
        tokens: 50,
        timestamp: new Date(),
      });

      // Assistant responds
      chatState.addMessage(convId, {
        id: 'msg-2',
        role: 'assistant',
        content: 'The code looks good. Consider adding error handling.',
        tokens: 75,
        timestamp: new Date(),
      });

      // Record comprehensive stats
      statsState.recordUsage({
        tokensUsed: 300 + 125, // context + messages
        messagesCount: 2,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      expect(useChatStore.getState().getTotalTokens(convId)).toBe(125);
      expect(useContextStore.getState().totalTokens).toBe(300);
      expect(useStatsStore.getState().totalTokens).toBe(425);
    });
  });

  describe('Chat with Memory Workflow', () => {
    it('should save and retrieve chat memories', () => {
      const chatState = useChatStore.getState();
      const memoryState = useMemoryStore.getState();

      // Create conversation
      const convId = chatState.createConversation('Learning Session');

      // Add messages
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: 'Teach me about TypeScript generics',
        tokens: 10,
        timestamp: new Date(),
      });

      chatState.addMessage(convId, {
        id: 'msg-2',
        role: 'assistant',
        content: 'Generics allow you to create reusable components...',
        tokens: 30,
        timestamp: new Date(),
      });

      // Save conversation to memory
      memoryState.saveConversationMemory({
        conversationId: convId,
        summary: 'User learned about TypeScript generics and their benefits',
        keyDecisions: [
          'Use T for type variable',
          'Implement extends constraint',
        ],
        relatedFiles: ['/src/types.ts', '/src/utils.ts'],
      });

      // Store context
      memoryState.addToRecentContext(`Conversation: TypeScript generics - ${convId}`);

      // Add preference memory
      memoryState.addMemory({
        key: 'learning_style',
        value: 'prefers_examples',
        category: 'preference',
      });

      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);
      expect(useMemoryStore.getState().recentContext).toHaveLength(1);
      expect(useMemoryStore.getState().memories).toHaveLength(1);

      // Retrieve conversation
      const savedMemory = memoryState.getConversationMemory(convId);
      expect(savedMemory?.summary).toContain('TypeScript generics');
    });
  });

  describe('Error Recovery Workflow', () => {
    it('should recover from chat errors gracefully', () => {
      const chatState = useChatStore.getState();
      const uiState = useUIStore.getState();

      // Create conversation
      const convId = chatState.createConversation('Risky Operation');

      // Attempt to add message
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: 'Do something risky',
        tokens: 5,
        timestamp: new Date(),
      });

      // Simulate error
      chatState.setLoading(false); // Stop loading
      uiState.addToast({
        message: 'Error occurred during processing',
        type: 'error',
        duration: 5000,
      });

      // Recovery: Add error message
      chatState.addMessage(convId, {
        id: 'msg-2',
        role: 'assistant',
        content: 'An error occurred. Please try again.',
        tokens: 10,
        timestamp: new Date(),
      });

      expect(useChatStore.getState().isLoading).toBe(false);
      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useChatStore.getState().getConversationMessages(convId)).toHaveLength(2);
    });
  });

  describe('Chat Performance Workflow', () => {
    it('should handle high-volume chat efficiently', () => {
      const chatState = useChatStore.getState();
      const statsState = useStatsStore.getState();

      const convId = chatState.createConversation('High Volume Chat');

      // Simulate rapid messages
      for (let i = 0; i < 50; i++) {
        if (i % 2 === 0) {
          chatState.addMessage(convId, {
            id: `msg-${i}`,
            role: 'user',
            content: `Message ${i}`,
            tokens: 10,
            timestamp: new Date(),
          });
        } else {
          chatState.addMessage(convId, {
            id: `msg-${i}`,
            role: 'assistant',
            content: `Response ${i}`,
            tokens: 20,
            timestamp: new Date(),
          });
        }
      }

      // Record aggregate usage
      statsState.recordUsage({
        tokensUsed: 750, // 50 * 15 avg
        messagesCount: 50,
        modelUsed: 'gpt-4',
        cost: 0.015,
      });

      expect(useChatStore.getState().getConversationMessages(convId)).toHaveLength(50);
      expect(useStatsStore.getState().totalMessages).toBe(50);
      expect(useStatsStore.getState().getAverageTokensPerMessage()).toBe(15);
    });
  });

  describe('Chat with Input Workflow', () => {
    it('should manage chat input state correctly', () => {
      const chatState = useChatStore.getState();

      const convId = chatState.createConversation('Input Test');

      // User types
      chatState.setCurrentInput('Hello, ');
      expect(useChatStore.getState().currentInput).toBe('Hello, ');

      chatState.setCurrentInput('Hello, I need help');
      expect(useChatStore.getState().currentInput).toBe('Hello, I need help');

      // Send message (typically clears input)
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: useChatStore.getState().currentInput,
        tokens: 5,
        timestamp: new Date(),
      });

      chatState.setCurrentInput(''); // Clear after send
      expect(useChatStore.getState().currentInput).toBe('');

      // New message
      chatState.setCurrentInput('Follow-up question');
      expect(useChatStore.getState().currentInput).toBe('Follow-up question');
    });
  });

  describe('End-to-End Chat Complete Scenario', () => {
    it('should execute complete chat scenario with all stores', () => {
      // Initialize config
      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
        apiKey: 'sk-test-123',
      });
      configState.addModel({
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
        costPer1kTokens: { input: 0.03, output: 0.06 },
      });
      configState.updateSettings({ temperature: 0.7, maxTokens: 2000 });

      // Create chat conversation
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('DevForge Development');

      // Add context
      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'store-ts',
        path: '/src/stores/chatStore.ts',
        name: 'chatStore.ts',
        tokens: 500,
        language: 'typescript',
      });
      contextState.addFile({
        id: 'component-ts',
        path: '/src/components/Chat.tsx',
        name: 'Chat.tsx',
        tokens: 400,
        language: 'typescript',
      });

      // User interaction
      chatState.setCurrentInput('How should I implement state management?');
      chatState.addMessage(convId, {
        id: 'msg-user-1',
        role: 'user',
        content: 'How should I implement state management?',
        tokens: 10,
        timestamp: new Date(),
      });
      chatState.setCurrentInput('');

      // AI response (simulated)
      chatState.setLoading(true);
      chatState.addMessage(convId, {
        id: 'msg-ai-1',
        role: 'assistant',
        content: 'Use Zustand for lightweight state management with good TypeScript support.',
        tokens: 20,
        timestamp: new Date(),
      });
      chatState.setLoading(false);

      // Follow-up
      chatState.setCurrentInput('What are the benefits?');
      chatState.addMessage(convId, {
        id: 'msg-user-2',
        role: 'user',
        content: 'What are the benefits?',
        tokens: 5,
        timestamp: new Date(),
      });
      chatState.setCurrentInput('');

      chatState.addMessage(convId, {
        id: 'msg-ai-2',
        role: 'assistant',
        content: 'Zustand offers: minimal boilerplate, excellent performance, and seamless TypeScript integration.',
        tokens: 20,
        timestamp: new Date(),
      });

      // Record statistics
      const statsState = useStatsStore.getState();
      statsState.updateModelStats('gpt-4', 'openai', 55, 0.003);
      statsState.recordUsage({
        tokensUsed: 955, // 900 context + 55 conversation
        messagesCount: 4,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      // Save to memory
      const memoryState = useMemoryStore.getState();
      memoryState.saveConversationMemory({
        conversationId: convId,
        summary: 'Discussed state management with Zustand',
        keyDecisions: ['Use Zustand', 'TypeScript support is important'],
        relatedFiles: ['/src/stores/chatStore.ts', '/src/components/Chat.tsx'],
      });
      memoryState.addMemory({
        key: 'preferred_state_lib',
        value: 'zustand',
        category: 'preference',
      });

      // UI notifications
      const uiState = useUIStore.getState();
      uiState.addToast({
        message: 'Chat completed successfully',
        type: 'success',
        duration: 3000,
      });

      // Verify complete state
      expect(useConfigStore.getState().isConfigurationValid()).toBe(true);
      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().getConversationMessages(convId)).toHaveLength(4);
      expect(useContextStore.getState().files).toHaveLength(2);
      expect(useContextStore.getState().totalTokens).toBe(900);
      expect(useStatsStore.getState().totalMessages).toBe(4);
      expect(useStatsStore.getState().totalTokens).toBe(955);
      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);
      expect(useMemoryStore.getState().memories).toHaveLength(1);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });
  });
});
