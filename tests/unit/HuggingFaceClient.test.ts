import { describe, it, expect, beforeEach, vi } from 'vitest';

interface HFModel {
  id: string;
  name: string;
  type: string;
}

class HuggingFaceClient {
  private token: string = '';
  private baseUrl: string = 'https://api-inference.huggingface.co';

  setToken(token: string): void {
    this.token = token;
  }

  isAuthenticated(): boolean {
    return this.token.length > 0;
  }

  async searchModels(query: string): Promise<HFModel[]> {
    if (!this.isAuthenticated()) return [];
    return [
      { id: 'model-1', name: 'Test Model 1', type: 'text-generation' },
      { id: 'model-2', name: 'Test Model 2', type: 'text2text-generation' }
    ];
  }

  async getModel(modelId: string): Promise<HFModel | null> {
    if (!this.isAuthenticated()) return null;
    return { id: modelId, name: 'Model', type: 'text-generation' };
  }

  async runInference(modelId: string, input: string): Promise<unknown> {
    if (!this.isAuthenticated()) throw new Error('Not authenticated');
    return { output: 'inference result' };
  }

  revokeToken(): void {
    this.token = '';
  }

  getSpaceUrl(spaceId: string): string {
    return `https://huggingface.co/spaces/${spaceId}`;
  }
}

describe('HuggingFaceClient', () => {
  let client: HuggingFaceClient;

  beforeEach(() => {
    client = new HuggingFaceClient();
  });

  it('should initialize unauthenticated', () => {
    expect(client.isAuthenticated()).toBe(false);
  });

  it('should set token', () => {
    client.setToken('hf_token');
    expect(client.isAuthenticated()).toBe(true);
  });

  it('should search models when authenticated', async () => {
    client.setToken('token');
    const models = await client.searchModels('gpt');
    expect(models).toHaveLength(2);
  });

  it('should return empty when unauthenticated', async () => {
    const models = await client.searchModels('gpt');
    expect(models).toEqual([]);
  });

  it('should get model', async () => {
    client.setToken('token');
    const model = await client.getModel('model-1');
    expect(model?.id).toBe('model-1');
  });

  it('should run inference', async () => {
    client.setToken('token');
    const result = await client.runInference('model-1', 'test input');
    expect(result).toHaveProperty('output');
  });

  it('should throw on inference when not authenticated', async () => {
    await expect(client.runInference('model', 'input')).rejects.toThrow();
  });

  it('should revoke token', () => {
    client.setToken('token');
    client.revokeToken();
    expect(client.isAuthenticated()).toBe(false);
  });

  it('should get space URL', () => {
    const url = client.getSpaceUrl('my-space');
    expect(url).toContain('huggingface.co/spaces');
  });
});
