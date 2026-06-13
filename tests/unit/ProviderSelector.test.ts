import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Provider {
  id: string;
  name: string;
  apiUrl: string;
  isAvailable: boolean;
}

class ProviderSelector {
  private providers: Provider[] = [];
  private selectedProvider: Provider | null = null;
  private onSelect: ((provider: Provider) => void) | null = null;

  addProvider(provider: Provider): void {
    if (!this.providers.find(p => p.id === provider.id)) {
      this.providers.push(provider);
    }
  }

  getProviders(): Provider[] {
    return [...this.providers];
  }

  selectProvider(providerId: string): boolean {
    const provider = this.providers.find(p => p.id === providerId);
    if (provider && provider.isAvailable) {
      this.selectedProvider = provider;
      this.onSelect?.(provider);
      return true;
    }
    return false;
  }

  getSelectedProvider(): Provider | null {
    return this.selectedProvider;
  }

  getAvailableProviders(): Provider[] {
    return this.providers.filter(p => p.isAvailable);
  }

  onProviderSelect(callback: (provider: Provider) => void): void {
    this.onSelect = callback;
  }

  removeProvider(providerId: string): boolean {
    const index = this.providers.findIndex(p => p.id === providerId);
    if (index > -1) {
      this.providers.splice(index, 1);
      return true;
    }
    return false;
  }
}

describe('ProviderSelector', () => {
  let selector: ProviderSelector;
  const mockProviders: Provider[] = [
    { id: 'openai', name: 'OpenAI', apiUrl: 'https://api.openai.com', isAvailable: true },
    { id: 'anthropic', name: 'Anthropic', apiUrl: 'https://api.anthropic.com', isAvailable: true },
    { id: 'groq', name: 'Groq', apiUrl: 'https://api.groq.com', isAvailable: false }
  ];

  beforeEach(() => {
    selector = new ProviderSelector();
    mockProviders.forEach(p => selector.addProvider(p));
  });

  it('should add providers', () => {
    expect(selector.getProviders()).toHaveLength(3);
  });

  it('should select available provider', () => {
    expect(selector.selectProvider('openai')).toBe(true);
    expect(selector.getSelectedProvider()?.id).toBe('openai');
  });

  it('should not select unavailable provider', () => {
    expect(selector.selectProvider('groq')).toBe(false);
  });

  it('should get available providers', () => {
    const available = selector.getAvailableProviders();
    expect(available).toHaveLength(2);
    expect(available.every(p => p.isAvailable)).toBe(true);
  });

  it('should call onSelect callback', () => {
    const callback = vi.fn();
    selector.onProviderSelect(callback);
    selector.selectProvider('openai');
    expect(callback).toHaveBeenCalledWith(mockProviders[0]);
  });

  it('should remove provider', () => {
    expect(selector.removeProvider('groq')).toBe(true);
    expect(selector.getProviders()).toHaveLength(2);
  });

  it('should not add duplicate providers', () => {
    selector.addProvider(mockProviders[0]);
    expect(selector.getProviders()).toHaveLength(3);
  });
});
