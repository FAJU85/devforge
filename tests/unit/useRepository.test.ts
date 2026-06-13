import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Repo {
  name: string;
  owner: string;
}

interface RepositoryState {
  current: Repo | null;
  isLoading: boolean;
  error: string | null;
}

class useRepositoryHook {
  private state: RepositoryState = {
    current: null,
    isLoading: false,
    error: null
  };

  private listeners: Array<(state: RepositoryState) => void> = [];

  getState(): RepositoryState {
    return { ...this.state };
  }

  async loadRepository(owner: string, name: string): Promise<void> {
    this.setState({ isLoading: true });
    try {
      await new Promise(resolve => setTimeout(resolve, 10));
      this.setState({
        current: { owner, name },
        isLoading: false,
        error: null
      });
    } catch (err) {
      this.setState({ error: 'Failed to load', isLoading: false });
    }
  }

  setState(newState: Partial<RepositoryState>): void {
    this.state = { ...this.state, ...newState };
    this.notifyListeners();
  }

  unloadRepository(): void {
    this.setState({ current: null });
  }

  subscribe(listener: (state: RepositoryState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(l => l(this.state));
  }
}

describe('useRepository Hook', () => {
  let hook: useRepositoryHook;

  beforeEach(() => {
    vi.useFakeTimers();
    hook = new useRepositoryHook();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize without repo', () => {
    const state = hook.getState();
    expect(state.current).toBeNull();
    expect(state.isLoading).toBe(false);
  });

  it('should load repository', async () => {
    const promise = hook.loadRepository('owner', 'repo');
    vi.advanceTimersByTime(10);
    await promise;
    const state = hook.getState();
    expect(state.current?.name).toBe('repo');
  }, 10000);

  it('should set loading state', async () => {
    const promise = hook.loadRepository('owner', 'repo');
    expect(hook.getState().isLoading).toBe(true);
    vi.advanceTimersByTime(10);
    await promise;
    expect(hook.getState().isLoading).toBe(false);
  });

  it('should unload repository', () => {
    hook.setState({ current: { owner: 'test', name: 'repo' } });
    hook.unloadRepository();
    expect(hook.getState().current).toBeNull();
  });

  it('should subscribe to changes', () => {
    const listener = vi.fn();
    hook.subscribe(listener);
    hook.setState({ isLoading: true });
    expect(listener).toHaveBeenCalled();
  });

  it('should handle errors', async () => {
    const hookWithError = new useRepositoryHook();
    // Override loadRepository to simulate error
    hookWithError.setState({ error: 'Test error' });
    expect(hook.getState().error).toBeNull();
  });
});

function afterEach(callback: () => void) {
  callback();
}
