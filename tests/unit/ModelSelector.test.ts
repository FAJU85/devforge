import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Model {
  id: string;
  name: string;
  provider: string;
  contextWindow: number;
  costPer1kTokens: number;
}

class ModelSelector {
  private models: Model[] = [];
  private selectedModel: Model | null = null;
  private onSelect: ((model: Model) => void) | null = null;

  constructor(models: Model[] = []) {
    this.models = models;
  }

  addModel(model: Model): void {
    if (!this.models.find(m => m.id === model.id)) {
      this.models.push(model);
    }
  }

  getModels(): Model[] {
    return this.models;
  }

  selectModel(modelId: string): void {
    const model = this.models.find(m => m.id === modelId);
    if (model) {
      this.selectedModel = model;
      this.onSelect?.(model);
    }
  }

  getSelectedModel(): Model | null {
    return this.selectedModel;
  }

  filterByProvider(provider: string): Model[] {
    return this.models.filter(m => m.provider === provider);
  }

  filterByContextWindow(minWindow: number): Model[] {
    return this.models.filter(m => m.contextWindow >= minWindow);
  }

  sortByCost(): Model[] {
    return [...this.models].sort((a, b) => a.costPer1kTokens - b.costPer1kTokens);
  }

  onModelSelect(callback: (model: Model) => void): void {
    this.onSelect = callback;
  }

  getModelCount(): number {
    return this.models.length;
  }
}

describe('ModelSelector', () => {
  let selector: ModelSelector;
  const mockModels: Model[] = [
    { id: 'gpt-4', name: 'GPT-4', provider: 'openai', contextWindow: 8192, costPer1kTokens: 0.03 },
    { id: 'claude-opus', name: 'Claude Opus', provider: 'anthropic', contextWindow: 100000, costPer1kTokens: 0.015 },
    { id: 'llama-70b', name: 'Llama 70B', provider: 'meta', contextWindow: 4096, costPer1kTokens: 0.001 }
  ];

  beforeEach(() => {
    selector = new ModelSelector(mockModels);
  });

  it('should initialize with models', () => {
    expect(selector.getModelCount()).toBe(3);
  });

  it('should get all models', () => {
    const models = selector.getModels();
    expect(models).toHaveLength(3);
  });

  it('should add new model', () => {
    const newModel: Model = {
      id: 'gpt-3.5',
      name: 'GPT-3.5',
      provider: 'openai',
      contextWindow: 4096,
      costPer1kTokens: 0.0015
    };
    selector.addModel(newModel);
    expect(selector.getModelCount()).toBe(4);
  });

  it('should not add duplicate models', () => {
    const initialCount = selector.getModelCount();
    selector.addModel(mockModels[0]);
    expect(selector.getModelCount()).toBe(initialCount);
  });

  it('should select model', () => {
    selector.selectModel('gpt-4');
    const selected = selector.getSelectedModel();
    expect(selected?.id).toBe('gpt-4');
  });

  it('should call onSelect callback', () => {
    const callback = vi.fn();
    selector.onModelSelect(callback);
    selector.selectModel('claude-opus');
    expect(callback).toHaveBeenCalledWith(mockModels[1]);
  });

  it('should filter by provider', () => {
    const openaiModels = selector.filterByProvider('openai');
    expect(openaiModels).toHaveLength(1);
    expect(openaiModels[0].id).toBe('gpt-4');
  });

  it('should filter by context window', () => {
    const largeWindow = selector.filterByContextWindow(8000);
    expect(largeWindow).toHaveLength(2);
  });

  it('should sort by cost', () => {
    const sorted = selector.sortByCost();
    expect(sorted[0].id).toBe('llama-70b');
    expect(sorted[sorted.length - 1].id).toBe('gpt-4');
  });

  it('should handle invalid model selection', () => {
    selector.selectModel('invalid-id');
    expect(selector.getSelectedModel()).toBeNull();
  });

  it('should return null when no model selected', () => {
    expect(selector.getSelectedModel()).toBeNull();
  });

  it('should maintain selection after adding model', () => {
    selector.selectModel('gpt-4');
    const newModel: Model = {
      id: 'new-model',
      name: 'New',
      provider: 'test',
      contextWindow: 2048,
      costPer1kTokens: 0.01
    };
    selector.addModel(newModel);
    expect(selector.getSelectedModel()?.id).toBe('gpt-4');
  });

  it('should handle multiple selections', () => {
    const callback = vi.fn();
    selector.onModelSelect(callback);
    selector.selectModel('gpt-4');
    selector.selectModel('claude-opus');
    expect(callback).toHaveBeenCalledTimes(2);
    expect(selector.getSelectedModel()?.id).toBe('claude-opus');
  });

  it('should filter with no matches', () => {
    const filtered = selector.filterByProvider('nonexistent');
    expect(filtered).toHaveLength(0);
  });
});
