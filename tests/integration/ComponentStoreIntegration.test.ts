import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useChatStore } from '../../src/stores/chatStore';
import { useUIStore } from '../../src/stores/uiStore';
import { useRepoStore } from '../../src/stores/repoStore';
import { useContextStore } from '../../src/stores/contextStore';

describe('Component + Store Integration Tests', () => {
  beforeEach(() => {
    // Reset stores
    useChatStore.setState({
      conversations: [],
      currentConversationId: null,
      isLoading: false,
      currentInput: '',
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

    useRepoStore.setState({
      repositories: [],
      currentRepoId: null,
      fileTree: [],
      selectedFileId: null,
      openFiles: [],
      searchQuery: '',
      filteredFiles: [],
    });

    useContextStore.setState({
      files: [],
      totalTokens: 0,
      maxTokens: 8000,
      references: [],
      createdAt: new Date(),
      lastUpdated: new Date(),
    });
  });

  describe('Chat Component Integration', () => {
    it('should coordinate chat input component with store', () => {
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Chat');

      // Simulate input component behavior
      const inputValue = 'Hello, AI';
      chatState.setCurrentInput(inputValue);

      expect(useChatStore.getState().currentInput).toBe(inputValue);

      // Submit (clear input)
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: inputValue,
        tokens: 5,
        timestamp: new Date(),
      });
      chatState.setCurrentInput('');

      expect(useChatStore.getState().currentInput).toBe('');
      expect(useChatStore.getState().getConversationMessages(convId)).toHaveLength(1);
    });

    it('should show loading state during message processing', () => {
      const chatState = useChatStore.getState();
      const uiState = useUIStore.getState();

      chatState.createConversation('Loading Test');

      // Start processing
      chatState.setLoading(true);
      uiState.addToast({
        message: 'Processing your message...',
        type: 'info',
        duration: 0,
      });

      expect(useChatStore.getState().isLoading).toBe(true);
      expect(useUIStore.getState().toasts).toHaveLength(1);

      // Finish processing
      chatState.setLoading(false);
      uiState.removeToast(useUIStore.getState().toasts[0].id);

      expect(useChatStore.getState().isLoading).toBe(false);
      expect(useUIStore.getState().toasts).toHaveLength(0);
    });

    it('should handle chat window message display', () => {
      const chatState = useChatStore.getState();
      const convId = chatState.createConversation('Messages');

      // Add multiple messages (like ChatWindow rendering)
      const messages = [
        { id: 'msg-1', role: 'user' as const, content: 'Hi', tokens: 1, timestamp: new Date() },
        { id: 'msg-2', role: 'assistant' as const, content: 'Hello!', tokens: 2, timestamp: new Date() },
        { id: 'msg-3', role: 'user' as const, content: 'How are you?', tokens: 3, timestamp: new Date() },
      ];

      messages.forEach((msg) => chatState.addMessage(convId, msg));

      const displayMessages = chatState.getConversationMessages(convId);
      expect(displayMessages).toHaveLength(3);
      expect(displayMessages[0].role).toBe('user');
      expect(displayMessages[1].role).toBe('assistant');
    });

    it('should handle conversation list with UI state', () => {
      const chatState = useChatStore.getState();
      const uiState = useUIStore.getState();

      // Create multiple conversations (for ConversationList component)
      const conv1 = chatState.createConversation('Discussion');
      const conv2 = chatState.createConversation('Bug Report');
      const conv3 = chatState.createConversation('Feature Request');

      // Simulate selection with UI feedback
      chatState.setCurrentConversation(conv2);
      uiState.addToast({
        message: 'Switched to Bug Report',
        type: 'info',
        duration: 2000,
      });

      expect(useChatStore.getState().currentConversationId).toBe(conv2);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });
  });

  describe('Repository Browser Component Integration', () => {
    it('should coordinate file tree component with repo store', () => {
      const repoState = useRepoStore.getState();

      repoState.addRepository({
        id: 'repo-1',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      });

      const fileTree = [
        {
          id: 'src',
          name: 'src',
          path: '/src',
          type: 'folder' as const,
          isOpen: false,
          children: [
            {
              id: 'main',
              name: 'main.ts',
              path: '/src/main.ts',
              type: 'file' as const,
            },
          ],
        },
      ];

      repoState.setFileTree(fileTree);

      // Simulate folder toggle
      repoState.toggleFolder('src');
      expect(useRepoStore.getState().fileTree[0].isOpen).toBe(true);

      // Simulate file selection
      repoState.selectFile('main');
      expect(useRepoStore.getState().selectedFileId).toBe('main');
    });

    it('should handle file open/close tab behavior', () => {
      const repoState = useRepoStore.getState();

      repoState.setFileTree([
        { id: 'f1', name: 'file1.ts', path: '/f1.ts', type: 'file' as const },
        { id: 'f2', name: 'file2.ts', path: '/f2.ts', type: 'file' as const },
        { id: 'f3', name: 'file3.ts', path: '/f3.ts', type: 'file' as const },
      ]);

      // Open tabs (like tab component)
      repoState.openFile('f1');
      repoState.openFile('f2');
      repoState.openFile('f3');

      expect(useRepoStore.getState().openFiles).toHaveLength(3);
      expect(useRepoStore.getState().getOpenFileCount()).toBe(3);

      // Close middle tab
      repoState.closeFile('f2');
      expect(useRepoStore.getState().openFiles).toHaveLength(2);
      expect(useRepoStore.getState().openFiles).not.toContain('f2');

      // Close active tab
      repoState.closeFile('f3');
      expect(useRepoStore.getState().selectedFileId).toBeNull();
    });

    it('should coordinate search component with repo store', () => {
      const repoState = useRepoStore.getState();

      repoState.setFileTree([
        { id: 'api', name: 'api.ts', path: '/api.ts', type: 'file' as const },
        { id: 'api-types', name: 'api.types.ts', path: '/api.types.ts', type: 'file' as const },
        { id: 'utils', name: 'utils.ts', path: '/utils.ts', type: 'file' as const },
      ]);

      // Search (like SearchBox component)
      repoState.setSearchQuery('api');
      expect(useRepoStore.getState().searchQuery).toBe('api');
      expect(useRepoStore.getState().filteredFiles.length).toBeGreaterThan(0);

      // Clear search
      repoState.setSearchQuery('');
      expect(useRepoStore.getState().filteredFiles).toEqual([]);
    });
  });

  describe('Context Panel Component Integration', () => {
    it('should manage context file display with UI panel state', () => {
      const contextState = useContextStore.getState();
      const uiState = useUIStore.getState();

      // Add files to context (like ContextDisplay component)
      contextState.addFile({
        id: 'file-1',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      contextState.addFile({
        id: 'file-2',
        path: '/src/utils.ts',
        name: 'utils.ts',
        tokens: 300,
        language: 'typescript',
      });

      // Toggle context panel visibility
      expect(useUIStore.getState().showContextPanel).toBe(true);
      uiState.setContextPanel(false);
      expect(useUIStore.getState().showContextPanel).toBe(false);

      // Verify context still there even if hidden
      expect(useContextStore.getState().files).toHaveLength(2);
      expect(useContextStore.getState().getTokenUsage()).toBe(800);
    });

    it('should display context info with token usage', () => {
      const contextState = useContextStore.getState();

      // Add files (like ContextInfo component would show)
      contextState.addFile({
        id: 'f1',
        path: '/f1.ts',
        name: 'f1.ts',
        tokens: 1000,
        language: 'typescript',
      });

      contextState.addFile({
        id: 'f2',
        path: '/f2.ts',
        name: 'f2.ts',
        tokens: 2000,
        language: 'typescript',
      });

      // ContextInfo would display these
      const contextSize = contextState.getContextSize();
      const tokenUsage = contextState.getTokenUsage();
      const tokenPercentage = contextState.getTokenPercentage();
      const availableTokens = contextState.getAvailableTokens();

      expect(contextSize).toBe(2);
      expect(tokenUsage).toBe(3000);
      expect(tokenPercentage).toBe(37.5); // 3000 / 8000 * 100
      expect(availableTokens).toBe(5000);
    });
  });

  describe('Settings/Config Modal Integration', () => {
    it('should coordinate settings modal with UI state', () => {
      const uiState = useUIStore.getState();

      // Open settings (like SettingsModal)
      expect(useUIStore.getState().showSettingsModal).toBe(false);
      uiState.setSettingsModal(true);
      expect(useUIStore.getState().showSettingsModal).toBe(true);

      // Close settings
      uiState.setSettingsModal(false);
      expect(useUIStore.getState().showSettingsModal).toBe(false);
    });

    it('should handle theme toggle in settings', () => {
      const uiState = useUIStore.getState();

      expect(useUIStore.getState().theme).toBe('dark');

      uiState.setTheme('light');
      expect(useUIStore.getState().theme).toBe('light');

      uiState.setTheme('dark');
      expect(useUIStore.getState().theme).toBe('dark');
    });
  });

  describe('Toast/Notification Integration', () => {
    it('should show success notification', () => {
      const uiState = useUIStore.getState();

      const toastId = uiState.addToast({
        message: 'Operation completed successfully',
        type: 'success',
        duration: 3000,
      });

      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().toasts[0].type).toBe('success');

      uiState.removeToast(toastId);
      expect(useUIStore.getState().toasts).toHaveLength(0);
    });

    it('should show error notification', () => {
      const uiState = useUIStore.getState();

      uiState.addToast({
        message: 'An error occurred',
        type: 'error',
        duration: 5000,
      });

      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().toasts[0].type).toBe('error');
    });

    it('should manage multiple toasts simultaneously', () => {
      const uiState = useUIStore.getState();

      const id1 = uiState.addToast({ message: 'First', type: 'info', duration: 0 });
      const id2 = uiState.addToast({ message: 'Second', type: 'success', duration: 0 });
      const id3 = uiState.addToast({ message: 'Third', type: 'error', duration: 0 });

      expect(useUIStore.getState().toasts).toHaveLength(3);

      uiState.removeToast(id2);
      expect(useUIStore.getState().toasts).toHaveLength(2);

      uiState.clearToasts();
      expect(useUIStore.getState().toasts).toHaveLength(0);
    });
  });

  describe('Dialog Component Integration', () => {
    it('should handle confirm dialog with store state', () => {
      const chatState = useChatStore.getState();
      const uiState = useUIStore.getState();

      // Create a conversation
      const convId = chatState.createConversation('To Delete');

      // Simulate confirm dialog (DeleteDialog component)
      const handleConfirm = vi.fn(() => {
        chatState.deleteConversation(convId);
        uiState.addToast({
          message: 'Conversation deleted',
          type: 'success',
          duration: 2000,
        });
      });

      // Trigger confirm
      handleConfirm();

      expect(chatState.deleteConversation).toBeDefined();
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });
  });

  describe('Sidebar/Layout Component Integration', () => {
    it('should toggle sidebar collapse state', () => {
      const uiState = useUIStore.getState();

      expect(useUIStore.getState().sidebarCollapsed).toBe(false);

      uiState.setSidebarCollapsed(true);
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);

      uiState.setSidebarCollapsed(false);
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    });

    it('should manage panel visibility independently', () => {
      const uiState = useUIStore.getState();

      uiState.setSidebarCollapsed(true);
      uiState.setContextPanel(false);

      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      expect(useUIStore.getState().showContextPanel).toBe(false);

      uiState.setSidebarCollapsed(false);
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
      expect(useUIStore.getState().showContextPanel).toBe(false); // Should remain false
    });
  });

  describe('Complex Multi-Component Workflow', () => {
    it('should coordinate multiple components in typical user flow', () => {
      const chatState = useChatStore.getState();
      const repoState = useRepoStore.getState();
      const contextState = useContextStore.getState();
      const uiState = useUIStore.getState();

      // 1. User opens a repository (RepoSelector)
      repoState.addRepository({
        id: 'repo-1',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      });

      repoState.setFileTree([
        {
          id: 'src',
          name: 'src',
          path: '/src',
          type: 'folder' as const,
          children: [
            {
              id: 'main',
              name: 'main.ts',
              path: '/src/main.ts',
              type: 'file' as const,
            },
          ],
        },
      ]);

      // 2. User opens a file (FileTreeNode, tabs)
      repoState.openFile('main');
      expect(useRepoStore.getState().openFiles).toContain('main');

      // 3. User adds file to context (ContextDisplay)
      contextState.addFile({
        id: 'main',
        path: '/src/main.ts',
        name: 'main.ts',
        tokens: 500,
        language: 'typescript',
      });

      // 4. User starts chat (ChatWindow, InputBox)
      const convId = chatState.createConversation('Code Review');
      chatState.setCurrentInput('Review this file');
      chatState.addMessage(convId, {
        id: 'msg-1',
        role: 'user',
        content: 'Review this file',
        tokens: 10,
        timestamp: new Date(),
      });
      chatState.setCurrentInput('');

      // 5. AI responds (ChatWindow)
      chatState.setLoading(true);
      chatState.addMessage(convId, {
        id: 'msg-2',
        role: 'assistant',
        content: 'Code looks good. Consider adding error handling.',
        tokens: 20,
        timestamp: new Date(),
      });
      chatState.setLoading(false);

      // 6. Show notification (Toast)
      uiState.addToast({
        message: 'Analysis complete',
        type: 'success',
        duration: 3000,
      });

      // Verify complete state
      expect(useRepoStore.getState().repositories).toHaveLength(1);
      expect(useRepoStore.getState().openFiles).toHaveLength(1);
      expect(useContextStore.getState().files).toHaveLength(1);
      expect(useChatStore.getState().conversations).toHaveLength(1);
      expect(useChatStore.getState().getConversationMessages(convId)).toHaveLength(2);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });
  });
});
