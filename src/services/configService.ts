/**
 * Configuration Service - integrates ConfigStore with API calls
 */

import { useConfigStore } from '../stores/configStore';
import { ConfigClient } from '../api/config';
import type { APIKey, Model, Provider, FeatureFlag, UserPreferences } from '../api/config';

export class ConfigService {
  private configClient: ConfigClient;
  private configStore: ReturnType<typeof useConfigStore>;

  constructor(apiBaseUrl: string = 'http://localhost:3000/api') {
    this.configClient = new ConfigClient(apiBaseUrl);
    this.configStore = useConfigStore();
  }

  // API Keys Management
  async loadAPIKeys(): Promise<APIKey[]> {
    try {
      const response = await this.configClient.listAPIKeys();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to load API keys: ${error}`);
    }
  }

  async createAPIKey(provider: string, keyValue: string): Promise<APIKey | null> {
    try {
      const response = await this.configClient.createAPIKey(provider, keyValue);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to create API key');
      }

      return response.data;
    } catch (error) {
      throw new Error(`Failed to create API key: ${error}`);
    }
  }

  async validateAPIKey(provider: string, keyValue: string): Promise<boolean> {
    try {
      const response = await this.configClient.validateAPIKey(provider, keyValue);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data?.valid || false;
    } catch (error) {
      throw new Error(`Failed to validate API key: ${error}`);
    }
  }

  async deleteAPIKey(keyId: string): Promise<boolean> {
    try {
      const response = await this.configClient.deleteAPIKey(keyId);

      if (response.error || !response.data?.success) {
        throw new Error(response.error || 'Failed to delete API key');
      }

      return true;
    } catch (error) {
      throw new Error(`Failed to delete API key: ${error}`);
    }
  }

  // Models Management
  async loadModels(): Promise<Model[]> {
    try {
      const response = await this.configClient.listModels();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to load models: ${error}`);
    }
  }

  async getModel(modelId: string): Promise<Model | null> {
    try {
      const response = await this.configClient.getModel(modelId);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to get model');
      }

      return response.data;
    } catch (error) {
      throw new Error(`Failed to get model: ${error}`);
    }
  }

  async createModel(model: Omit<Model, 'id'>): Promise<Model | null> {
    try {
      const response = await this.configClient.createModel(model);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to create model');
      }

      return response.data;
    } catch (error) {
      throw new Error(`Failed to create model: ${error}`);
    }
  }

  async updateModel(modelId: string, updates: Partial<Model>): Promise<Model | null> {
    try {
      const response = await this.configClient.updateModel(modelId, updates);

      if (response.error || !response.data) {
        throw new Error(response.error || 'Failed to update model');
      }

      return response.data;
    } catch (error) {
      throw new Error(`Failed to update model: ${error}`);
    }
  }

  async deleteModel(modelId: string): Promise<boolean> {
    try {
      const response = await this.configClient.deleteModel(modelId);

      if (response.error || !response.data?.success) {
        throw new Error(response.error || 'Failed to delete model');
      }

      return true;
    } catch (error) {
      throw new Error(`Failed to delete model: ${error}`);
    }
  }

  async getModelsByProvider(provider: string): Promise<Model[]> {
    try {
      const response = await this.configClient.getModelsByProvider(provider);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    } catch (error) {
      throw new Error(`Failed to get models by provider: ${error}`);
    }
  }

  // Providers Management
  async loadProviders(): Promise<Provider[]> {
    try {
      const response = await this.configClient.listProviders();

      if (response.error) {
        throw new Error(response.error);
      }

      const providers = response.data || [];
      providers.forEach((provider) => {
        this.configStore.addProvider({
          id: provider.id,
          name: provider.name,
          apiKey: '',
          baseUrl: provider.apiBaseUrl,
          isActive: provider.isActive,
          rateLimit: provider.rateLimit,
        });
      });

      return providers;
    } catch (error) {
      throw new Error(`Failed to load providers: ${error}`);
    }
  }

  async testProviderConnection(providerId: string): Promise<boolean> {
    try {
      const response = await this.configClient.testProviderConnection(providerId);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data?.connected || false;
    } catch (error) {
      throw new Error(`Failed to test provider connection: ${error}`);
    }
  }

  // Feature Flags Management
  async loadFeatureFlags(): Promise<FeatureFlag[]> {
    try {
      const response = await this.configClient.listFeatureFlags();

      if (response.error) {
        throw new Error(response.error);
      }

      const flags = response.data || [];
      flags.forEach((flag) => {
        this.configStore.setFeatureFlag(flag.name, flag.enabled);
      });

      return flags;
    } catch (error) {
      throw new Error(`Failed to load feature flags: ${error}`);
    }
  }

  async isFeatureEnabled(flagName: string): Promise<boolean> {
    try {
      const response = await this.configClient.isFeatureEnabled(flagName);

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data?.enabled || false;
    } catch (error) {
      throw new Error(`Failed to check feature flag: ${error}`);
    }
  }

  async updateFeatureFlag(flagName: string, enabled: boolean): Promise<boolean> {
    try {
      const response = await this.configClient.updateFeatureFlag(flagName, { enabled });

      if (response.error) {
        throw new Error(response.error);
      }

      this.configStore.setFeatureFlag(flagName, enabled);
      return true;
    } catch (error) {
      throw new Error(`Failed to update feature flag: ${error}`);
    }
  }

  // Preferences
  async loadUserPreferences(): Promise<UserPreferences | null> {
    try {
      const response = await this.configClient.getUserPreferences();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || null;
    } catch (error) {
      throw new Error(`Failed to load user preferences: ${error}`);
    }
  }

  async updateUserPreferences(prefs: Partial<UserPreferences>): Promise<boolean> {
    try {
      const response = await this.configClient.updateUserPreferences(prefs);

      if (response.error) {
        throw new Error(response.error);
      }

      return true;
    } catch (error) {
      throw new Error(`Failed to update user preferences: ${error}`);
    }
  }

  // System Status
  async getSystemStatus(): Promise<any> {
    try {
      const response = await this.configClient.getSystemStatus();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || null;
    } catch (error) {
      throw new Error(`Failed to get system status: ${error}`);
    }
  }

  async getAppVersion(): Promise<{ version: string; buildTime: string } | null> {
    try {
      const response = await this.configClient.getVersion();

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || null;
    } catch (error) {
      throw new Error(`Failed to get app version: ${error}`);
    }
  }

  setBaseUrl(url: string): void {
    this.configClient.setBaseUrl(url);
  }

  setAuthToken(token: string): void {
    this.configClient.setAuthHeader(token, 'Bearer');
  }
}
