/**
 * DevForge Frontend - Main Entry Point
 * Foundation components, layout components, and state management
 */

// Foundation Components
export { Button } from './components/common/Button';
export { Input } from './components/common/Input';
export { Toast } from './components/common/Toast';
export { Dialog } from './components/common/Dialog';

// Layout Components
export { Sidebar } from './components/layout/Sidebar';
export { MainPanel } from './components/layout/MainPanel';
export { SettingsPanel } from './components/layout/SettingsPanel';
export { CommandPalette } from './components/layout/CommandPalette';

// Chat Components
export { ChatWindow } from './components/chat/ChatWindow';
export { ChatMessage } from './components/chat/ChatMessage';
export { InputBox } from './components/chat/InputBox';
export { TokenMeter } from './components/chat/TokenMeter';

// Repository Components
export { RepoSelector } from './components/repo/RepoSelector';
export { RepoTree } from './components/repo/RepoTree';
export { FileTreeNode } from './components/repo/FileTreeNode';
export { SearchBox } from './components/repo/SearchBox';

// Configuration Components
export { ProviderSelector } from './components/config/ProviderSelector';
export { ModelSelector } from './components/config/ModelSelector';
export { ApiKeyInput } from './components/config/ApiKeyInput';
export { SettingsForm } from './components/config/SettingsForm';

// Context Components
export { ContextDisplay } from './components/context/ContextDisplay';
export { FileList } from './components/context/FileList';
export { ContextInfo } from './components/context/ContextInfo';

// Modal Components
export { DiffViewer } from './components/modals/DiffViewer';
export { WritePanel } from './components/modals/WritePanel';
export { BatchPanel } from './components/modals/BatchPanel';
export { DepsAudit } from './components/modals/DepsAudit';

// Integration Components
export { AppLayout } from './components/integration/AppLayout';
export { StatusBar } from './components/integration/StatusBar';
export { NotificationHub } from './components/integration/NotificationHub';
export { ThemeToggle } from './components/integration/ThemeToggle';

// Stores
export { useUIStore } from './stores/uiStore';
export { useChatStore } from './stores/chatStore';
export { useRepoStore } from './stores/repoStore';
export { useConfigStore } from './stores/configStore';
export { useContextStore } from './stores/contextStore';
export { useMemoryStore } from './stores/memoryStore';
export { useStatsStore } from './stores/statsStore';

// API Clients
export { ApiClient } from './api/client';
export { GitHubClient } from './api/github';
export { RepositoryClient } from './api/repo';
export { HuggingFaceClient } from './api/hf';
export { ConfigClient } from './api/config';
export { OptimizedApiClient } from './api/optimizedClient';
export { WebSocketClient, getWebSocketClient } from './api/websocketClient';

// Services
export { ChatService, RepositoryService, ConfigService, ContextService, ServiceContainer } from './services';

// Hooks
export { useChat, useRepository, useConfig, useContextValue, useRealtimeUpdates, useOptimizedApi } from './hooks';

// Utilities
export { RequestCache, RequestDeduplicator, RequestBatcher, createCacheKey } from './utils';

// Types
export type { ApiResponse, ApiConfig } from './api/client';
export type { GitHubUser, GitHubRepository, GitHubCommit, GitHubPullRequest, GitHubIssue } from './api/github';
export type { FileInfo, DirectoryTree, SearchResult, RepositoryInfo, DiffResult } from './api/repo';
export type { HFModel, HFDataset, HFSpace, HFModelInfo, HFSearchResult } from './api/hf';
export type { AppConfig, UserPreferences, APIKey, Model, Provider, FeatureFlag } from './api/config';
export type { OptimizedClientConfig } from './api/optimizedClient';
export type { WebSocketConfig, WebSocketMessage, WebSocketEventType } from './api/websocketClient';
export type { ChatMessage, ChatResponse } from './services/chatService';
export type { ServiceConfig } from './services/serviceContainer';
export type { UseChatReturn } from './hooks/useChat';
export type { UseRepositoryReturn } from './hooks/useRepository';
export type { UseConfigReturn } from './hooks/useConfig';
export type { UseContextValue } from './hooks/useContext';
export type { ButtonProps } from './types/ui';
export type { InputProps } from './types/ui';
export type { ToastMessage } from './types/ui';
export type { DialogOptions } from './types/ui';
export type { UIState } from './stores/uiStore';
export type { ChatState, Conversation, ChatMessage } from './stores/chatStore';
export type { RepoState, Repository, FileNode } from './stores/repoStore';
export type { ConfigState, ProviderConfig, ModelConfig } from './stores/configStore';
export type { ContextState, ContextFile, ContextReference } from './stores/contextStore';
export type { MemoryState, MemoryItem, ConversationMemory } from './stores/memoryStore';
export type { StatsState, UsageMetric, ModelStats } from './stores/statsStore';
export type { CommandPaletteOptions } from './components/layout/CommandPalette';
export type { ChatWindowOptions } from './components/chat/ChatWindow';
export type { ChatMessageOptions } from './components/chat/ChatMessage';
export type { InputBoxOptions } from './components/chat/InputBox';
export type { TokenMeterOptions } from './components/chat/TokenMeter';
export type { RepoSelectorOptions, Repository } from './components/repo/RepoSelector';
export type { RepoTreeOptions } from './components/repo/RepoTree';
export type { FileTreeNodeOptions } from './components/repo/FileTreeNode';
export type { SearchBoxOptions, SearchResult } from './components/repo/SearchBox';
export type { ProviderSelectorOptions, Provider } from './components/config/ProviderSelector';
export type { ModelSelectorOptions, Model } from './components/config/ModelSelector';
export type { ApiKeyInputOptions } from './components/config/ApiKeyInput';
export type { SettingsFormOptions, SettingValue } from './components/config/SettingsForm';
export type { ContextDisplayOptions, ContextItem } from './components/context/ContextDisplay';
export type { FileListOptions, FileItem } from './components/context/FileList';
export type { ContextInfoOptions, ContextStats } from './components/context/ContextInfo';
export type { DiffViewerOptions } from './components/modals/DiffViewer';
export type { WritePanelOptions } from './components/modals/WritePanel';
export type { BatchPanelOptions, BatchOperation } from './components/modals/BatchPanel';
export type { DepsAuditOptions, Vulnerability } from './components/modals/DepsAudit';
export type { AppLayoutOptions } from './components/integration/AppLayout';
export type { StatusBarOptions, StatusItem } from './components/integration/StatusBar';
export type { NotificationHubOptions, Notification } from './components/integration/NotificationHub';
export type { ThemeToggleOptions, Theme } from './components/integration/ThemeToggle';
