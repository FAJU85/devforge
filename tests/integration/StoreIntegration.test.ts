import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../../src/stores/chatStore';
import { useConfigStore } from '../../src/stores/configStore';
import { useContextStore } from '../../src/stores/contextStore';
import { useMemoryStore } from '../../src/stores/memoryStore';
import { useRepoStore } from '../../src/stores/repoStore';
import { useStatsStore } from '../../src/stores/statsStore';
import { useUIStore } from '../../src/stores/uiStore';

describe('Store Integration Tests', () => {
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

    useRepoStore.setState({
      repositories: [],
      currentRepoId: null,
      fileTree: [],
      selectedFileId: null,
      openFiles: [],
      searchQuery: '',
      filteredFiles: [],
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

  describe('Chat + Config Integration', () => {
    it('should create chat using configured model', () => {
      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      });
      configState.addModel({
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      });

      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Chat with GPT-4');

      expect(convId).toBeDefined();
      expect(useConfigStore.getState().getActiveModel()?.name).toBe('GPT-4');
      expect(useChatStore.getState().conversations).toHaveLength(1);
    });

    it('should respect configuration settings in chat', () => {
      const configState = useConfigStore.getState();
      configState.updateSettings({
        temperature: 0.5,
        maxTokens: 4000,
      });

      const chatState = useChatStore.getState();
      chatState.createConversation('Test');

      expect(useConfigStore.getState().temperature).toBe(0.5);
      expect(useConfigStore.getState().maxTokens).toBe(4000);
      expect(useChatStore.getState().conversations).toHaveLength(1);
    });
  });

  describe('Chat + Memory Integration', () => {
    it('should save conversation to memory', () => {
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Learning Session');

      const memoryState = useMemoryStore.getState();
      memoryState.saveConversationMemory({
        conversationId: convId,
        summary: 'User learned about React hooks',
        keyDecisions: ['Use custom hooks', 'Implement memo'],
        relatedFiles: ['/src/hooks.ts'],
      });

      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);
      expect(useMemoryStore.getState().conversationMemories[0].conversationId).toBe(convId);
    });

    it('should track conversation context in memory', () => {
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Development');

      const memoryState = useMemoryStore.getState();
      memoryState.addToRecentContext(`Conversation: ${convId}`);
      memoryState.addMemory({
        key: `conversation_${convId}`,
        value: { topic: 'Development', duration: 30 },
        category: 'context',
      });

      expect(useMemoryStore.getState().recentContext).toHaveLength(1);
      expect(useMemoryStore.getState().memories).toHaveLength(1);
    });
  });

  describe('Chat + Context Integration', () => {
    it('should add files to context during chat', () => {
      const chatState = useChatStore.getState();
      chatState.createConversation('Code Review');

      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useContextStore.getState().totalTokens).toBe(500);
    });

    it('should track token usage across chat and context', () => {
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Chat');

      const message = {
        id: 'msg-1',
        role: 'user' as const,
        content: 'Review this code',
        tokens: 100,
        timestamp: new Date(),
      };

      chatState.addMessage(convId, message);

      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      expect(useChatStore.getState().getTotalTokens(convId)).toBe(100);
      expect(useContextStore.getState().totalTokens).toBe(500);
    });
  });

  describe('Stats + Config Integration', () => {
    it('should track usage across configured models', () => {
      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      });
      configState.addModel({
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      });
      configState.addModel({
        id: 'gpt-3.5',
        name: 'GPT-3.5',
        provider: 'openai',
        contextWindow: 4096,
      });

      const statsState = useStatsStore.getState();
      statsState.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      statsState.recordUsage({
        tokensUsed: 50,
        messagesCount: 1,
        modelUsed: 'gpt-3.5',
        cost: 0.001,
      });

      expect(useConfigStore.getState().models).toHaveLength(2);
      expect(useStatsStore.getState().totalTokens).toBe(150);
      expect(useStatsStore.getState().totalMessages).toBe(2);
    });

    it('should update model stats based on provider configuration', () => {
      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      });
      configState.addModel({
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      });

      const statsState = useStatsStore.getState();
      statsState.updateModelStats('gpt-4', 'openai', 100, 0.003);
      statsState.updateModelStats('gpt-4', 'openai', 200, 0.006);

      const modelStats = statsState.getModelStats();
      expect(modelStats[0].model).toBe('gpt-4');
      expect(modelStats[0].provider).toBe('openai');
      expect(modelStats[0].totalTokens).toBe(300);
    });
  });

  describe('Repo + Context Integration', () => {
    it('should add repository files to context', () => {
      const repoState = useRepoStore.getState();
      const repo = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      repoState.addRepository(repo);
      repoState.setFileTree([
        {
          id: 'file-1',
          name: 'main.ts',
          path: '/src/main.ts',
          type: 'file' as const,
          language: 'typescript',
        },
      ]);

      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      expect(useRepoStore.getState().repositories).toHaveLength(1);
      expect(useContextStore.getState().files).toHaveLength(1);
    });

    it('should track file selection across repo and context', () => {
      const repoState = useRepoStore.getState();
      repoState.setFileTree([
        {
          id: 'file-1',
          name: 'main.ts',
          path: '/src/main.ts',
          type: 'file' as const,
        },
      ]);

      repoState.selectFile('file-1');
      repoState.openFile('file-1');

      expect(useRepoStore.getState().selectedFileId).toBe('file-1');
      expect(useRepoStore.getState().openFiles).toContain('file-1');
    });
  });

  describe('UI + All Stores Integration', () => {
    it('should show toast when adding chat conversation', () => {
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('New Chat');

      const uiState = useUIStore.getState();
      const toastId = uiState.addToast({
        message: `Conversation "${convId}" created`,
        type: 'success',
        duration: 3000,
      });

      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().toasts[0].id).toBe(toastId);
    });

    it('should coordinate modal states with other stores', () => {
      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: false,
      });

      const uiState = useUIStore.getState();
      uiState.setSettingsModal(true);

      expect(useConfigStore.getState().providers).toHaveLength(1);
      expect(useUIStore.getState().showSettingsModal).toBe(true);
    });

    it('should maintain UI state during config changes', () => {
      const uiState = useUIStore.getState();
      uiState.setTheme('light');
      uiState.setSidebarCollapsed(true);

      const configState = useConfigStore.getState();
      configState.updateSettings({ temperature: 0.5 });

      expect(useUIStore.getState().theme).toBe('light');
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      expect(useConfigStore.getState().temperature).toBe(0.5);
    });
  });

  describe('Complex Multi-Store Workflows', () => {
    it('should handle complete chat workflow with all stores', () => {
      // Setup configuration
      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      });
      configState.addModel({
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      });

      // Create chat conversation
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Code Review');

      // Add message
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: 'Review this code',
        tokens: 100,
        timestamp: new Date(),
      });

      // Add context files
      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      // Record stats
      const statsState = useStatsStore.getState();
      statsState.recordUsage({
        tokensUsed: 600,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      statsState.updateModelStats('gpt-4', 'openai', 600, 0.003);

      // Save conversation memory
      const memoryState = useMemoryStore.getState();
      memoryState.saveConversationMemory({
        conversationId: convId,
        summary: 'Code review completed',
        keyDecisions: ['Fix type annotations'],
        relatedFiles: ['/src/main.ts'],
      });

      // Show notification
      const uiState = useUIStore.getState();
      uiState.addToast({
        message: 'Code review completed',
        type: 'success',
        duration: 3000,
      });

      // Verify all stores
      expect(useConfigStore.getState().models).toHaveLength(1);
      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().getTotalTokens(convId)).toBe(100);
      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useStatsStore.getState().totalTokens).toBe(600);
      expect(useMemoryStore.getState().conversationMemories).toHaveLength(1);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });

    it('should handle repository management with context and stats', () => {
      // Setup repository
      const repoState = useRepoStore.getState();
      const repo = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      repoState.addRepository(repo);
      repoState.setFileTree([
        {
          id: 'file-1',
          name: 'store.ts',
          path: '/src/stores/store.ts',
          type: 'file' as const,
          language: 'typescript',
        },
      ]);

      repoState.selectFile('file-1');
      repoState.openFile('file-1');

      // Add to context
      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'file-1',
        path: '/src/stores/store.ts',
        name: 'store.ts',
        tokens: 1000,
        language: 'typescript',
      });

      // Record operation
      const statsState = useStatsStore.getState();
      statsState.recordUsage({
        tokensUsed: 1000,
        messagesCount: 0,
        modelUsed: 'analysis',
        cost: 0,
      });

      // Show status
      const uiState = useUIStore.getState();
      uiState.addToast({
        message: `Loaded ${repoState.getOpenFileCount()} files`,
        type: 'info',
        duration: 2000,
      });

      expect(useRepoStore.getState().repositories).toHaveLength(1);
      expect(useRepoStore.getState().openFiles).toHaveLength(1);
      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useStatsStore.getState().totalTokens).toBe(1000);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });

    it('should maintain consistency across store updates', () => {
      // Create initial state
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Test');

      const contextState = useContextStore.getState();
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      const statsState = useStatsStore.getState();
      statsState.recordUsage({
        tokensUsed: 500,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      // Verify consistency
      expect(useContextStore.getState().getTokenUsage()).toBe(500);
      expect(useStatsStore.getState().totalTokens).toBe(500);

      // Update context
      contextState.removeFile('file-1');

      // Verify consistency maintained
      expect(useContextStore.getState().getTokenUsage()).toBe(0);
      expect(useStatsStore.getState().totalTokens).toBe(500); // Stats unchanged
    });
  });

  describe('Store Independence', () => {
    it('should isolate chat state from config', () => {
      const chatState = useChatStore.getState();
      chatState.createConversation('Chat 1');
      chatState.createConversation('Chat 2');

      const configState = useConfigStore.getState();
      configState.addProvider({
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      });

      expect(useChatStore.getState().conversations).toHaveLength(2);
      expect(useConfigStore.getState().providers).toHaveLength(1);
    });

    it('should isolate memory operations from repo operations', () => {
      const memoryState = useMemoryStore.getState();
      memoryState.addMemory({
        key: 'test',
        value: 'data',
        category: 'user',
      });

      const repoState = useRepoStore.getState();
      repoState.addRepository({
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      });

      expect(useMemoryStore.getState().memories).toHaveLength(1);
      expect(useRepoStore.getState().repositories).toHaveLength(1);
    });
  });
});
