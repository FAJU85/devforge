# DevForge API Integration Guide

This guide explains how to use the API clients and services in DevForge.

## Table of Contents

1. [Overview](#overview)
2. [API Clients](#api-clients)
3. [Services Layer](#services-layer)
4. [Quick Start](#quick-start)
5. [Examples](#examples)
6. [Configuration](#configuration)

## Overview

DevForge provides a three-layer architecture for API communication:

```
UI Components
    ↓
Services (ChatService, RepoService, ConfigService, ContextService)
    ↓
API Clients (GitHubClient, RepositoryClient, HuggingFaceClient, ConfigClient)
    ↓
Backend APIs / External Services
```

- **API Clients**: Low-level HTTP communication with type-safe endpoints
- **Services**: Business logic that integrates API clients with Zustand stores
- **UI Components**: React components that consume services

## API Clients

### Base Client (ApiClient)

The `ApiClient` class provides the foundation for all API communication:

```typescript
import { ApiClient } from '@devforge/api/client';

const client = new ApiClient({
  baseUrl: 'http://localhost:3000/api',
  timeout: 30000,
  headers: { 'X-Custom': 'value' },
});

// HTTP Methods
const response = await client.get('/endpoint');
const response = await client.post('/endpoint', { data });
const response = await client.put('/endpoint', { data });
const response = await client.patch('/endpoint', { data });
const response = await client.delete('/endpoint');

// Auth
client.setAuthHeader('token', 'Bearer');
client.clearAuthHeader();

// Headers
client.addHeader('X-Custom', 'value');
client.removeHeader('X-Custom');
```

### GitHubClient

Interact with GitHub repositories and APIs:

```typescript
import { GitHubClient } from '@devforge/api/github';

const github = new GitHubClient('gh_token');

// Users
const user = await github.getUser('username');
const authUser = await github.getAuthenticatedUser();

// Repositories
const repo = await github.getRepository('owner', 'repo');
const repos = await github.listUserRepositories('username');

// Commits
const commits = await github.getRepositoryCommits('owner', 'repo');
const commit = await github.getCommit('owner', 'repo', 'sha');

// Pull Requests
const prs = await github.listPullRequests('owner', 'repo', 'open');
const pr = await github.getPullRequest('owner', 'repo', 123);

// Issues
const issues = await github.listIssues('owner', 'repo', 'open');
const issue = await github.getIssue('owner', 'repo', 456);
const created = await github.createIssue('owner', 'repo', 'Title', 'Body');
const updated = await github.updateIssue('owner', 'repo', 456, { state: 'closed' });

// Search
const results = await github.searchRepositories('query');
const codeResults = await github.searchCode('query', 'owner', 'repo');
```

### RepositoryClient

Manage local and remote repositories:

```typescript
import { RepositoryClient } from '@devforge/api/repo';

const repo = new RepositoryClient('http://localhost:3000/api');

// Repository Info
const info = await repo.getRepositoryInfo('/path/to/repo');
const branch = await repo.getCurrentBranch('/path/to/repo');
const branches = await repo.listBranches('/path/to/repo');

// Files
const file = await repo.getFileContent('/path/to/repo', 'src/index.ts');
const files = await repo.listFiles('/path/to/repo', 'src');
const tree = await repo.getDirectoryTree('/path/to/repo', 3);

// Search & Analysis
const results = await repo.searchFiles('/path/to/repo', 'query', 'ts');
const symbol = await repo.findSymbol('/path/to/repo', 'MyClass');
const languages = await repo.getLanguages('/path/to/repo');
const stats = await repo.getCodeStats('/path/to/repo');
const analysis = await repo.analyzeRepository('/path/to/repo');

// Diffs
const diff = await repo.getDiff('/path/to/repo', 'main', 'feature');
const fileDiff = await repo.getFileDiff('/path/to/repo', 'src/index.ts');

// Write Operations
const written = await repo.writeFile('/path/to/repo', 'new-file.ts', 'content');
const deleted = await repo.deleteFile('/path/to/repo', 'old-file.ts');
```

### HuggingFaceClient

Search and interact with HuggingFace Hub:

```typescript
import { HuggingFaceClient } from '@devforge/api/hf';

const hf = new HuggingFaceClient('hf_token');

// Search
const models = await hf.searchModels('bert', 20, 0, { task: 'text-classification' });
const datasets = await hf.searchDatasets('imagenet');
const spaces = await hf.searchSpaces('gradio');

// Models
const model = await hf.getModel('bert-base-uncased');
const info = await hf.getModelInfo('bert-base-uncased');
const files = await hf.listModelFiles('bert-base-uncased');
const file = await hf.getModelFile('bert-base-uncased', 'README.md');

// Trending & Popular
const trending = await hf.getTrendingModels(20);
const newest = await hf.getNewestModels(20);
const popular = await hf.getMostDownloadedModels(20);

// Tasks & Discovery
const taskModels = await hf.searchByTask('text-generation', 20);
const tags = await hf.listModelTags();

// Analytics
const downloads = await hf.getModelDownloads('bert-base-uncased', 'week');
```

### ConfigClient

Manage DevForge configuration:

```typescript
import { ConfigClient } from '@devforge/api/config';

const config = new ConfigClient('http://localhost:3000/api');

// API Keys
const keys = await config.listAPIKeys();
const key = await config.createAPIKey('anthropic', 'sk-...');
const valid = await config.validateAPIKey('anthropic', 'sk-...');
await config.deleteAPIKey('key-id');

// Models
const models = await config.listModels();
const model = await config.getModel('claude-opus');
const created = await config.createModel({ /* ... */ });
const updated = await config.updateModel('model-id', { /* ... */ });
const byProvider = await config.getModelsByProvider('anthropic');

// Providers
const providers = await config.listProviders();
const provider = await config.getProvider('provider-id');
const connected = await config.testProviderConnection('provider-id');

// Feature Flags
const flags = await config.listFeatureFlags();
const flag = await config.getFeatureFlag('canaryDeployment');
const enabled = await config.isFeatureEnabled('betaFeatures');
await config.updateFeatureFlag('betaFeatures', { enabled: true });

// Preferences
const prefs = await config.getUserPreferences();
await config.updateUserPreferences({ theme: 'dark', fontSize: 14 });

// System
const status = await config.getSystemStatus();
const version = await config.getVersion();
```

## Services Layer

Services provide business logic that integrates API clients with Zustand stores.

### ChatService

Handle conversations with token tracking and cost calculation:

```typescript
import { ChatService } from '@devforge/services';

const chat = new ChatService('http://localhost:3000/api');

// Conversations
const conversationId = await chat.createConversation('My Chat');
await chat.deleteConversation(conversationId);
const conversations = await chat.getConversations();

// Messages
const response = await chat.sendMessage(
  conversationId,
  'What is TypeScript?',
  'claude-opus',
  0.7
);

// The service automatically:
// - Adds user message to ChatStore
// - Sends to API
// - Adds assistant response to ChatStore
// - Records usage in StatsStore
// - Calculates tokens and costs
```

### RepositoryService

Explore repositories with store integration:

```typescript
import { RepositoryService } from '@devforge/services';

const repo = new RepositoryService('http://localhost:3000/api');

// Load repository (adds to RepoStore)
const repoInfo = await repo.loadRepository('/path/to/repo');

// Load file tree (updates RepoStore)
const fileTree = await repo.loadFileTree('/path/to/repo', 3);

// File operations
const content = await repo.getFileContent('/path/to/repo', 'src/index.ts');
const files = await repo.listFiles('/path/to/repo', 'src');

// Search
const results = await repo.searchFiles('/path/to/repo', 'component');
const symbols = await repo.findSymbol('/path/to/repo', 'MyClass');

// Analysis
const languages = await repo.getLanguages('/path/to/repo');
const stats = await repo.getCodeStats('/path/to/repo');
const analysis = await repo.analyzeRepository('/path/to/repo');

// Write
const written = await repo.writeFile('/path/to/repo', 'new.ts', 'content');
const deleted = await repo.deleteFile('/path/to/repo', 'old.ts');
```

### ConfigService

Manage configuration with store integration:

```typescript
import { ConfigService } from '@devforge/services';

const config = new ConfigService('http://localhost:3000/api');

// API Keys
const keys = await config.loadAPIKeys();
const key = await config.createAPIKey('anthropic', 'sk-...');
const valid = await config.validateAPIKey('anthropic', 'sk-...');
await config.deleteAPIKey('key-id');

// Providers (adds to ConfigStore)
const providers = await config.loadProviders();
const connected = await config.testProviderConnection('provider-id');

// Models
const models = await config.loadModels();
const model = await config.getModel('claude-opus');
const byProvider = await config.getModelsByProvider('anthropic');

// Feature Flags (updates ConfigStore)
const flags = await config.loadFeatureFlags();
const enabled = await config.isFeatureEnabled('canaryDeployment');
await config.updateFeatureFlag('betaFeatures', true);

// Preferences
const prefs = await config.loadUserPreferences();
await config.updateUserPreferences({ theme: 'dark' });

// System
const status = await config.getSystemStatus();
const version = await config.getAppVersion();
```

### ContextService

Build intelligent context with token limits:

```typescript
import { ContextService } from '@devforge/services';

const context = new ContextService('http://localhost:3000/api');

// Add files (respects token limits)
const file = await context.addFileToContext('/path/to/repo', 'src/index.ts');
const files = await context.addMultipleFilesToContext('/path/to/repo', [
  'src/types.ts',
  'src/api/client.ts',
]);

// Search and auto-add
const found = await context.searchAndAddFiles('/path/to/repo', 'store', 5);
const related = await context.addRelatedFiles('/path/to/repo', 'src/index.ts');

// Management
await context.removeFileFromContext('file-id');
await context.updateFileInContext('file-id', 'new content');
context.clearContext();

// Information
const summary = context.getContextSummary();
// { filesCount, totalTokens, availableTokens, percentageUsed, maxTokens }

const hasRoom = context.hasRoom(1000);
const available = context.getAvailableTokens();

// Configuration
context.setMaxContextTokens(16000);
```

### ServiceContainer

Centralized service management:

```typescript
import { ServiceContainer } from '@devforge/services';

// Initialize (singleton pattern)
const services = ServiceContainer.initialize({
  apiBaseUrl: 'http://localhost:3000/api',
  authToken: 'your-token',
});

// Get individual services
const chat = services.getChat();
const repo = services.getRepository();
const config = services.getConfig();
const context = services.getContext();

// Update configuration
services.setBaseUrl('http://new-api.example.com/api');
services.setAuthToken('new-token');
services.updateConfig({ apiBaseUrl: '...', authToken: '...' });

// Health check
const health = await services.healthCheck();
// { healthy, services: { chat, repository, config, context } }

// Reset
services.reset();
```

## Quick Start

```typescript
import { ServiceContainer } from '@devforge/services';

// 1. Initialize services
const services = ServiceContainer.initialize({
  apiBaseUrl: 'http://localhost:3000/api',
  authToken: process.env.API_TOKEN,
});

// 2. Create a conversation
const chat = services.getChat();
const conversationId = await chat.createConversation('My Chat');

// 3. Build context from repository
const context = services.getContext();
const repo = services.getRepository();

const repoInfo = await repo.loadRepository('/path/to/repo');
await context.addFileToContext('/path/to/repo', 'src/index.ts');
await context.addFileToContext('/path/to/repo', 'src/types.ts');

// 4. Send message with context
const response = await chat.sendMessage(
  conversationId,
  'Review this code',
  'claude-opus'
);

console.log(response?.content);
```

## Examples

See `src/examples/serviceUsage.ts` for detailed examples:

- `example1_sendMessage()` - Send chat messages
- `example2_exploreRepository()` - Explore code structure
- `example3_manageConfig()` - Manage configuration
- `example4_buildContext()` - Build file context
- `example5_chatWithContext()` - Complete workflow
- `example6_serviceHealth()` - Monitor service health
- `example7_updateConfig()` - Update configuration at runtime
- `example8_errorHandling()` - Handle errors gracefully

## Configuration

Services support configuration via `ServiceContainer.initialize()`:

```typescript
ServiceContainer.initialize({
  // Required
  apiBaseUrl: 'http://localhost:3000/api',

  // Optional
  authToken: 'api-token',
  timeout: 30000,
});
```

All services share the same configuration. Update at runtime:

```typescript
const services = ServiceContainer.getInstance();

// Update base URL
services.setBaseUrl('http://new-api.example.com/api');

// Update auth token
services.setAuthToken('new-token');

// Update multiple settings
services.updateConfig({
  apiBaseUrl: 'http://localhost:4000/api',
  authToken: 'new-token',
  timeout: 60000,
});
```

## Error Handling

All services throw errors with descriptive messages:

```typescript
try {
  const conversation = await chat.createConversation('Test');
} catch (error) {
  console.error('Failed:', error.message);
}
```

Services also gracefully update stores on API errors:

```typescript
// ChatService adds error messages to store
const response = await chat.sendMessage(conversationId, 'Hello');
// If API fails, error message is still added to ChatStore

// ContextService respects limits
try {
  await context.addFileToContext(path, file);
} catch (error) {
  // File not added if it would exceed token limit
  console.log('Context full:', error.message);
}
```
