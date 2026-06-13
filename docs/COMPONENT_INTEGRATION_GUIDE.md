# Component Integration Guide

This guide explains how to integrate the API layer with React components using the provided hooks and integration examples.

## Quick Start

### 1. Basic Hook Usage

```typescript
import { useChat } from '@devforge/hooks';

function MyChatComponent() {
  const chat = useChat('http://localhost:3000/api');

  const handleSendMessage = async (message: string) => {
    await chat.sendMessage(chat.activeConversationId, message);
  };

  return (
    <div>
      {/* Your component JSX */}
    </div>
  );
}
```

### 2. Use Integration Components

For a faster start, use the provided integration examples:

```typescript
import { ChatWindowIntegration } from '@devforge/components/integration';

function App() {
  return (
    <ChatWindowIntegration 
      apiBaseUrl="http://localhost:3000/api"
      authToken={process.env.REACT_APP_API_TOKEN}
    />
  );
}
```

## Integration Components

### ChatWindowIntegration

Complete chat interface with conversation management.

**Features:**
- Conversation creation and switching
- Message sending with loading states
- Automatic token tracking
- Error handling and recovery
- Message history display

**Props:**
```typescript
interface ChatWindowIntegrationProps {
  apiBaseUrl?: string;           // Default: 'http://localhost:3000/api'
  authToken?: string;            // Optional auth token
  onError?: (error: Error) => void; // Error callback
}
```

**Usage:**
```typescript
<ChatWindowIntegration
  apiBaseUrl={API_URL}
  authToken={token}
  onError={(err) => console.error(err)}
/>
```

**Key State:**
- `chat.conversations`: Available conversations
- `chat.activeConversationId`: Currently selected conversation
- `chat.messages`: All messages

**Key Actions:**
- `chat.sendMessage()`: Send a message
- `chat.createConversation()`: Create new conversation
- `chat.switchConversation()`: Switch active conversation

### RepositoryBrowserIntegration

File explorer with search and content viewing.

**Features:**
- Interactive file tree navigation
- File content viewing
- Repository search
- Language statistics
- Repository analysis

**Props:**
```typescript
interface RepositoryBrowserIntegrationProps {
  apiBaseUrl?: string;
  initialRepoPath?: string;      // Default: '/home/user/devforge'
  onError?: (error: Error) => void;
}
```

**Usage:**
```typescript
<RepositoryBrowserIntegration
  apiBaseUrl={API_URL}
  initialRepoPath="/path/to/repo"
  onError={(err) => console.error(err)}
/>
```

**Key State:**
- `repo.repositories`: Loaded repositories
- `repo.fileTree`: File tree structure
- `repo.openFiles`: Currently open files/tabs

**Key Actions:**
- `repo.loadRepository()`: Load repository
- `repo.loadFileTree()`: Load file tree
- `repo.getFileContent()`: Get file content
- `repo.searchFiles()`: Search files

### ConfigurationPanelIntegration

Configuration management interface.

**Features:**
- Provider management and connection testing
- Model selection and display
- Feature flag toggling
- System status monitoring

**Props:**
```typescript
interface ConfigurationPanelIntegrationProps {
  apiBaseUrl?: string;
  onError?: (error: Error) => void;
}
```

**Usage:**
```typescript
<ConfigurationPanelIntegration
  apiBaseUrl={API_URL}
  onError={(err) => console.error(err)}
/>
```

**Key State:**
- `config.providers`: Available providers
- `config.models`: Available models
- `config.activeProvider`: Selected provider
- `config.activeModel`: Selected model
- `config.featureFlags`: Feature flag states

**Key Actions:**
- `config.loadProviders()`: Load providers
- `config.loadModels()`: Load models
- `config.testProviderConnection()`: Test provider
- `config.setActiveModel()`: Set active model
- `config.toggleFeatureFlag()`: Toggle feature

### ContextManagerIntegration

Context file management with token limits.

**Features:**
- Token usage visualization
- Smart file discovery and addition
- Context limit enforcement
- File management
- Search-based file discovery

**Props:**
```typescript
interface ContextManagerIntegrationProps {
  repoPath: string;              // Repository path (required)
  apiBaseUrl?: string;
  onError?: (error: Error) => void;
}
```

**Usage:**
```typescript
<ContextManagerIntegration
  repoPath="/path/to/repo"
  apiBaseUrl={API_URL}
  onError={(err) => console.error(err)}
/>
```

**Key State:**
- `context.files`: Files in context
- `context.totalTokens`: Token usage
- `context.availableTokens`: Remaining tokens
- `context.tokenPercentage`: Usage percentage

**Key Actions:**
- `context.addFile()`: Add file to context
- `context.removeFile()`: Remove file
- `context.searchAndAddFiles()`: Auto-add files
- `context.clearContext()`: Clear all files
- `context.setMaxTokens()`: Configure limits

## Building Custom Components

### Pattern 1: Simple Wrapper

Create a wrapper component around an integration component:

```typescript
import { ChatWindowIntegration } from '@devforge/components/integration';

export function MyChat() {
  const handleError = (error: Error) => {
    // Handle error globally
    showNotification('error', error.message);
  };

  return (
    <ChatWindowIntegration
      apiBaseUrl={process.env.REACT_APP_API_URL}
      authToken={getAuthToken()}
      onError={handleError}
    />
  );
}
```

### Pattern 2: Custom Component Using Hooks

Create a custom component using the hooks directly:

```typescript
import { useChat, useRepository, useConfig } from '@devforge/hooks';

export function DashboardComponent() {
  const chat = useChat();
  const repo = useRepository();
  const config = useConfig();

  useEffect(() => {
    // Initialize data
    config.loadProviders();
    repo.loadRepository('/path/to/repo');
  }, []);

  return (
    <div className="dashboard">
      {/* Custom layout combining all hooks */}
      <div className="left-panel">{/* Chat UI */}</div>
      <div className="center-panel">{/* Repository UI */}</div>
      <div className="right-panel">{/* Config UI */}</div>
    </div>
  );
}
```

### Pattern 3: Feature-Specific Component

Create a focused component for a specific feature:

```typescript
import { useContext } from '@devforge/hooks';

export function SmartContextBuilder({
  repoPath,
}: {
  repoPath: string;
}) {
  const context = useContextValue();
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);

  const handleQuickAdd = async () => {
    await context.addMultipleFiles(repoPath, selectedFiles);
  };

  return (
    <div className="context-builder">
      {/* Custom context-building UI */}
    </div>
  );
}
```

## Integration Patterns

### Error Handling

All hooks provide comprehensive error handling:

```typescript
function MyComponent() {
  const chat = useChat();
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (message: string) => {
    try {
      await chat.sendMessage(chat.activeConversationId, message);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message);
    }
  };

  return (
    <>
      {error && <ErrorBanner message={error} />}
      {/* Component JSX */}
    </>
  );
}
```

### Loading States

Components automatically update store state. Show loading states:

```typescript
function MyComponent() {
  const chat = useChat();
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (message: string) => {
    setIsLoading(true);
    try {
      await chat.sendMessage(chat.activeConversationId, message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button onClick={() => handleSend('Hi')} disabled={isLoading}>
      {isLoading ? 'Sending...' : 'Send'}
    </button>
  );
}
```

### Store Integration

Hooks automatically update Zustand stores:

```typescript
function MyComponent() {
  const chat = useChat();
  const chatStore = useChatStore(); // Direct store access if needed

  // chat hook keeps store in sync
  // chatStore updates reflected in UI automatically

  return (
    <div>
      {chat.conversations.map((conv) => (
        <div key={conv.id}>{conv.title}</div>
      ))}
    </div>
  );
}
```

## Best Practices

### 1. Initialize Services at App Level

```typescript
function App() {
  useEffect(() => {
    // Initialize on app load
    ServiceContainer.initialize({
      apiBaseUrl: process.env.REACT_APP_API_URL,
      authToken: getStoredToken(),
    });
  }, []);

  return <Routes>{/* App routes */}</Routes>;
}
```

### 2. Provide Global Error Handler

```typescript
function App() {
  const handleError = (error: Error) => {
    console.error('API Error:', error);
    // Show user-friendly notification
    showNotification('error', 'An error occurred');
  };

  return (
    <ErrorBoundary onError={handleError}>
      <Routes>{/* App routes */}</Routes>
    </ErrorBoundary>
  );
}
```

### 3. Use Context for Shared State

```typescript
// Create app context
const AppContext = createContext<{
  apiUrl: string;
  authToken: string;
}>({
  apiUrl: '',
  authToken: '',
});

// Use in components
function MyComponent() {
  const { apiUrl, authToken } = useContext(AppContext);
  const chat = useChat(apiUrl);
  // ...
}
```

### 4. Optimize Re-renders

Hooks use `useCallback` internally, but you should also optimize:

```typescript
function ChatList() {
  const chat = useChat();

  // Memoize if lists are large
  const memoizedConversations = useMemo(
    () => chat.conversations,
    [chat.conversations]
  );

  return (
    <ul>
      {memoizedConversations.map((conv) => (
        <ConversationItem key={conv.id} conversation={conv} />
      ))}
    </ul>
  );
}
```

## Testing

### Unit Test Example

```typescript
import { renderHook, act } from '@testing-library/react';
import { useChat } from '@devforge/hooks';

describe('useChat', () => {
  it('should create a conversation', async () => {
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.createConversation('Test Chat');
    });

    expect(result.current.conversations.length).toBeGreaterThan(0);
  });
});
```

### Integration Test Example

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatWindowIntegration } from '@devforge/components/integration';

describe('ChatWindowIntegration', () => {
  it('should send a message', async () => {
    const user = userEvent.setup();
    render(<ChatWindowIntegration apiBaseUrl="http://localhost:3000/api" />);

    const input = screen.getByPlaceholderText('Type your message...');
    const button = screen.getByRole('button', { name: /send/i });

    await user.type(input, 'Hello');
    await user.click(button);

    expect(input).toHaveValue('');
  });
});
```

## Troubleshooting

### API Connection Issues

1. Check `apiBaseUrl` is correct
2. Verify backend is running
3. Check auth token is valid
4. Look for CORS issues in browser console

### State Not Updating

1. Verify hook is called in component
2. Check store state with Redux DevTools
3. Ensure error callback isn't hiding errors
4. Verify network requests in browser DevTools

### Performance Issues

1. Check for unnecessary re-renders with React DevTools Profiler
2. Memoize expensive computations
3. Lazy load large file content
4. Implement pagination for large lists

## Advanced Topics

### Custom Service Container

```typescript
const customContainer = ServiceContainer.initialize({
  apiBaseUrl: 'https://api.production.com',
  authToken: process.env.PROD_API_TOKEN,
  timeout: 60000,
});

// Use custom container in component
const chat = customContainer.getChat();
```

### Request Interceptors

For request/response handling, extend ApiClient:

```typescript
class CustomApiClient extends ApiClient {
  async request<T>(endpoint: string, options: RequestInit) {
    // Add custom logic here
    return super.request<T>(endpoint, options);
  }
}
```

### Offline Support

Implement with Service Worker and local storage:

```typescript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

// Hooks automatically use localStorage via Zustand persist
const chat = useChat(); // Automatically syncs with localStorage
```

## Next Steps

1. Review the integration examples in `src/components/integration/`
2. Try the examples in your app
3. Create custom components following the patterns
4. Implement error handling and loading states
5. Add tests for your components

For more details, see:
- [API Integration Guide](./API_INTEGRATION.md)
- [Phase 5 Summary](./PHASE5_INTEGRATION_SUMMARY.md)
- [Example Usage](../src/examples/serviceUsage.ts)
