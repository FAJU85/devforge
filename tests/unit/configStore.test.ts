import { describe, it, expect, beforeEach } from 'vitest';
import { useConfigStore, ProviderConfig, ModelConfig } from '../../src/stores/configStore';

describe('Config Store', () => {
  beforeEach(() => {
    // Reset store state
    useConfigStore.setState({
      providers: [],
      activeProviderId: null,
      models: [],
      activeModelId: null,
      temperature: 0.7,
      maxTokens: 2000,
      topP: 1,
      topK: 0,
      featureFlags: {
        canaryDeployment: false,
        betaFeatures: false,
        autoSave: true,
        diffViewer: true,
        batchOperations: true,
      },
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useConfigStore.getState();
      expect(state.providers).toEqual([]);
      expect(state.activeProviderId).toBeNull();
      expect(state.models).toEqual([]);
      expect(state.activeModelId).toBeNull();
      expect(state.temperature).toBe(0.7);
      expect(state.maxTokens).toBe(2000);
      expect(state.topP).toBe(1);
      expect(state.topK).toBe(0);
    });

    it('should have default feature flags', () => {
      const state = useConfigStore.getState();
      expect(state.featureFlags.autoSave).toBe(true);
      expect(state.featureFlags.diffViewer).toBe(true);
      expect(state.featureFlags.batchOperations).toBe(true);
      expect(state.featureFlags.canaryDeployment).toBe(false);
      expect(state.featureFlags.betaFeatures).toBe(false);
    });
  });

  describe('Provider Management', () => {
    it('should add a provider', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
        apiKey: 'sk-test',
      };

      state.addProvider(provider);

      expect(useConfigStore.getState().providers).toHaveLength(1);
      expect(useConfigStore.getState().providers[0]).toEqual(provider);
    });

    it('should set first provider as active automatically', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };

      state.addProvider(provider);

      expect(useConfigStore.getState().activeProviderId).toBe('openai');
    });

    it('should not change active provider when adding subsequent providers', () => {
      const state = useConfigStore.getState();
      const provider1: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };
      const provider2: ProviderConfig = {
        id: 'anthropic',
        name: 'Anthropic',
        isConfigured: true,
      };

      state.addProvider(provider1);
      state.addProvider(provider2);

      expect(useConfigStore.getState().activeProviderId).toBe('openai');
    });

    it('should update a provider', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: false,
      };

      state.addProvider(provider);
      state.updateProvider('openai', { isConfigured: true, apiKey: 'new-key' });

      const updated = useConfigStore.getState().providers[0];
      expect(updated.isConfigured).toBe(true);
      expect(updated.apiKey).toBe('new-key');
      expect(updated.name).toBe('OpenAI');
    });

    it('should remove a provider', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };

      state.addProvider(provider);
      expect(useConfigStore.getState().providers).toHaveLength(1);

      state.removeProvider('openai');
      expect(useConfigStore.getState().providers).toHaveLength(0);
    });

    it('should clear active provider when removing active provider', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };

      state.addProvider(provider);
      expect(useConfigStore.getState().activeProviderId).toBe('openai');

      state.removeProvider('openai');
      expect(useConfigStore.getState().activeProviderId).toBeNull();
    });

    it('should set active provider', () => {
      const state = useConfigStore.getState();
      const provider1: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };
      const provider2: ProviderConfig = {
        id: 'anthropic',
        name: 'Anthropic',
        isConfigured: true,
      };

      state.addProvider(provider1);
      state.addProvider(provider2);

      state.setActiveProvider('anthropic');
      expect(useConfigStore.getState().activeProviderId).toBe('anthropic');
    });

    it('should get active provider', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };

      state.addProvider(provider);
      const active = state.getActiveProvider();

      expect(active?.id).toBe('openai');
      expect(active?.name).toBe('OpenAI');
    });
  });

  describe('Model Management', () => {
    it('should add a model', () => {
      const state = useConfigStore.getState();
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addModel(model);

      expect(useConfigStore.getState().models).toHaveLength(1);
      expect(useConfigStore.getState().models[0]).toEqual(model);
    });

    it('should set first model as active automatically', () => {
      const state = useConfigStore.getState();
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addModel(model);

      expect(useConfigStore.getState().activeModelId).toBe('gpt-4');
    });

    it('should update a model', () => {
      const state = useConfigStore.getState();
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addModel(model);
      state.updateModel('gpt-4', {
        contextWindow: 16384,
        costPer1kTokens: { input: 0.03, output: 0.06 },
      });

      const updated = useConfigStore.getState().models[0];
      expect(updated.contextWindow).toBe(16384);
      expect(updated.costPer1kTokens?.input).toBe(0.03);
    });

    it('should remove a model', () => {
      const state = useConfigStore.getState();
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addModel(model);
      state.removeModel('gpt-4');

      expect(useConfigStore.getState().models).toHaveLength(0);
    });

    it('should get active model', () => {
      const state = useConfigStore.getState();
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addModel(model);
      const active = state.getActiveModel();

      expect(active?.id).toBe('gpt-4');
      expect(active?.name).toBe('GPT-4');
    });

    it('should get provider models', () => {
      const state = useConfigStore.getState();
      const model1: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };
      const model2: ModelConfig = {
        id: 'gpt-3.5',
        name: 'GPT-3.5',
        provider: 'openai',
        contextWindow: 4096,
      };
      const model3: ModelConfig = {
        id: 'claude-3',
        name: 'Claude 3',
        provider: 'anthropic',
        contextWindow: 100000,
      };

      state.addModel(model1);
      state.addModel(model2);
      state.addModel(model3);

      const openaiModels = state.getProviderModels('openai');
      expect(openaiModels).toHaveLength(2);
      expect(openaiModels[0].provider).toBe('openai');
      expect(openaiModels[1].provider).toBe('openai');

      const anthropicModels = state.getProviderModels('anthropic');
      expect(anthropicModels).toHaveLength(1);
      expect(anthropicModels[0].provider).toBe('anthropic');
    });
  });

  describe('Settings', () => {
    it('should update settings', () => {
      const state = useConfigStore.getState();
      state.updateSettings({
        temperature: 0.5,
        maxTokens: 4000,
        topP: 0.9,
      });

      const updated = useConfigStore.getState();
      expect(updated.temperature).toBe(0.5);
      expect(updated.maxTokens).toBe(4000);
      expect(updated.topP).toBe(0.9);
    });

    it('should preserve other settings when updating partial settings', () => {
      const state = useConfigStore.getState();
      state.updateSettings({ temperature: 0.5 });

      const updated = useConfigStore.getState();
      expect(updated.temperature).toBe(0.5);
      expect(updated.maxTokens).toBe(2000);
      expect(updated.topP).toBe(1);
    });
  });

  describe('Feature Flags', () => {
    it('should set feature flag', () => {
      const state = useConfigStore.getState();
      state.setFeatureFlag('betaFeatures', true);

      expect(useConfigStore.getState().featureFlags.betaFeatures).toBe(true);
    });

    it('should toggle feature flag', () => {
      const state = useConfigStore.getState();
      expect(useConfigStore.getState().featureFlags.betaFeatures).toBe(false);

      state.toggleFeatureFlag('betaFeatures');
      expect(useConfigStore.getState().featureFlags.betaFeatures).toBe(true);

      state.toggleFeatureFlag('betaFeatures');
      expect(useConfigStore.getState().featureFlags.betaFeatures).toBe(false);
    });

    it('should check if feature is enabled', () => {
      const state = useConfigStore.getState();
      expect(state.isFeatureEnabled('autoSave')).toBe(true);
      expect(state.isFeatureEnabled('betaFeatures')).toBe(false);
    });

    it('should return false for non-existent feature flags', () => {
      const state = useConfigStore.getState();
      expect(state.isFeatureEnabled('nonExistentFeature')).toBe(false);
    });

    it('should create new feature flags dynamically', () => {
      const state = useConfigStore.getState();
      state.setFeatureFlag('newFeature', true);

      expect(state.isFeatureEnabled('newFeature')).toBe(true);
    });
  });

  describe('Configuration Validation', () => {
    it('should return false when configuration is empty', () => {
      const state = useConfigStore.getState();
      expect(state.isConfigurationValid()).toBe(false);
    });

    it('should return false when only provider is configured', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };

      state.addProvider(provider);

      expect(state.isConfigurationValid()).toBe(false);
    });

    it('should return false when provider is not configured', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: false,
      };
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addProvider(provider);
      state.addModel(model);

      expect(state.isConfigurationValid()).toBe(false);
    });

    it('should return true when both provider and model are configured', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };
      const model: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };

      state.addProvider(provider);
      state.addModel(model);

      expect(state.isConfigurationValid()).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle updating non-existent provider', () => {
      const state = useConfigStore.getState();
      state.updateProvider('non-existent', { isConfigured: true });

      expect(useConfigStore.getState().providers).toHaveLength(0);
    });

    it('should handle removing non-existent provider', () => {
      const state = useConfigStore.getState();
      state.removeProvider('non-existent');

      expect(useConfigStore.getState().providers).toHaveLength(0);
    });

    it('should handle custom settings in provider', () => {
      const state = useConfigStore.getState();
      const provider: ProviderConfig = {
        id: 'custom',
        name: 'Custom Provider',
        isConfigured: true,
        customSettings: {
          timeout: 30000,
          retries: 3,
          debug: true,
        },
      };

      state.addProvider(provider);
      const added = useConfigStore.getState().providers[0];

      expect(added.customSettings?.timeout).toBe(30000);
      expect(added.customSettings?.retries).toBe(3);
      expect(added.customSettings?.debug).toBe(true);
    });

    it('should handle extreme temperature values', () => {
      const state = useConfigStore.getState();
      state.updateSettings({ temperature: 0.0 });

      expect(useConfigStore.getState().temperature).toBe(0);

      state.updateSettings({ temperature: 2.0 });
      expect(useConfigStore.getState().temperature).toBe(2);
    });

    it('should handle large max token values', () => {
      const state = useConfigStore.getState();
      state.updateSettings({ maxTokens: 1000000 });

      expect(useConfigStore.getState().maxTokens).toBe(1000000);
    });
  });

  describe('Multiple Concurrent Operations', () => {
    it('should handle multiple provider and model operations', () => {
      const state = useConfigStore.getState();

      const provider1: ProviderConfig = {
        id: 'openai',
        name: 'OpenAI',
        isConfigured: true,
      };
      const provider2: ProviderConfig = {
        id: 'anthropic',
        name: 'Anthropic',
        isConfigured: true,
      };

      state.addProvider(provider1);
      state.addProvider(provider2);

      const model1: ModelConfig = {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'openai',
        contextWindow: 8192,
      };
      const model2: ModelConfig = {
        id: 'claude-3',
        name: 'Claude 3',
        provider: 'anthropic',
        contextWindow: 100000,
      };

      state.addModel(model1);
      state.addModel(model2);

      expect(useConfigStore.getState().providers).toHaveLength(2);
      expect(useConfigStore.getState().models).toHaveLength(2);

      state.setActiveProvider('anthropic');
      state.setActiveModel('claude-3');

      expect(useConfigStore.getState().activeProviderId).toBe('anthropic');
      expect(useConfigStore.getState().activeModelId).toBe('claude-3');
    });
  });
});
