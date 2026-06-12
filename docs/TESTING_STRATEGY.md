# Testing Strategy for Phase 5 API Integration

This document outlines the comprehensive testing strategy for the API clients, services, and React hooks.

## Testing Pyramid

```
          E2E Tests (Integration)
       /                    \
     Service Integration    API Tests
     /                    \
   Hook Tests          Unit Tests
 /                    \
Component Tests    Mock Tests
```

## Test Levels

### 1. Unit Tests (Low-level)

**Scope:** Individual functions and classes

**Tools:** Jest + React Testing Library

**Examples:**

#### API Client Tests
```typescript
describe('ApiClient', () => {
  it('should set auth header correctly', () => {
    const client = new ApiClient({ baseUrl: 'http://localhost:3000' });
    client.setAuthHeader('test-token');
    
    // Verify header is set
    expect(client).toBeDefined();
  });

  it('should handle timeout', async () => {
    const client = new ApiClient({
      baseUrl: 'http://localhost:3000',
      timeout: 100,
    });
    
    // This should timeout
    await expect(
      client.get('/slow-endpoint')
    ).rejects.toThrow('timeout');
  });
});
```

#### Service Tests
```typescript
describe('ChatService', () => {
  it('should estimate tokens correctly', () => {
    const service = new ChatService();
    
    // Test token estimation logic
    const tokens = service.sendMessage(...);
    expect(tokens).toBeGreaterThan(0);
  });

  it('should calculate cost correctly', () => {
    // Test cost calculation for different models
    const cost = service.calculateCost('claude-opus', 1000);
    expect(cost).toBeGreaterThan(0);
  });
});
```

#### Hook Tests
```typescript
describe('useChat', () => {
  it('should initialize with empty conversations', () => {
    const { result } = renderHook(() => useChat());
    
    expect(result.current.conversations).toEqual([]);
  });

  it('should handle create conversation', async () => {
    const { result } = renderHook(() => useChat());
    
    await act(async () => {
      const id = await result.current.createConversation('Test');
      expect(id).toBeDefined();
    });
  });
});
```

### 2. Component Tests

**Scope:** React components with mocked services

**Tools:** React Testing Library + Vitest

**Examples:**

```typescript
describe('ChatWindowIntegration', () => {
  it('should render chat window', () => {
    render(<ChatWindowIntegration apiBaseUrl="http://localhost:3000" />);
    
    expect(screen.getByText('Conversations')).toBeInTheDocument();
  });

  it('should send message on form submit', async () => {
    const user = userEvent.setup();
    render(<ChatWindowIntegration apiBaseUrl="http://localhost:3000" />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const button = screen.getByRole('button', { name: /send/i });
    
    await user.type(input, 'Hello');
    await user.click(button);
    
    // Message should be cleared after send
    expect(input).toHaveValue('');
  });

  it('should display error message', async () => {
    const { rerender } = render(
      <ChatWindowIntegration apiBaseUrl="http://invalid-url" />
    );
    
    // Trigger an error
    await act(async () => {
      // Error should be displayed
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
```

### 3. Integration Tests

**Scope:** Services working together with stores

**Tools:** Vitest + custom test utilities

**Examples:**

```typescript
describe('Service Integration', () => {
  it('should sync ChatService updates with ChatStore', async () => {
    const chatService = new ChatService();
    const chatStore = useChatStore();
    
    // Send message via service
    await chatService.sendMessage('conv-1', 'Hello');
    
    // Verify store is updated
    const messages = chatStore.getConversationMessages('conv-1');
    expect(messages.length).toBeGreaterThan(0);
  });

  it('should update StatsStore when sending message', async () => {
    const chatService = new ChatService();
    const statsStore = useStatsStore();
    
    const initialTokens = statsStore.totalTokens;
    
    await chatService.sendMessage('conv-1', 'Hello');
    
    // Verify stats are updated
    expect(statsStore.totalTokens).toBeGreaterThan(initialTokens);
  });

  it('should respect ContextStore token limits', async () => {
    const contextService = new ContextService();
    const contextStore = useContextStore();
    
    contextStore.setMaxTokens(100);
    
    // Try to add file that exceeds limit
    await expect(
      contextService.addFileToContext('/repo', 'large-file.js')
    ).rejects.toThrow('exceed');
  });
});
```

### 4. API Integration Tests

**Scope:** API clients with mock server

**Tools:** MSW (Mock Service Worker) + Vitest

**Setup:**
```typescript
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.post('/api/chat/message', () => {
    return HttpResponse.json({
      id: '1',
      content: 'Hello!',
      tokens: 10,
      model: 'claude-opus',
      responseTime: 100,
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('ChatService with API', () => {
  it('should send message and receive response', async () => {
    const service = new ChatService('http://localhost:3000/api');
    
    const response = await service.sendMessage('conv-1', 'Hello');
    
    expect(response).toBeDefined();
    expect(response.content).toBe('Hello!');
  });

  it('should handle API errors', async () => {
    server.use(
      http.post('/api/chat/message', () => {
        return HttpResponse.json(
          { error: 'Rate limited' },
          { status: 429 }
        );
      })
    );

    const service = new ChatService('http://localhost:3000/api');
    
    await expect(
      service.sendMessage('conv-1', 'Hello')
    ).rejects.toThrow();
  });
});
```

### 5. E2E Tests

**Scope:** Full workflow with real backend

**Tools:** Playwright

**Examples:**

```typescript
test('user workflow: chat with context', async ({ page }) => {
  // Navigate to app
  await page.goto('http://localhost:5173');
  
  // Load repository
  await page.fill('[data-testid=repo-path]', '/path/to/repo');
  await page.click('[data-testid=load-repo]');
  await page.waitForSelector('[data-testid=file-tree]');
  
  // Add files to context
  await page.click('[data-testid=search-input]');
  await page.fill('[data-testid=search-input]', 'component');
  await page.click('[data-testid=search-add]');
  
  // Create conversation
  await page.click('[data-testid=new-chat]');
  
  // Send message
  await page.fill('[data-testid=message-input]', 'Review this code');
  await page.click('[data-testid=send-button]');
  
  // Verify response
  await page.waitForSelector('[data-testid=message-assistant]');
  expect(page.locator('[data-testid=message-assistant]')).toContainText('Review');
});
```

## Mock Strategy

### API Mocking (MSW)

Use Mock Service Worker for API integration tests:

```typescript
// handlers.ts
export const handlers = [
  http.get('/api/chat/conversations', () => {
    return HttpResponse.json([
      { id: '1', title: 'Chat 1' },
      { id: '2', title: 'Chat 2' },
    ]);
  }),

  http.post('/api/chat/message', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: crypto.randomUUID(),
      content: `Echo: ${body.message}`,
      tokens: 10,
      model: 'claude-opus',
      responseTime: 50,
    });
  }),
];
```

### Store Mocking

Mock Zustand stores in component tests:

```typescript
jest.mock('@devforge/stores', () => ({
  useChatStore: () => ({
    conversations: [],
    activeConversationId: 'test-id',
    addMessage: jest.fn(),
    createConversation: jest.fn(() => 'new-id'),
  }),
}));
```

### Service Mocking

Mock services when testing components:

```typescript
jest.mock('@devforge/services', () => ({
  ChatService: jest.fn(() => ({
    sendMessage: jest.fn(() => 
      Promise.resolve({
        content: 'Test response',
        tokens: 10,
      })
    ),
    createConversation: jest.fn(() => Promise.resolve('conv-id')),
  })),
}));
```

## Test Organization

```
tests/
├── unit/
│   ├── api/
│   │   ├── client.test.ts
│   │   ├── github.test.ts
│   │   ├── repo.test.ts
│   │   ├── hf.test.ts
│   │   └── config.test.ts
│   ├── services/
│   │   ├── chatService.test.ts
│   │   ├── repoService.test.ts
│   │   ├── configService.test.ts
│   │   └── contextService.test.ts
│   └── hooks/
│       ├── useChat.test.ts
│       ├── useRepository.test.ts
│       ├── useConfig.test.ts
│       └── useContext.test.ts
├── components/
│   ├── ChatWindowIntegration.test.tsx
│   ├── RepositoryBrowserIntegration.test.tsx
│   ├── ConfigurationPanelIntegration.test.tsx
│   └── ContextManagerIntegration.test.tsx
├── integration/
│   ├── service-store-sync.test.ts
│   ├── api-service-integration.test.ts
│   └── complete-workflow.test.ts
├── e2e/
│   ├── chat.spec.ts
│   ├── repository.spec.ts
│   ├── configuration.spec.ts
│   └── context.spec.ts
└── fixtures/
    ├── mockData.ts
    ├── handlers.ts
    └── testUtils.ts
```

## Coverage Targets

| Category | Target | Priority |
|----------|--------|----------|
| API Clients | 90%+ | High |
| Services | 85%+ | High |
| Hooks | 80%+ | Medium |
| Components | 75%+ | Medium |
| Integration | 70%+ | Medium |
| Overall | 85%+ | High |

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm run test:unit
      - run: npm run test:coverage

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm run dev &
      - run: npm run test:e2e
```

## Test Data

### Fixtures

```typescript
// fixtures/mockData.ts
export const mockConversation = {
  id: 'conv-1',
  title: 'Test Chat',
  createdAt: new Date(),
  updatedAt: new Date(),
};

export const mockMessage = {
  id: 'msg-1',
  role: 'user' as const,
  content: 'Hello',
  timestamp: new Date(),
  tokens: 10,
};

export const mockRepository = {
  id: 'repo-1',
  name: 'devforge',
  path: '/home/user/devforge',
  isGit: true,
  branch: 'main',
};
```

## Testing Checklist

- [ ] All API endpoints have test coverage
- [ ] All services have integration tests
- [ ] All hooks have behavior tests
- [ ] All components render correctly
- [ ] Error scenarios are tested
- [ ] Loading states are tested
- [ ] Network failures are handled
- [ ] Store updates are verified
- [ ] E2E workflows pass
- [ ] Coverage targets met

## Running Tests

```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Coverage report
npm run test:coverage

# Watch mode
npm run test:watch

# All tests
npm run test
```

## Best Practices

1. **Test Behavior, Not Implementation**
   - Test what users see and do
   - Don't test internal implementation details

2. **Use Realistic Data**
   - Use fixtures that resemble real data
   - Mock external APIs consistently

3. **Test Error Paths**
   - Test both success and failure cases
   - Verify error messages are user-friendly

4. **Keep Tests Fast**
   - Mock expensive operations
   - Use in-memory databases when possible
   - Parallelize test execution

5. **Maintain Tests**
   - Keep tests simple and readable
   - Update tests when behavior changes
   - Remove dead test code

6. **Document Complex Tests**
   - Add comments explaining the test purpose
   - Document any unusual setup/teardown

## Continuous Improvement

1. Monitor test execution time
2. Track coverage trends
3. Review failed tests regularly
4. Refactor flaky tests
5. Add tests for reported bugs
6. Keep test dependencies updated

## Additional Resources

- [Testing Library Docs](https://testing-library.com/)
- [Vitest Docs](https://vitest.dev/)
- [MSW Documentation](https://mswjs.io/)
- [Playwright Docs](https://playwright.dev/)
