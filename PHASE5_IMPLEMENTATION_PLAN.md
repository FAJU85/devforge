# Phase 5: Frontend Modularization Implementation Plan

**Project:** DevForge  
**Current State:** Monolithic HTML (3305 lines) with 2000+ lines inline JavaScript  
**Goal:** Modular component architecture with esbuild, Zustand state management, and Playwright E2E testing  
**Timeline:** 6-8 weeks

---

## Executive Summary

Phase 5 transforms the DevForge frontend from a single-file monolithic application into a modular, maintainable system. The strategy prioritizes **components first**, establishing a solid component library before introducing state management and API integration.

**Key Principles:**
- Components are decoupled from state until necessary
- State management via Zustand stores (one store per domain)
- API client agnostic until integration phase
- Every component has E2E tests from creation
- Build tooling with esbuild (fast, minimal config)

---

## Project Structure

### Directory Layout

```
/home/user/devforge/
├── package.json                          # Updated with build scripts
├── esbuild.config.js                     # Build configuration
├── playwright.config.ts                  # E2E test configuration (existing)
├── tsconfig.json                         # New: TypeScript config
├── .prettierrc                           # New: Code formatting
│
├── src/                                  # New: Application source
│   ├── index.html                        # Main entry point
│   ├── index.ts                          # App initialization
│   ├── styles/
│   │   ├── global.css                   # Theme variables & resets
│   │   ├── components.css               # Component styles
│   │   └── layout.css                   # Layout/grid styles
│   │
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.ts              # Sidebar container
│   │   │   ├── MainPanel.ts            # Main content area
│   │   │   ├── SettingsPanel.ts        # Settings modal
│   │   │   └── CommandPalette.ts       # Command palette
│   │   │
│   │   ├── ChatInterface/
│   │   │   ├── ChatWindow.ts           # Chat messages list
│   │   │   ├── ChatMessage.ts          # Single message (user/assistant)
│   │   │   ├── MessageActions.ts       # Copy/delete/edit buttons
│   │   │   ├── InputBox.ts             # Textarea with autoexpand
│   │   │   ├── TabBar.ts               # Chat tabs
│   │   │   └── __tests__/              # Playwright tests
│   │   │       ├── ChatWindow.spec.ts
│   │   │       ├── ChatMessage.spec.ts
│   │   │       └── InputBox.spec.ts
│   │   │
│   │   ├── RepoPanel/
│   │   │   ├── RepoSelector.ts         # GitHub repo picker
│   │   │   ├── RepoTree.ts             # File tree with expand/collapse
│   │   │   ├── FileTreeNode.ts         # Recursive tree item
│   │   │   ├── SearchBox.ts            # Tree search
│   │   │   └── __tests__/
│   │   │       ├── RepoSelector.spec.ts
│   │   │       ├── RepoTree.spec.ts
│   │   │       └── SearchBox.spec.ts
│   │   │
│   │   ├── ConfigPanel/
│   │   │   ├── ProviderSelector.ts     # Anthropic/HF/Groq picker
│   │   │   ├── ModelSelector.ts        # Model dropdown
│   │   │   ├── ApiKeyInput.ts          # Masked token inputs
│   │   │   ├── SettingsForm.ts         # Theme, memory, etc.
│   │   │   └── __tests__/
│   │   │       └── ProviderSelector.spec.ts
│   │   │
│   │   ├── ToolsPanel/
│   │   │   ├── FeatureFlagsSection.ts  # Flags UI
│   │   │   ├── HFBuildStatus.ts        # HF build widget
│   │   │   ├── ModeSelector.ts         # Agent mode picker
│   │   │   ├── ToolsList.ts            # Custom tools list
│   │   │   └── __tests__/
│   │   │       └── HFBuildStatus.spec.ts
│   │   │
│   │   ├── ContextPanel/
│   │   │   ├── ContextDisplay.ts       # Token counter + selected files
│   │   │   ├── FileList.ts             # Selected files list
│   │   │   ├── TokenMeter.ts           # Visual token counter
│   │   │   └── __tests__/
│   │   │       └── TokenMeter.spec.ts
│   │   │
│   │   ├── ModalWindow/
│   │   │   ├── Modal.ts                # Base modal wrapper
│   │   │   ├── DiffViewer.ts           # Diff display
│   │   │   ├── WritePanel.ts           # GitHub file write UI
│   │   │   ├── BatchPanel.ts           # Multi-file commit UI
│   │   │   ├── DepsAudit.ts            # Dependency audit modal
│   │   │   └── __tests__/
│   │   │       └── Modal.spec.ts
│   │   │
│   │   ├── common/
│   │   │   ├── Button.ts               # Base button component
│   │   │   ├── Input.ts                # Base input component
│   │   │   ├── Tooltip.ts              # Tooltip helper
│   │   │   ├── Toast.ts                # Toast notifications
│   │   │   ├── Dialog.ts               # Confirmation dialogs
│   │   │   └── __tests__/
│   │   │       ├── Toast.spec.ts
│   │   │       └── Dialog.spec.ts
│   │   │
│   │   └── index.ts                    # Component exports
│   │
│   ├── stores/                          # Zustand state management
│   │   ├── chatStore.ts                # Messages, tabs, history
│   │   ├── repoStore.ts                # GitHub repo, files, branches
│   │   ├── configStore.ts              # Provider, keys, settings
│   │   ├── toolsStore.ts               # Custom tools, flags
│   │   ├── uiStore.ts                  # Modal visibility, panels
│   │   ├── memoryStore.ts              # Memory/summary state
│   │   ├── statsStore.ts               # Token counts, metrics
│   │   ├── contextStore.ts             # Selected files, context
│   │   └── index.ts                    # Store exports
│   │
│   ├── api/                            # API client (phase will start in phase)
│   │   ├── client.ts                   # Base HTTP client
│   │   ├── github.ts                   # GitHub API endpoints
│   │   ├── repo.ts                     # Repo operations
│   │   ├── hf.ts                       # Hugging Face API
│   │   ├── config.ts                   # Config endpoint
│   │   └── types.ts                    # Shared API types
│   │
│   ├── utils/
│   │   ├── formatters.ts               # tokFmt, fmt, ficon, etc.
│   │   ├── storage.ts                  # localStorage helpers
│   │   ├── markdown.ts                 # marked + DOMPurify wrapper
│   │   ├── dom.ts                      # DOM utilities (ar, gv, gc)
│   │   ├── validators.ts               # Input validation
│   │   └── constants.ts                # Magic strings, config
│   │
│   └── types/
│       ├── chat.ts                     # Message, Tab types
│       ├── repo.ts                     # Repo, File, Branch types
│       ├── config.ts                   # Provider, Settings types
│       └── api.ts                      # API response types
│
├── dist/                               # Esbuild output (git ignored)
│   ├── index.html                      # Built HTML
│   ├── bundle.js                       # Built JS
│   └── bundle.css                      # Built CSS
│
├── e2e/                                # Playwright E2E tests (existing dir)
│   ├── config.spec.ts                  # Config panel tests
│   ├── chat.spec.ts                    # Chat interface tests
│   ├── repo.spec.ts                    # Repo panel tests
│   ├── api.spec.ts                     # API endpoint tests (existing)
│   ├── workflow.spec.ts                # End-to-end workflows
│   └── fixtures/
│       ├── auth.ts                     # Auth helpers
│       └── mocks.ts                    # Mock data
│
└── static/                             # Old monolithic file (archived)
    └── index.html.bak                  # Backup of original
```

---

## Build Configuration

### package.json

```json
{
  "name": "devforge",
  "version": "1.0.0",
  "description": "AI code editor and GitHub assistant",
  "type": "module",
  "main": "dist/bundle.js",
  "scripts": {
    "dev": "esbuild src/index.ts --bundle --outdir=dist --sourcemap --watch",
    "build": "esbuild src/index.ts --bundle --outdir=dist --minify",
    "preview": "npx http-server dist -c-1 -p 3000",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:debug": "playwright test --debug",
    "lint": "eslint src --ext .ts,.tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit"
  },
  "devDependencies": {
    "@playwright/test": "^1.60.0",
    "@types/node": "^25.9.1",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "esbuild": "^0.20.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0",
    "typescript": "^5.3.0"
  },
  "dependencies": {
    "zustand": "^4.4.0"
  }
}
```

### esbuild.config.js

```javascript
import * as esbuild from 'esbuild';
import * as fs from 'fs';
import * as path from 'path';

const config = {
  entryPoints: ['src/index.ts'],
  bundle: true,
  outdir: 'dist',
  sourcemap: process.env.NODE_ENV !== 'production',
  minify: process.env.NODE_ENV === 'production',
  loader: {
    '.css': 'css',
    '.woff2': 'dataurl',
  },
  external: [],
  define: {
    'process.env.NODE_ENV': process.env.NODE_ENV === 'production' ? '"production"' : '"development"',
  },
};

if (process.argv.includes('--watch')) {
  const ctx = await esbuild.context(config);
  await ctx.watch();
  console.log('watching...');
} else {
  await esbuild.build(config);
  console.log('build complete');
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "resolveJsonModule": true,
    "moduleResolution": "bundler",
    "rootDir": "./src",
    "outDir": "./dist",
    "baseUrl": "./src",
    "paths": {
      "@components/*": ["components/*"],
      "@stores/*": ["stores/*"],
      "@api/*": ["api/*"],
      "@utils/*": ["utils/*"],
      "@types/*": ["types/*"]
    }
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules", "dist", "e2e"]
}
```

---

## Component Extraction Strategy

### Phase 1: Layout & Common (Week 1)

**Scope:** Foundation components - no state, pure UI  
**Extraction Order:**

1. **common/Button.ts** → Extract all button patterns
   - Plain button, primary, secondary, danger variants
   - Icon + text combos
   - Disabled state handling
   - Source lines: ~50

2. **common/Input.ts** → Extract input patterns
   - Text input, textarea, password
   - Auto-expand textarea logic (ar function)
   - Source lines: ~40

3. **common/Toast.ts** → Extract notification system
   - toast() function refactored to class
   - CSS animations from global styles
   - Source lines: ~60

4. **common/Dialog.ts** → Extract confirmation dialogs
   - confirm() → reusable Dialog component
   - ESC/Enter handling
   - Source lines: ~80

5. **Layout/Sidebar.ts** → Extract sidebar structure
   - Collapsed/expanded state (UI only, no state management yet)
   - Tab switching logic (references CSS classes)
   - Source lines: ~100

6. **Layout/MainPanel.ts** → Main content wrapper
   - flex layout, responsive behavior
   - Panel switching
   - Source lines: ~50

**Tests per component:** 3-5 E2E tests per component (smoke tests)

---

### Phase 2: Chat Interface (Week 2-3)

**Scope:** Chat message rendering, no API calls yet  
**Dependencies:** Layout, Common components

**Extraction Order:**

1. **ChatInterface/ChatMessage.ts** → Single message renderer
   - User vs assistant styling
   - Markdown rendering (marked + DOMPurify)
   - Code block highlighting (hljs)
   - Source lines: ~80

2. **ChatInterface/MessageActions.ts** → Message action buttons
   - Copy button (cpMsg logic)
   - Delete button (delMsg logic)
   - Edit button (editMsg logic)
   - Source lines: ~60

3. **ChatInterface/InputBox.ts** → Chat input textarea
   - Auto-expand on type
   - @ file mention detection (_pickAt logic)
   - History navigation (up/down arrows)
   - Source lines: ~100

4. **ChatInterface/ChatWindow.ts** → Messages list container
   - Scroll to bottom on new message
   - Message filtering/search
   - Empty state
   - Source lines: ~80

5. **ChatInterface/TabBar.ts** → Chat tabs UI
   - Tab switching (switchTab logic)
   - Rename tab modal
   - New/close tab buttons
   - Source lines: ~90

6. **ContextPanel/TokenMeter.ts** → Token counter display
   - Visual meter (tokCls, tokFmt)
   - File list with token counts
   - Source lines: ~70

**Tests:** 8-10 tests per component

---

### Phase 3: Repo & Config Panels (Week 3-4)

**Scope:** UI for GitHub repo selection and configuration  
**Dependencies:** Layout, Common, Chat components

**Extraction Order:**

1. **RepoPanel/RepoSelector.ts** → GitHub repo picker
   - Search/filter (filterRepos logic)
   - List rendering (renderRepoList)
   - Connection status badge
   - Source lines: ~90

2. **RepoPanel/SearchBox.ts** → Tree search input
   - Debounced search (debounceSearch)
   - Real-time filtering
   - Clear button
   - Source lines: ~50

3. **RepoPanel/FileTreeNode.ts** → Recursive tree item
   - Expand/collapse toggle
   - File icon (ficon)
   - Selection checkbox
   - Folder vs file styling
   - Source lines: ~80

4. **RepoPanel/RepoTree.ts** → Full file tree container
   - Tree state (expanded folders)
   - Node rendering
   - Add to context button
   - Source lines: ~100

5. **ConfigPanel/ProviderSelector.ts** → Provider buttons
   - Anthropic/HF/Groq/OCI toggle
   - Active indicator
   - Provider group switching (setProvGroup)
   - Source lines: ~70

6. **ConfigPanel/ApiKeyInput.ts** → Token inputs
   - Masked display
   - Show/hide toggle
   - Clear button
   - Validation hints
   - Source lines: ~60

7. **ConfigPanel/ModelSelector.ts** → Model picker
   - Dropdown with search (fetchModels)
   - Current model badge
   - Custom model input
   - Source lines: ~80

8. **ConfigPanel/SettingsForm.ts** → Settings panel
   - Theme toggle
   - Memory mode select
   - Agent mode select
   - Preset saver
   - Source lines: ~120

**Tests:** 10-12 tests per component

---

### Phase 4: Tools & Special Panels (Week 4-5)

**Scope:** Tools panel, modals, utility panels  
**Dependencies:** All previous components

**Extraction Order:**

1. **ToolsPanel/FeatureFlagsSection.ts** → Flags UI
   - Flags list (loadFlags)
   - Toggle flag state (toggleFlag, saveFlag)
   - Add flag form
   - Source lines: ~100

2. **ToolsPanel/HFBuildStatus.ts** → HF build widget
   - Fetch live status (fetchLiveMetrics)
   - Status indicator animation
   - Refresh button
   - Source lines: ~60

3. **ToolsPanel/ModeSelector.ts** → Agent mode picker
   - Mode buttons (setAgent logic)
   - Streaming indicator
   - Source lines: ~40

4. **ToolsPanel/ToolsList.ts** → Custom tools manager
   - Tool CRUD (saveTool, deleteTool)
   - Tool list (renderToolList)
   - Source lines: ~110

5. **ModalWindow/Modal.ts** → Base modal wrapper
   - Overlay + content
   - Close button, ESC handling
   - z-index layering
   - Source lines: ~50

6. **ModalWindow/DiffViewer.ts** → Code diff display
   - renderDiff logic
   - Add/delete line styling
   - Copy diff button
   - Source lines: ~70

7. **ModalWindow/WritePanel.ts** → GitHub file write
   - Path/branch/message inputs
   - Code block display
   - Commit button (commitFile)
   - PR creation link
   - Source lines: ~140

8. **ModalWindow/BatchPanel.ts** → Batch commit UI
   - File list with checkboxes
   - Message input
   - Branch selector
   - Source lines: ~100

9. **ModalWindow/DepsAudit.ts** → Dependency audit modal
   - Audit results table
   - Copy to clipboard
   - Source lines: ~80

10. **Layout/CommandPalette.ts** → Command palette
    - Search/filter (filterCmdPalette)
    - Command list (renderCmdList)
    - Keyboard navigation
    - Source lines: ~120

11. **Layout/SettingsPanel.ts** → Settings modal
    - Tab navigation
    - Form sections
    - Save/reset buttons
    - Source lines: ~150

**Tests:** 8-10 tests per component

---

## Zustand State Management

### Architecture Principles

- **Store per domain:** chatStore, repoStore, configStore, etc.
- **No derived state:** Compute in selectors, not in setters
- **Actions are explicit:** No implicit mutations
- **Types first:** Every store has TypeScript interfaces
- **Testing:** Mock stores in component tests

### Store Definitions

#### `stores/chatStore.ts`

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  tokens?: number;
}

export interface ChatTab {
  id: string;
  name: string;
  messages: Message[];
  createdAt: number;
}

export interface ChatState {
  // State
  tabs: ChatTab[];
  activeTabId: string | null;
  messages: Message[]; // Convenience reference to active tab's messages
  promptHistory: string[];
  historyIndex: number;
  isStreaming: boolean;
  
  // Selectors
  getActiveTab: () => ChatTab | null;
  getTotalTokens: () => number;
  
  // Actions
  createTab: (name?: string) => string;
  switchTab: (tabId: string) => void;
  closeTab: (tabId: string) => void;
  renameTab: (tabId: string, name: string) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, content: string) => void;
  deleteMessage: (id: string) => void;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  
  // Prompt history
  addToHistory: (prompt: string) => void;
  navigateHistory: (direction: 'up' | 'down') => string | null;
  
  // Bulk operations
  loadFromStorage: (data: Partial<ChatState>) => void;
  exportChat: () => string;
}

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        tabs: [],
        activeTabId: null,
        messages: [],
        promptHistory: [],
        historyIndex: -1,
        isStreaming: false,

        getActiveTab: () => {
          const state = get();
          return state.tabs.find(t => t.id === state.activeTabId) || null;
        },

        getTotalTokens: () => {
          const state = get();
          return state.messages.reduce((sum, m) => sum + (m.tokens || 0), 0);
        },

        createTab: (name) => {
          const id = Math.random().toString(36).slice(2, 11);
          const tab: ChatTab = {
            id,
            name: name || `Chat ${Date.now()}`,
            messages: [],
            createdAt: Date.now(),
          };
          set(state => ({
            tabs: [...state.tabs, tab],
            activeTabId: id,
            messages: [],
          }));
          return id;
        },

        switchTab: (tabId) => {
          const state = get();
          const tab = state.tabs.find(t => t.id === tabId);
          if (tab) {
            set({ activeTabId: tabId, messages: tab.messages });
          }
        },

        closeTab: (tabId) => {
          set(state => {
            const remaining = state.tabs.filter(t => t.id !== tabId);
            let nextActiveId = state.activeTabId;
            if (nextActiveId === tabId) {
              nextActiveId = remaining[0]?.id || null;
            }
            return {
              tabs: remaining,
              activeTabId: nextActiveId,
              messages: remaining.find(t => t.id === nextActiveId)?.messages || [],
            };
          });
        },

        renameTab: (tabId, name) => {
          set(state => ({
            tabs: state.tabs.map(t =>
              t.id === tabId ? { ...t, name } : t
            ),
          }));
        },

        addMessage: (message) => {
          const id = Math.random().toString(36).slice(2, 11);
          const newMessage: Message = {
            ...message,
            id,
            timestamp: Date.now(),
          };
          set(state => {
            const updatedTabs = state.tabs.map(t =>
              t.id === state.activeTabId
                ? { ...t, messages: [...t.messages, newMessage] }
                : t
            );
            return {
              tabs: updatedTabs,
              messages: [...state.messages, newMessage],
            };
          });
        },

        updateMessage: (id, content) => {
          set(state => ({
            messages: state.messages.map(m =>
              m.id === id ? { ...m, content } : m
            ),
            tabs: state.tabs.map(t =>
              t.id === state.activeTabId
                ? {
                    ...t,
                    messages: t.messages.map(m =>
                      m.id === id ? { ...m, content } : m
                    ),
                  }
                : t
            ),
          }));
        },

        deleteMessage: (id) => {
          set(state => ({
            messages: state.messages.filter(m => m.id !== id),
            tabs: state.tabs.map(t =>
              t.id === state.activeTabId
                ? { ...t, messages: t.messages.filter(m => m.id !== id) }
                : t
            ),
          }));
        },

        clearMessages: () => {
          set(state => ({
            messages: [],
            tabs: state.tabs.map(t =>
              t.id === state.activeTabId ? { ...t, messages: [] } : t
            ),
          }));
        },

        setStreaming: (streaming) => {
          set({ isStreaming: streaming });
        },

        addToHistory: (prompt) => {
          if (!prompt.trim()) return;
          set(state => ({
            promptHistory: [prompt, ...state.promptHistory].slice(0, 50),
            historyIndex: -1,
          }));
        },

        navigateHistory: (direction) => {
          const state = get();
          if (direction === 'up') {
            const nextIdx = state.historyIndex + 1;
            if (nextIdx < state.promptHistory.length) {
              set({ historyIndex: nextIdx });
              return state.promptHistory[nextIdx];
            }
          } else {
            const nextIdx = state.historyIndex - 1;
            if (nextIdx >= 0) {
              set({ historyIndex: nextIdx });
              return state.promptHistory[nextIdx];
            } else if (nextIdx === -1) {
              set({ historyIndex: -1 });
              return '';
            }
          }
          return null;
        },

        loadFromStorage: (data) => {
          set(data);
        },

        exportChat: () => {
          const state = get();
          return JSON.stringify(state.messages, null, 2);
        },
      }),
      { name: 'devforge-chat' }
    )
  )
);
```

#### `stores/repoStore.ts`

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface FileInfo {
  path: string;
  size: number;
  type: 'file' | 'dir';
}

export interface Branch {
  name: string;
  commit: { sha: string };
  protected: boolean;
}

export interface RepoInfo {
  owner: string;
  repo: string;
  branch: string;
  files: FileInfo[];
  url: string;
}

export interface RepoState {
  // State
  repoInfo: RepoInfo | null;
  selectedFiles: Map<string, string>; // path -> content
  fileSizes: Map<string, number>;
  branches: Branch[];
  allRepos: any[]; // GitHub API response
  searchQuery: string;
  
  // Selectors
  getSelectedFileCount: () => number;
  getTotalSelectedSize: () => number;
  
  // Actions
  setRepoInfo: (info: RepoInfo) => void;
  clearRepo: () => void;
  toggleFile: (path: string, content: string) => void;
  addFile: (path: string, content: string) => void;
  removeFile: (path: string) => void;
  setFileSize: (path: string, size: number) => void;
  clearSelectedFiles: () => void;
  setSearchQuery: (query: string) => void;
  setBranches: (branches: Branch[]) => void;
  setAllRepos: (repos: any[]) => void;
}

export const useRepoStore = create<RepoState>()(
  devtools((set, get) => ({
    repoInfo: null,
    selectedFiles: new Map(),
    fileSizes: new Map(),
    branches: [],
    allRepos: [],
    searchQuery: '',

    getSelectedFileCount: () => get().selectedFiles.size,
    
    getTotalSelectedSize: () => {
      const sizes = get().fileSizes;
      let total = 0;
      get().selectedFiles.forEach((_, path) => {
        total += sizes.get(path) || 0;
      });
      return total;
    },

    setRepoInfo: (info) => {
      set({ repoInfo: info });
    },

    clearRepo: () => {
      set({
        repoInfo: null,
        selectedFiles: new Map(),
        fileSizes: new Map(),
        branches: [],
        searchQuery: '',
      });
    },

    toggleFile: (path, content) => {
      set(state => {
        const files = new Map(state.selectedFiles);
        if (files.has(path)) {
          files.delete(path);
        } else {
          if (files.size >= 8) return state; // Max 8 files
          files.set(path, content);
        }
        return { selectedFiles: files };
      });
    },

    addFile: (path, content) => {
      set(state => {
        const files = new Map(state.selectedFiles);
        if (files.size >= 8) return state;
        files.set(path, content);
        return { selectedFiles: files };
      });
    },

    removeFile: (path) => {
      set(state => {
        const files = new Map(state.selectedFiles);
        files.delete(path);
        return { selectedFiles: files };
      });
    },

    setFileSize: (path, size) => {
      set(state => {
        const sizes = new Map(state.fileSizes);
        sizes.set(path, size);
        return { fileSizes: sizes };
      });
    },

    clearSelectedFiles: () => {
      set({ selectedFiles: new Map(), fileSizes: new Map() });
    },

    setSearchQuery: (query) => {
      set({ searchQuery: query });
    },

    setBranches: (branches) => {
      set({ branches });
    },

    setAllRepos: (repos) => {
      set({ allRepos: repos });
    },
  }))
);
```

#### `stores/configStore.ts`

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export type Provider = 'anthropic' | 'hf' | 'groq' | 'oai-compat';

export interface ConfigState {
  // Provider
  provider: Provider;
  
  // API Keys
  anthropicKey: string;
  groqKey: string;
  hfToken: string;
  oaiCompatKey: string;
  oaiCompatBaseUrl: string;
  
  // Models
  anthropicModel: string;
  hfModel: string;
  groqModel: string;
  oaiCompatModel: string;
  
  // UI Settings
  theme: 'light' | 'dark';
  memoryMode: boolean;
  agentMode: 'code' | 'default';
  
  // GitHub
  githubToken: string;
  
  // Actions
  setProvider: (provider: Provider) => void;
  setAnthropicKey: (key: string) => void;
  setGroqKey: (key: string) => void;
  setHFToken: (token: string) => void;
  setOAICompat: (key: string, baseUrl: string, model: string) => void;
  setModel: (model: string) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setMemoryMode: (enabled: boolean) => void;
  setAgentMode: (mode: 'code' | 'default') => void;
  setGithubToken: (token: string) => void;
  clearKeys: () => void;
}

export const useConfigStore = create<ConfigState>()(
  devtools(
    persist(
      (set) => ({
        provider: 'anthropic',
        anthropicKey: '',
        groqKey: '',
        hfToken: '',
        oaiCompatKey: '',
        oaiCompatBaseUrl: '',
        anthropicModel: 'claude-sonnet-4-6',
        hfModel: 'Qwen/Qwen2.5-Coder-32B-Instruct',
        groqModel: '',
        oaiCompatModel: '',
        theme: 'dark',
        memoryMode: false,
        agentMode: 'code',
        githubToken: '',

        setProvider: (provider) => set({ provider }),
        setAnthropicKey: (key) => set({ anthropicKey: key }),
        setGroqKey: (key) => set({ groqKey: key }),
        setHFToken: (token) => set({ hfToken: token }),
        setOAICompat: (key, baseUrl, model) => {
          set({
            oaiCompatKey: key,
            oaiCompatBaseUrl: baseUrl,
            oaiCompatModel: model,
          });
        },
        setModel: (model) => set(state => {
          if (state.provider === 'anthropic') return { anthropicModel: model };
          if (state.provider === 'hf') return { hfModel: model };
          return state;
        }),
        setTheme: (theme) => set({ theme }),
        setMemoryMode: (enabled) => set({ memoryMode: enabled }),
        setAgentMode: (mode) => set({ agentMode: mode }),
        setGithubToken: (token) => set({ githubToken: token }),
        clearKeys: () => {
          set({
            anthropicKey: '',
            groqKey: '',
            hfToken: '',
            oaiCompatKey: '',
            githubToken: '',
          });
        },
      }),
      { name: 'devforge-config' }
    )
  )
);
```

#### `stores/uiStore.ts`

```typescript
import { create } from 'zustand';

export interface UIState {
  // Modal/panel visibility
  settingsOpen: boolean;
  commandPaletteOpen: boolean;
  diffModalOpen: boolean;
  writePanelOpen: boolean;
  batchPanelOpen: boolean;
  depsAuditOpen: boolean;
  
  // Active tabs/panels
  activeConfigTab: 'ai' | 'tools' | 'settings';
  activeSidebarTab: 'repo' | 'config' | 'tools';
  
  // Sidebar state
  sidebarCollapsed: boolean;
  leftPanelCollapsed: boolean;
  
  // Actions
  openSettings: () => void;
  closeSettings: () => void;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  toggleCommandPalette: () => void;
  openDiffModal: () => void;
  closeDiffModal: () => void;
  openWritePanel: () => void;
  closeWritePanel: () => void;
  openBatchPanel: () => void;
  closeBatchPanel: () => void;
  openDepsAudit: () => void;
  closeDepsAudit: () => void;
  setActiveConfigTab: (tab: 'ai' | 'tools' | 'settings') => void;
  setActiveSidebarTab: (tab: 'repo' | 'config' | 'tools') => void;
  toggleSidebar: () => void;
  toggleLeftPanel: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  settingsOpen: false,
  commandPaletteOpen: false,
  diffModalOpen: false,
  writePanelOpen: false,
  batchPanelOpen: false,
  depsAuditOpen: false,
  activeConfigTab: 'ai',
  activeSidebarTab: 'repo',
  sidebarCollapsed: false,
  leftPanelCollapsed: false,

  openSettings: () => set({ settingsOpen: true }),
  closeSettings: () => set({ settingsOpen: false }),
  openCommandPalette: () => set({ commandPaletteOpen: true }),
  closeCommandPalette: () => set({ commandPaletteOpen: false }),
  toggleCommandPalette: () =>
    set(state => ({ commandPaletteOpen: !state.commandPaletteOpen })),
  openDiffModal: () => set({ diffModalOpen: true }),
  closeDiffModal: () => set({ diffModalOpen: false }),
  openWritePanel: () => set({ writePanelOpen: true }),
  closeWritePanel: () => set({ writePanelOpen: false }),
  openBatchPanel: () => set({ batchPanelOpen: true }),
  closeBatchPanel: () => set({ batchPanelOpen: false }),
  openDepsAudit: () => set({ depsAuditOpen: true }),
  closeDepsAudit: () => set({ depsAuditOpen: false }),
  setActiveConfigTab: (tab) => set({ activeConfigTab: tab }),
  setActiveSidebarTab: (tab) => set({ activeSidebarTab: tab }),
  toggleSidebar: () =>
    set(state => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  toggleLeftPanel: () =>
    set(state => ({ leftPanelCollapsed: !state.leftPanelCollapsed })),
}));
```

#### `stores/toolsStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface CustomTool {
  id: string;
  name: string;
  description: string;
  schema: Record<string, any>; // JSON Schema
}

export interface FeatureFlag {
  key: string;
  enabled: boolean;
}

export interface ToolsState {
  // Custom tools
  tools: CustomTool[];
  
  // Feature flags
  flags: FeatureFlag[];
  
  // Actions
  addTool: (tool: CustomTool) => void;
  updateTool: (id: string, tool: Partial<CustomTool>) => void;
  deleteTool: (id: string) => void;
  setTools: (tools: CustomTool[]) => void;
  
  // Flags
  setFlags: (flags: FeatureFlag[]) => void;
  toggleFlag: (key: string) => void;
  getFlag: (key: string) => boolean;
}

export const useToolsStore = create<ToolsState>()(
  persist(
    (set, get) => ({
      tools: [],
      flags: [],

      addTool: (tool) => {
        set(state => ({
          tools: [...state.tools, tool],
        }));
      },

      updateTool: (id, updates) => {
        set(state => ({
          tools: state.tools.map(t =>
            t.id === id ? { ...t, ...updates } : t
          ),
        }));
      },

      deleteTool: (id) => {
        set(state => ({
          tools: state.tools.filter(t => t.id !== id),
        }));
      },

      setTools: (tools) => {
        set({ tools });
      },

      setFlags: (flags) => {
        set({ flags });
      },

      toggleFlag: (key) => {
        set(state => ({
          flags: state.flags.map(f =>
            f.key === key ? { ...f, enabled: !f.enabled } : f
          ),
        }));
      },

      getFlag: (key) => {
        const state = get();
        return state.flags.find(f => f.key === key)?.enabled || false;
      },
    }),
    { name: 'devforge-tools' }
  )
);
```

#### `stores/statsStore.ts`

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface StatsState {
  tokens: number;
  messages: number;
  startTime: number;
  
  addTokens: (count: number) => void;
  incrementMessages: () => void;
  reset: () => void;
  getSessionDuration: () => number;
}

export const useStatsStore = create<StatsState>()(
  devtools((set, get) => ({
    tokens: 0,
    messages: 0,
    startTime: Date.now(),

    addTokens: (count) => {
      set(state => ({
        tokens: state.tokens + count,
      }));
    },

    incrementMessages: () => {
      set(state => ({
        messages: state.messages + 1,
      }));
    },

    reset: () => {
      set({
        tokens: 0,
        messages: 0,
        startTime: Date.now(),
      });
    },

    getSessionDuration: () => {
      return Date.now() - get().startTime;
    },
  }))
);
```

### Store Organization (index.ts)

```typescript
export { useChatStore, type ChatState, type Message, type ChatTab } from './chatStore';
export { useRepoStore, type RepoState, type RepoInfo, type FileInfo, type Branch } from './repoStore';
export { useConfigStore, type ConfigState, type Provider } from './configStore';
export { useUIStore, type UIState } from './uiStore';
export { useToolsStore, type ToolsState, type CustomTool, type FeatureFlag } from './toolsStore';
export { useStatsStore, type StatsState } from './statsStore';
```

---

## API Client Integration (Phase in Week 5)

### Structure

```typescript
// api/client.ts
class HTTPClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
    this.headers = { 'Content-Type': 'application/json' };
  }

  async get<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      method: 'GET',
    });
    return this.handleResponse<T>(response);
  }

  async post<T>(path: string, data?: any, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      method: 'POST',
      headers: { ...this.headers, ...options?.headers },
      body: JSON.stringify(data),
    });
    return this.handleResponse<T>(response);
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  }
}

export const apiClient = new HTTPClient();
```

### Endpoint Modules

- **api/github.ts** → loadRepos, selectRepo, loadBranches, commitFile
- **api/repo.ts** → fetchFile, summarizeFile, buildTree, getDiff
- **api/hf.ts** → fetchModels, getBuildStatus, getLiveMetrics
- **api/config.ts** → getConfig, getFlagStatus, getTools

### Integration Strategy

1. Each API module exports async functions
2. Functions are called in event handlers (submit, click, etc.)
3. Results update Zustand stores
4. Components re-render via store subscriptions
5. Error handling via try/catch → toast notifications

---

## E2E Testing Strategy

### Test Organization

**File structure:**
```
e2e/
├── api.spec.ts              # API endpoint tests (existing)
├── chat.spec.ts             # Chat interface workflows
├── config.spec.ts           # Config panel interactions
├── repo.spec.ts             # Repo selection & tree
├── workflow.spec.ts         # End-to-end user flows
├── fixtures/
│   ├── auth.ts              # Auth/login helpers
│   └── mocks.ts             # Mock data
└── example.spec.ts          # Existing tests
```

### Test Examples

#### chat.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Chat Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('send message appears in chat', async ({ page }) => {
    const input = page.locator('#ti'); // text input
    await input.fill('Hello, world');
    await page.keyboard.press('Enter');
    
    const message = page.locator('.msg-body');
    await expect(message).toContainText('Hello, world');
  });

  test('message can be copied', async ({ page }) => {
    await page.locator('#ti').fill('Test message');
    await page.keyboard.press('Enter');
    
    const copyBtn = page.locator('button:has-text("copy")').first();
    await copyBtn.click();
    
    await expect(copyBtn).toContainText('✓');
  });

  test('message can be deleted', async ({ page }) => {
    await page.locator('#ti').fill('Deleteme');
    await page.keyboard.press('Enter');
    
    const delBtn = page.locator('button:has-text("×")').first();
    await delBtn.click();
    
    const message = page.locator('.msg-body');
    await expect(message).not.toContainText('Deleteme');
  });

  test('new tab creates separate chat', async ({ page }) => {
    const newTabBtn = page.locator('button:has-text("+ New")');
    await newTabBtn.click();
    
    const tabs = page.locator('.tab');
    expect(await tabs.count()).toBe(2);
  });

  test('tab switching preserves messages', async ({ page }) => {
    // Send message in tab 1
    await page.locator('#ti').fill('Tab 1 message');
    await page.keyboard.press('Enter');
    
    // Create new tab
    const newTabBtn = page.locator('button:has-text("+ New")');
    await newTabBtn.click();
    
    // Send different message in tab 2
    await page.locator('#ti').fill('Tab 2 message');
    await page.keyboard.press('Enter');
    
    // Switch back to tab 1
    const firstTab = page.locator('.tab').first();
    await firstTab.click();
    
    // Check message is still there
    const message = page.locator('.msg-body');
    await expect(message).toContainText('Tab 1 message');
  });
});
```

#### repo.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Repo Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Assume auth token is set via localStorage
    await page.evaluate(() => {
      localStorage.setItem('devforge-config', JSON.stringify({
        githubToken: process.env.GITHUB_TOKEN || 'test-token',
      }));
    });
  });

  test('repo list loads and is searchable', async ({ page }) => {
    const repoInput = page.locator('#repo-search');
    await repoInput.fill('devforge');
    
    const repoList = page.locator('#repo-list');
    const items = repoList.locator('.list-item');
    
    expect(await items.count()).toBeGreaterThan(0);
  });

  test('repo selection shows file tree', async ({ page }) => {
    // Select a repo
    const repoItem = page.locator('.list-item').first();
    await repoItem.click();
    
    // Wait for tree to load
    const tree = page.locator('#file-tree');
    await expect(tree).not.toContainText('Loading');
    
    // Check folders are visible
    const folders = page.locator('.tfolder');
    expect(await folders.count()).toBeGreaterThan(0);
  });

  test('file search filters tree', async ({ page }) => {
    // Select repo and wait for tree
    const repoItem = page.locator('.list-item').first();
    await repoItem.click();
    await page.waitForSelector('#file-tree .tfolder');
    
    // Search for file
    const searchInput = page.locator('#tree-search');
    await searchInput.fill('index.ts');
    
    // Check filtered results
    const files = page.locator('.tfile:not([style*="display: none"])');
    const fileNames = await files.allTextContents();
    fileNames.forEach(name => {
      expect(name.toLowerCase()).toContain('index');
    });
  });
});
```

#### config.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Config Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('provider selection updates UI', async ({ page }) => {
    await page.locator('#stab-config').click();
    
    // Click Hugging Face provider
    const hfBtn = page.locator('#provch-hf');
    await hfBtn.click();
    
    // Check model selector shows HF models
    const modelInput = page.locator('#model-input');
    expect(await modelInput.getAttribute('placeholder')).toContain('Hugging Face');
  });

  test('API key input is masked', async ({ page }) => {
    await page.locator('#stab-config').click();
    
    const keyInput = page.locator('#ak'); // anthropic key
    await keyInput.fill('sk-test123');
    
    // Check type is password
    expect(await keyInput.getAttribute('type')).toBe('password');
    
    // Click show button and verify visible
    const showBtn = page.locator('button:has-text("👁")').first();
    await showBtn.click();
    
    expect(await keyInput.getAttribute('type')).toBe('text');
  });

  test('theme toggle switches colors', async ({ page }) => {
    const htmlElement = page.locator('html');
    const initialTheme = await htmlElement.getAttribute('data-theme');
    
    const themeBtn = page.locator('button:has-text("🌙")');
    await themeBtn.click();
    
    const newTheme = await htmlElement.getAttribute('data-theme');
    expect(newTheme).not.toBe(initialTheme);
  });

  test('model search fetches options', async ({ page }) => {
    await page.locator('#stab-config').click();
    
    const modelSearch = page.locator('#model-search');
    await modelSearch.fill('gpt');
    
    // Wait for results to load
    const results = page.locator('#model-list .list-item');
    await expect(results.first()).toBeVisible();
    
    expect(await results.count()).toBeGreaterThan(0);
  });
});
```

#### workflow.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('End-to-End Workflows', () => {
  test('complete setup and query flow', async ({ page }) => {
    await page.goto('/');
    
    // Step 1: Set GitHub token
    await page.locator('#stab-config').click();
    const ghToken = page.locator('#ghtoken');
    await ghToken.fill(process.env.GITHUB_TOKEN || 'test-token');
    
    // Step 2: Select repo
    const repoSearch = page.locator('#repo-search');
    await repoSearch.fill('anthropics-org/anthropic-sdk-python');
    await page.locator('.list-item').first().click();
    
    // Wait for files to load
    await page.waitForSelector('#file-tree .tfile');
    
    // Step 3: Select a file
    const firstFile = page.locator('.tfile').first();
    await firstFile.click();
    
    // Step 4: Send query about the file
    const input = page.locator('#ti');
    await input.fill('Explain the main purpose of this file');
    await page.keyboard.press('Enter');
    
    // Wait for response
    const message = page.locator('.msg-body').last();
    await expect(message).not.toBeEmpty({ timeout: 30000 });
  });

  test('batch file commit workflow', async ({ page }) => {
    await page.goto('/');
    
    // Setup: Set GitHub token and select repo
    await page.locator('#stab-config').click();
    const ghToken = page.locator('#ghtoken');
    await ghToken.fill(process.env.GITHUB_TOKEN || 'test-token');
    
    const repoSearch = page.locator('#repo-search');
    await repoSearch.fill('test-repo');
    await page.locator('.list-item').first().click();
    
    // Open batch commit panel
    const batchBtn = page.locator('button:has-text("Batch")');
    await batchBtn.click();
    
    // Select files to commit
    const checkboxes = page.locator('.batch-panel input[type="checkbox"]');
    await checkboxes.first().check();
    
    // Enter commit message
    const msgInput = page.locator('.batch-panel .wp-msg');
    await msgInput.fill('Update documentation');
    
    // Commit
    const commitBtn = page.locator('.batch-panel button:has-text("Commit")');
    await commitBtn.click();
    
    // Check success toast
    const toast = page.locator('.toast');
    await expect(toast).toContainText('Committed');
  });
});
```

### Test Coverage Goals

| Category | Current | Target | Notes |
|----------|---------|--------|-------|
| Component rendering | 0% | 80% | Via component E2E tests |
| User interactions | 20% | 90% | Click, input, keyboard |
| API integration | 40% | 85% | Mock & real endpoint tests |
| Error handling | 10% | 70% | Toast errors, validation |
| State management | 0% | 75% | Store action tests |
| **Total** | **14%** | **80%** | By end of Phase 5 |

---

## Migration Path: Monolithic → Modular

### Week 1: Build Setup + Foundations

1. Initialize src/ directory structure
2. Create esbuild.config.js and tsconfig.json
3. Migrate styles from inline to separate CSS files
4. Extract common components (Button, Input, Toast)
5. Create basic Zustand stores
6. Set up test infrastructure
7. **Deliverable:** Working dev build, first E2E tests pass

### Week 2-3: Chat Interface

1. Extract ChatMessage, MessageActions, InputBox
2. Extract TabBar, ChatWindow
3. Wire up chatStore to components
4. Write E2E tests for all chat features
5. Create component stories (optional)
6. **Deliverable:** Chat interface 100% modular, all tests green

### Week 3-4: Repo Panel

1. Extract RepoSelector, SearchBox, FileTreeNode, RepoTree
2. Wire repoStore to components
3. Extract ConfigPanel subcomponents
4. Test repository operations
5. **Deliverable:** Repo selection fully modular, tree renders correctly

### Week 4-5: Tools & Modals

1. Extract ToolsPanel subcomponents
2. Extract Modal, DiffViewer, WritePanel, BatchPanel
3. Wire uiStore for modal state
4. Command palette component
5. Write modal interaction tests
6. **Deliverable:** All modals working, 30+ E2E tests

### Week 5-6: API Client Integration

1. Create api/ directory structure
2. Refactor API calls out of components into api modules
3. Wire API calls to update stores
4. Test error handling and retries
5. **Deliverable:** Zero direct fetch() calls in components

### Week 6-7: Integration & Polish

1. End-to-end workflow tests
2. Performance optimization (code splitting, lazy loading)
3. Error boundary components
4. Analytics/telemetry updates
5. Build output validation
6. **Deliverable:** Production-ready build, all tests passing

### Week 7-8: Documentation & Handoff

1. Component API documentation
2. Store usage guide
3. Testing guidelines
4. Migration guide for future work
5. Deploy to production
6. Monitor error rates
7. **Deliverable:** Complete modular codebase, zero regressions

---

## File Creation Checklist

### Phase 1: Build & Configuration
- [ ] `tsconfig.json` - TypeScript compiler options
- [ ] `esbuild.config.js` - Build configuration
- [ ] `.prettierrc` - Code formatting rules
- [ ] `src/index.html` - Main HTML (copy from static/)
- [ ] `src/index.ts` - App entry point (initialize app)
- [ ] `src/styles/global.css` - CSS variables, resets
- [ ] `src/styles/components.css` - Component styles
- [ ] `src/styles/layout.css` - Layout styles

### Phase 2: Foundation Components
- [ ] `src/components/common/Button.ts`
- [ ] `src/components/common/Input.ts`
- [ ] `src/components/common/Toast.ts`
- [ ] `src/components/common/Dialog.ts`
- [ ] `src/components/common/__tests__/Toast.spec.ts`
- [ ] `src/components/common/__tests__/Dialog.spec.ts`

### Phase 3: Layout Components
- [ ] `src/components/Layout/Sidebar.ts`
- [ ] `src/components/Layout/MainPanel.ts`
- [ ] `src/components/Layout/CommandPalette.ts`
- [ ] `src/components/Layout/SettingsPanel.ts`

### Phase 4: Chat Components
- [ ] `src/components/ChatInterface/ChatMessage.ts`
- [ ] `src/components/ChatInterface/MessageActions.ts`
- [ ] `src/components/ChatInterface/InputBox.ts`
- [ ] `src/components/ChatInterface/ChatWindow.ts`
- [ ] `src/components/ChatInterface/TabBar.ts`
- [ ] `src/components/ChatInterface/__tests__/ChatMessage.spec.ts`
- [ ] `src/components/ChatInterface/__tests__/InputBox.spec.ts`
- [ ] `src/components/ContextPanel/TokenMeter.ts`

### Phase 5: Repo Components
- [ ] `src/components/RepoPanel/RepoSelector.ts`
- [ ] `src/components/RepoPanel/SearchBox.ts`
- [ ] `src/components/RepoPanel/FileTreeNode.ts`
- [ ] `src/components/RepoPanel/RepoTree.ts`
- [ ] `src/components/ConfigPanel/ProviderSelector.ts`
- [ ] `src/components/ConfigPanel/ApiKeyInput.ts`
- [ ] `src/components/ConfigPanel/ModelSelector.ts`
- [ ] `src/components/ConfigPanel/SettingsForm.ts`

### Phase 6: Tools & Modals
- [ ] `src/components/ToolsPanel/FeatureFlagsSection.ts`
- [ ] `src/components/ToolsPanel/HFBuildStatus.ts`
- [ ] `src/components/ToolsPanel/ModeSelector.ts`
- [ ] `src/components/ToolsPanel/ToolsList.ts`
- [ ] `src/components/ModalWindow/Modal.ts`
- [ ] `src/components/ModalWindow/DiffViewer.ts`
- [ ] `src/components/ModalWindow/WritePanel.ts`
- [ ] `src/components/ModalWindow/BatchPanel.ts`
- [ ] `src/components/ModalWindow/DepsAudit.ts`

### Phase 7: State Management
- [ ] `src/stores/chatStore.ts`
- [ ] `src/stores/repoStore.ts`
- [ ] `src/stores/configStore.ts`
- [ ] `src/stores/uiStore.ts`
- [ ] `src/stores/toolsStore.ts`
- [ ] `src/stores/statsStore.ts`
- [ ] `src/stores/index.ts`

### Phase 8: Utilities & Types
- [ ] `src/utils/formatters.ts`
- [ ] `src/utils/storage.ts`
- [ ] `src/utils/markdown.ts`
- [ ] `src/utils/dom.ts`
- [ ] `src/utils/validators.ts`
- [ ] `src/utils/constants.ts`
- [ ] `src/types/chat.ts`
- [ ] `src/types/repo.ts`
- [ ] `src/types/config.ts`
- [ ] `src/types/api.ts`

### Phase 9: API Client
- [ ] `src/api/client.ts`
- [ ] `src/api/github.ts`
- [ ] `src/api/repo.ts`
- [ ] `src/api/hf.ts`
- [ ] `src/api/config.ts`
- [ ] `src/api/types.ts`

### Phase 10: E2E Tests
- [ ] `e2e/chat.spec.ts`
- [ ] `e2e/config.spec.ts`
- [ ] `e2e/repo.spec.ts`
- [ ] `e2e/workflow.spec.ts`
- [ ] `e2e/fixtures/auth.ts`
- [ ] `e2e/fixtures/mocks.ts`

---

## Estimated Implementation Timeline

| Phase | Week(s) | Deliverables | Risk |
|-------|---------|--------------|------|
| 1 | 1 | Build setup, common components, 1st tests | Low |
| 2 | 2-3 | Chat interface (100% modular) | Low |
| 3 | 3-4 | Repo panel, config panel | Medium |
| 4 | 4-5 | Tools, modals, 30+ tests | Medium |
| 5 | 5-6 | API client integration | High |
| 6 | 6-7 | End-to-end tests, optimization | Medium |
| 7 | 7-8 | Documentation, launch | Low |
| **Total** | **6-8 weeks** | **Production-ready app** | **Medium** |

### Resource Requirements

- **1 Frontend Developer** (full-time)
- **1 QA Engineer** (0.5 FTE for E2E testing)
- **DevOps** (CI/CD integration, deployment)
- **API Team** (support for API client integration, no blockers)

### Critical Path

```
Build Config → Common Components → Chat → Repo Panel →
Tools & Modals → API Integration → Testing → Deploy
```

**Longest poles:** Chat interface extraction (2 wks), API client integration (1 wk)

---

## Success Criteria

### Development
- [ ] Zero lint errors
- [ ] TypeScript strict mode enabled
- [ ] 80%+ code coverage (E2E + unit)
- [ ] All existing features work identically
- [ ] No new console errors in production

### Performance
- [ ] Bundle size < 500KB gzipped
- [ ] Initial page load < 2s (from 3s)
- [ ] Chat response time unchanged
- [ ] No memory leaks over 30min session

### Quality
- [ ] All 50+ E2E tests passing
- [ ] Regression test suite for old features
- [ ] Feature parity with monolithic version
- [ ] Error handling for all API calls

### Deployment
- [ ] Zero downtime migration
- [ ] Rollback plan in place
- [ ] Canary deployment (5% of traffic)
- [ ] Monitoring/alerting configured

---

## Post-Phase 5 Opportunities

1. **Component Library:** Export components for other projects
2. **CLI Plugin System:** Modular custom tools via npm packages
3. **Mobile App:** React Native using shared component logic
4. **Dark Mode Enhancement:** CSS-in-JS or Tailwind CSS migration
5. **Performance:** Code splitting per route, service worker caching
6. **Testing:** Visual regression tests, accessibility audits (axe)
7. **Documentation:** Storybook for component preview
8. **Analytics:** Track user behavior per component

---

## Appendix: Code Patterns

### Component Template

```typescript
// src/components/Example/ExampleComponent.ts

interface ExampleProps {
  title: string;
  onAction?: (value: string) => void;
}

export function ExampleComponent({ title, onAction }: ExampleProps): HTMLElement {
  const container = document.createElement('div');
  container.className = 'example-component';

  const heading = document.createElement('h3');
  heading.textContent = title;
  container.appendChild(heading);

  const button = document.createElement('button');
  button.textContent = 'Click me';
  button.addEventListener('click', () => {
    onAction?.('action-performed');
  });
  container.appendChild(button);

  return container;
}
```

### Store Usage in Components

```typescript
// In component
import { useChatStore } from '@stores';

function updateUIFromStore() {
  const { messages, addMessage } = useChatStore();
  
  const unsubscribe = useChatStore.subscribe(
    (state) => state.messages,
    (messages) => {
      // Re-render when messages change
      renderMessages(messages);
    }
  );

  // Cleanup on component destroy
  return () => unsubscribe();
}
```

### E2E Test Template

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should do X when user does Y', async ({ page }) => {
    // Arrange
    const element = page.locator('#target');

    // Act
    await element.click();

    // Assert
    await expect(element).toContainText('expected text');
  });
});
```

---

## Questions for Stakeholders

1. **Backwards compatibility:** Can we break old localStorage format? (Answer: Yes, graceful degradation OK)
2. **Browser support:** IE11 or modern browsers only? (Assumed: Modern)
3. **Third-party scripts:** Keep Sentry/Rollbar/PostHog CDN loads? (Assumed: Yes, lazy-load after init)
4. **Build output location:** Keep dist/ directory or move? (Assumed: dist/ is final)
5. **Deployment:** Cloudflare Pages, GitHub Pages, or custom server? (Assumed: Existing server)

---

**Document Version:** 1.0  
**Last Updated:** June 2026  
**Status:** Ready for Implementation  
**Estimated Start:** Next Sprint
