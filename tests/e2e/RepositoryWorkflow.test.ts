import { describe, it, expect, beforeEach } from 'vitest';
import { useRepoStore, FileNode, Repository } from '../../src/stores/repoStore';
import { useContextStore } from '../../src/stores/contextStore';
import { useMemoryStore } from '../../src/stores/memoryStore';
import { useStatsStore } from '../../src/stores/statsStore';
import { useUIStore } from '../../src/stores/uiStore';

describe('Repository Workflow E2E Tests', () => {
  beforeEach(() => {
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

  describe('Repository Setup Workflow', () => {
    it('should setup and configure repository', () => {
      const repoState = useRepoStore.getState();
      const uiState = useUIStore.getState();

      // Add repository
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      repoState.addRepository(repo);
      expect(useRepoStore.getState().currentRepoId).toBe('repo-1');

      // Setup file tree
      const fileTree: FileNode[] = [
        {
          id: 'src',
          name: 'src',
          path: '/src',
          type: 'folder',
          isOpen: true,
          children: [
            {
              id: 'stores',
              name: 'stores',
              path: '/src/stores',
              type: 'folder',
              isOpen: false,
              children: [
                {
                  id: 'chatStore',
                  name: 'chatStore.ts',
                  path: '/src/stores/chatStore.ts',
                  type: 'file',
                  language: 'typescript',
                  size: 4525,
                },
              ],
            },
            {
              id: 'components',
              name: 'components',
              path: '/src/components',
              type: 'folder',
              isOpen: false,
            },
          ],
        },
        {
          id: 'tests',
          name: 'tests',
          path: '/tests',
          type: 'folder',
          isOpen: false,
        },
      ];

      repoState.setFileTree(fileTree);

      // Show notification
      uiState.addToast({
        message: 'Repository loaded successfully',
        type: 'success',
        duration: 3000,
      });

      expect(useRepoStore.getState().fileTree).toHaveLength(2);
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });
  });

  describe('File Navigation Workflow', () => {
    it('should navigate and open files in repository', () => {
      const repoState = useRepoStore.getState();

      // Setup repo with files
      const repo: Repository = {
        id: 'repo-1',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      };

      repoState.addRepository(repo);

      const fileTree: FileNode[] = [
        {
          id: 'src',
          name: 'src',
          path: '/src',
          type: 'folder',
          children: [
            {
              id: 'main-ts',
              name: 'main.ts',
              path: '/src/main.ts',
              type: 'file',
              language: 'typescript',
            },
            {
              id: 'utils-ts',
              name: 'utils.ts',
              path: '/src/utils.ts',
              type: 'file',
              language: 'typescript',
            },
          ],
        },
      ];

      repoState.setFileTree(fileTree);

      // Open first file
      repoState.openFile('main-ts');
      expect(useRepoStore.getState().selectedFileId).toBe('main-ts');
      expect(useRepoStore.getState().openFiles).toContain('main-ts');

      // Open second file
      repoState.openFile('utils-ts');
      expect(useRepoStore.getState().selectedFileId).toBe('utils-ts');
      expect(useRepoStore.getState().openFiles).toHaveLength(2);

      // Close first file
      repoState.closeFile('main-ts');
      expect(useRepoStore.getState().openFiles).toHaveLength(1);
      expect(useRepoStore.getState().selectedFileId).toBe('utils-ts');
    });
  });

  describe('File Search and Filter Workflow', () => {
    it('should search and filter files in repository', () => {
      const repoState = useRepoStore.getState();

      const fileTree: FileNode[] = [
        {
          id: 'src',
          name: 'src',
          path: '/src',
          type: 'folder',
          children: [
            {
              id: 'api-service',
              name: 'api.service.ts',
              path: '/src/api.service.ts',
              type: 'file',
              language: 'typescript',
            },
            {
              id: 'api-types',
              name: 'api.types.ts',
              path: '/src/api.types.ts',
              type: 'file',
              language: 'typescript',
            },
            {
              id: 'chat-component',
              name: 'Chat.component.tsx',
              path: '/src/Chat.component.tsx',
              type: 'file',
              language: 'typescript',
            },
          ],
        },
      ];

      repoState.setFileTree(fileTree);

      // Search for API files
      repoState.setSearchQuery('api');
      expect(useRepoStore.getState().searchQuery).toBe('api');
      expect(useRepoStore.getState().filteredFiles.length).toBeGreaterThan(0);

      // Search for Chat
      repoState.setSearchQuery('chat');
      expect(useRepoStore.getState().searchQuery).toBe('chat');

      // Clear search
      repoState.setSearchQuery('');
      expect(useRepoStore.getState().filteredFiles).toEqual([]);
    });
  });

  describe('File Context Integration Workflow', () => {
    it('should add repository files to context for analysis', () => {
      const repoState = useRepoStore.getState();
      const contextState = useContextStore.getState();
      const statsState = useStatsStore.getState();

      // Setup repository
      repoState.addRepository({
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      });

      const fileTree: FileNode[] = [
        {
          id: 'chatStore',
          name: 'chatStore.ts',
          path: '/src/stores/chatStore.ts',
          type: 'file',
          language: 'typescript',
          size: 4525,
        },
        {
          id: 'configStore',
          name: 'configStore.ts',
          path: '/src/stores/configStore.ts',
          type: 'file',
          language: 'typescript',
          size: 4912,
        },
      ];

      repoState.setFileTree(fileTree);
      repoState.openFile('chatStore');
      repoState.openFile('configStore');

      // Add files to context for analysis
      contextState.addFile({
        id: 'chatStore',
        path: '/src/stores/chatStore.ts',
        name: 'chatStore.ts',
        tokens: 500,
        language: 'typescript',
      });

      contextState.addFile({
        id: 'configStore',
        path: '/src/stores/configStore.ts',
        name: 'configStore.ts',
        tokens: 450,
        language: 'typescript',
      });

      // Record analysis operation
      statsState.recordUsage({
        tokensUsed: 950,
        messagesCount: 0,
        modelUsed: 'analysis-engine',
        cost: 0,
      });

      expect(useRepoStore.getState().openFiles).toHaveLength(2);
      expect(useContextStore.getState().totalTokens).toBe(950);
      expect(useStatsStore.getState().totalTokens).toBe(950);
    });
  });

  describe('Multi-Repository Workflow', () => {
    it('should manage multiple repositories and switch between them', () => {
      const repoState = useRepoStore.getState();

      // Add first repository
      const repo1: Repository = {
        id: 'devforge',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      repoState.addRepository(repo1);
      expect(useRepoStore.getState().currentRepoId).toBe('devforge');

      // Setup files for repo1
      const repo1Files: FileNode[] = [
        {
          id: 'main-1',
          name: 'main.ts',
          path: '/main.ts',
          type: 'file',
          language: 'typescript',
        },
      ];
      repoState.setFileTree(repo1Files);
      repoState.openFile('main-1');

      // Add second repository
      const repo2: Repository = {
        id: 'project',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'develop',
      };

      repoState.addRepository(repo2);

      // Setup files for repo2
      const repo2Files: FileNode[] = [
        {
          id: 'app-2',
          name: 'app.tsx',
          path: '/app.tsx',
          type: 'file',
          language: 'typescript',
        },
      ];

      repoState.setCurrentRepository('project');
      repoState.setFileTree(repo2Files);
      repoState.openFile('app-2');

      // Verify both repos exist
      expect(useRepoStore.getState().repositories).toHaveLength(2);
      expect(useRepoStore.getState().currentRepoId).toBe('project');
      expect(useRepoStore.getState().openFiles).toHaveLength(1);
      expect(useRepoStore.getState().openFiles[0]).toBe('app-2');

      // Switch back
      repoState.setCurrentRepository('devforge');
      expect(useRepoStore.getState().currentRepoId).toBe('devforge');
    });
  });

  describe('File Tree Navigation Workflow', () => {
    it('should expand and collapse folders in file tree', () => {
      const repoState = useRepoStore.getState();

      const fileTree: FileNode[] = [
        {
          id: 'src',
          name: 'src',
          path: '/src',
          type: 'folder',
          isOpen: false,
          children: [
            {
              id: 'stores',
              name: 'stores',
              path: '/src/stores',
              type: 'folder',
              isOpen: false,
              children: [
                {
                  id: 'chatStore',
                  name: 'chatStore.ts',
                  path: '/src/stores/chatStore.ts',
                  type: 'file',
                },
              ],
            },
          ],
        },
      ];

      repoState.setFileTree(fileTree);

      // Expand src folder
      repoState.toggleFolder('src');
      expect(useRepoStore.getState().fileTree[0].isOpen).toBe(true);

      // Expand stores folder
      repoState.toggleFolder('stores');
      const storesFolder = useRepoStore.getState().fileTree[0].children?.[0];
      expect(storesFolder?.isOpen).toBe(true);

      // Get nested file
      const file = repoState.getFile('chatStore');
      expect(file?.name).toBe('chatStore.ts');

      // Collapse stores
      repoState.toggleFolder('stores');
      expect(useRepoStore.getState().fileTree[0].children?.[0].isOpen).toBe(false);
    });
  });

  describe('Repository Memory Workflow', () => {
    it('should store repository exploration in memory', () => {
      const repoState = useRepoStore.getState();
      const memoryState = useMemoryStore.getState();

      // Setup repository
      const repo: Repository = {
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      };

      repoState.addRepository(repo);

      // Explore repository
      repoState.setFileTree([
        {
          id: 'stores',
          name: 'stores',
          path: '/src/stores',
          type: 'folder',
          children: [
            {
              id: 'chatStore',
              name: 'chatStore.ts',
              path: '/src/stores/chatStore.ts',
              type: 'file',
            },
          ],
        },
      ]);

      repoState.openFile('chatStore');

      // Save exploration to memory
      memoryState.addMemory({
        key: 'repo_structure',
        value: {
          name: 'DevForge',
          structure: ['src/stores', 'src/components', 'tests'],
        },
        category: 'project',
      });

      memoryState.addToRecentContext(`Explored: ${repo.name}`);
      memoryState.addToRecentContext(`Opened: /src/stores/chatStore.ts`);

      expect(useMemoryStore.getState().memories).toHaveLength(1);
      expect(useMemoryStore.getState().recentContext).toHaveLength(2);
    });
  });

  describe('File Analysis Workflow', () => {
    it('should analyze multiple files from repository', () => {
      const repoState = useRepoStore.getState();
      const contextState = useContextStore.getState();
      const memoryState = useMemoryStore.getState();

      // Setup repository
      repoState.addRepository({
        id: 'repo-1',
        name: 'Project',
        owner: 'user',
        url: 'https://github.com/user/project',
        branch: 'main',
      });

      const fileTree: FileNode[] = [
        {
          id: 'chatStore',
          name: 'chatStore.ts',
          path: '/src/stores/chatStore.ts',
          type: 'file',
          language: 'typescript',
        },
        {
          id: 'configStore',
          name: 'configStore.ts',
          path: '/src/stores/configStore.ts',
          type: 'file',
          language: 'typescript',
        },
        {
          id: 'ChatComponent',
          name: 'Chat.tsx',
          path: '/src/components/Chat.tsx',
          type: 'file',
          language: 'typescript',
        },
      ];

      repoState.setFileTree(fileTree);

      // Open files for analysis
      repoState.openFile('chatStore');
      repoState.openFile('configStore');
      repoState.openFile('ChatComponent');

      // Add to context for comprehensive analysis
      contextState.addFile({
        id: 'chatStore',
        path: '/src/stores/chatStore.ts',
        name: 'chatStore.ts',
        tokens: 500,
        language: 'typescript',
      });

      contextState.addFile({
        id: 'configStore',
        path: '/src/stores/configStore.ts',
        name: 'configStore.ts',
        tokens: 450,
        language: 'typescript',
      });

      contextState.addFile({
        id: 'ChatComponent',
        path: '/src/components/Chat.tsx',
        name: 'Chat.tsx',
        tokens: 600,
        language: 'typescript',
      });

      // Record analysis findings
      memoryState.addMemory({
        key: 'architecture_analysis',
        value: {
          stores: ['chat', 'config'],
          components: ['Chat'],
          issues: [],
        },
        category: 'project',
      });

      expect(useRepoStore.getState().openFiles).toHaveLength(3);
      expect(useContextStore.getState().totalTokens).toBe(1550);
      expect(useMemoryStore.getState().memories).toHaveLength(1);
    });
  });

  describe('Repository and Context Synchronization', () => {
    it('should keep repository and context in sync', () => {
      const repoState = useRepoStore.getState();
      const contextState = useContextStore.getState();

      // Add repository
      repoState.addRepository({
        id: 'repo-1',
        name: 'DevForge',
        owner: 'user',
        url: 'https://github.com/user/devforge',
        branch: 'main',
      });

      const fileTree: FileNode[] = [
        {
          id: 'file-1',
          name: 'file1.ts',
          path: '/file1.ts',
          type: 'file',
          language: 'typescript',
        },
        {
          id: 'file-2',
          name: 'file2.ts',
          path: '/file2.ts',
          type: 'file',
          language: 'typescript',
        },
      ];

      repoState.setFileTree(fileTree);
      repoState.openFile('file-1');

      // Add same file to context
      contextState.addFile({
        id: 'file-1',
        path: '/file1.ts',
        name: 'file1.ts',
        tokens: 500,
        language: 'typescript',
      });

      // Verify sync
      expect(repoState.openFiles).toContain('file-1');
      expect(contextState.files).toHaveLength(1);
      expect(contextState.files[0].id).toBe('file-1');

      // Add second file to context
      contextState.addFile({
        id: 'file-2',
        path: '/file2.ts',
        name: 'file2.ts',
        tokens: 400,
        language: 'typescript',
      });

      repoState.openFile('file-2');

      // Verify both in sync
      expect(repoState.openFiles).toHaveLength(2);
      expect(contextState.files).toHaveLength(2);
    });
  });
});
