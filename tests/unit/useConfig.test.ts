import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ConfigState {
  apiKey: string;
  provider: string;
  isDirty: boolean;
}

class useConfigHook {
  private state: ConfigState = {
    apiKey: '',
    provider: 'openai',
    isDirty: false
  };

  private listeners: Array<(state: ConfigState) => void> = [];

  getState(): ConfigState {
    return { ...this.state };
  }

  setState(newState: Partial<ConfigState>): void {
    this.state = { ...this.state, ...newState };
    this.notifyListeners();
  }

  updateApiKey(key: string): void {
    this.setState({ apiKey: key, isDirty: true });
  }

  updateProvider(provider: string): void {
    this.setState({ provider, isDirty: true });
  }

  resetChanges(): void {
    this.setState({ isDirty: false });
  }

  subscribe(listener: (state: ConfigState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    this.listeners.forEach(l => l(this.state));
  }

  async saveConfig(): Promise<boolean> {
    if (!this.state.apiKey) return false;
    this.resetChanges();
    return true;
  }
}

describe('useConfig Hook', () => {
  let hook: useConfigHook;

  beforeEach(() => {
    hook = new useConfigHook();
  });

  it('should initialize with defaults', () => {
    const state = hook.getState();
    expect(state.provider).toBe('openai');
    expect(state.isDirty).toBe(false);
  });

  it('should update API key', () => {
    hook.updateApiKey('test-key');
    expect(hook.getState().apiKey).toBe('test-key');
  });

  it('should mark as dirty on update', () => {
    hook.updateApiKey('key');
    expect(hook.getState().isDirty).toBe(true);
  });

  it('should update provider', () => {
    hook.updateProvider('anthropic');
    expect(hook.getState().provider).toBe('anthropic');
  });

  it('should reset changes', () => {
    hook.updateApiKey('key');
    hook.resetChanges();
    expect(hook.getState().isDirty).toBe(false);
  });

  it('should subscribe to changes', () => {
    const listener = vi.fn();
    hook.subscribe(listener);
    hook.updateApiKey('key');
    expect(listener).toHaveBeenCalled();
  });

  it('should unsubscribe', () => {
    const listener = vi.fn();
    const unsubscribe = hook.subscribe(listener);
    unsubscribe();
    hook.updateApiKey('key');
    expect(listener).not.toHaveBeenCalled();
  });

  it('should save config', async () => {
    hook.updateApiKey('valid-key');
    const result = await hook.saveConfig();
    expect(result).toBe(true);
    expect(hook.getState().isDirty).toBe(false);
  });

  it('should fail save without key', async () => {
    const result = await hook.saveConfig();
    expect(result).toBe(false);
  });
});
