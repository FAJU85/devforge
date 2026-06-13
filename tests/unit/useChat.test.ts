import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ChatState {
  messages: Array<{ id: string; role: 'user' | 'assistant'; content: string }>;
  isLoading: boolean;
  error: string | null;
}

class useChatHook {
  private state: ChatState = {
    messages: [],
    isLoading: false,
    error: null
  };
  private listeners: Array<(state: ChatState) => void> = [];

  getState(): ChatState {
    return { ...this.state };
  }

  setState(newState: Partial<ChatState>): void {
    this.state = { ...this.state, ...newState };
    this.notify();
  }

  addMessage(role: 'user' | 'assistant', content: string): void {
    const message = {
      id: `msg-${Date.now()}`,
      role,
      content
    };
    this.setState({
      messages: [...this.state.messages, message]
    });
  }

  clearMessages(): void {
    this.setState({ messages: [] });
  }

  setLoading(isLoading: boolean): void {
    this.setState({ isLoading });
  }

  setError(error: string | null): void {
    this.setState({ error });
  }

  async sendMessage(content: string): Promise<void> {
    this.addMessage('user', content);
    this.setLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 100));
      this.addMessage('assistant', 'Response to: ' + content);
    } catch (err) {
      this.setError('Failed to send message');
    } finally {
      this.setLoading(false);
    }
  }

  subscribe(listener: (state: ChatState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  getMessageCount(): number {
    return this.state.messages.length;
  }

  isLoading(): boolean {
    return this.state.isLoading;
  }

  hasError(): boolean {
    return this.state.error !== null;
  }
}

describe('useChat Hook', () => {
  let hook: useChatHook;

  beforeEach(() => {
    hook = new useChatHook();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize with empty state', () => {
    const state = hook.getState();
    expect(state.messages).toHaveLength(0);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should add message', () => {
    hook.addMessage('user', 'Hello');
    expect(hook.getMessageCount()).toBe(1);
  });

  it('should add multiple messages', () => {
    hook.addMessage('user', 'Hello');
    hook.addMessage('assistant', 'Hi there');
    hook.addMessage('user', 'How are you?');
    expect(hook.getMessageCount()).toBe(3);
  });

  it('should clear messages', () => {
    hook.addMessage('user', 'Hello');
    hook.clearMessages();
    expect(hook.getMessageCount()).toBe(0);
  });

  it('should set loading state', () => {
    hook.setLoading(true);
    expect(hook.isLoading()).toBe(true);
  });

  it('should set error', () => {
    hook.setError('Connection failed');
    expect(hook.hasError()).toBe(true);
  });

  it('should clear error', () => {
    hook.setError('Error');
    hook.setError(null);
    expect(hook.hasError()).toBe(false);
  });

  it('should send message', async () => {
    await hook.sendMessage('Hello');
    vi.advanceTimersByTime(100);

    expect(hook.getMessageCount()).toBe(2);
    const state = hook.getState();
    expect(state.messages[0].role).toBe('user');
    expect(state.messages[1].role).toBe('assistant');
  });

  it('should handle loading during send', async () => {
    const promise = hook.sendMessage('Test');
    expect(hook.isLoading()).toBe(true);

    vi.advanceTimersByTime(100);
    await promise;

    expect(hook.isLoading()).toBe(false);
  });

  it('should subscribe to state changes', () => {
    const listener = vi.fn();
    hook.subscribe(listener);
    hook.addMessage('user', 'Hello');
    expect(listener).toHaveBeenCalled();
  });

  it('should unsubscribe from state changes', () => {
    const listener = vi.fn();
    const unsubscribe = hook.subscribe(listener);
    unsubscribe();
    hook.addMessage('user', 'Hello');
    expect(listener).not.toHaveBeenCalled();
  });

  it('should preserve message order', () => {
    hook.addMessage('user', 'First');
    hook.addMessage('assistant', 'Response');
    hook.addMessage('user', 'Second');

    const state = hook.getState();
    expect(state.messages[0].content).toBe('First');
    expect(state.messages[1].content).toBe('Response');
    expect(state.messages[2].content).toBe('Second');
  });

  it('should handle concurrent sends', async () => {
    const promise1 = hook.sendMessage('Message 1');
    const promise2 = hook.sendMessage('Message 2');

    vi.advanceTimersByTime(100);
    await Promise.all([promise1, promise2]);

    expect(hook.getMessageCount()).toBe(4); // 2 user + 2 assistant
  });
});

function afterEach(callback: () => void) {
  callback();
}
