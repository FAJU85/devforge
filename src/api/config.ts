/**
 * Configuration API Client - DevForge configuration management
 */

import { ApiClient, ApiResponse, ApiConfig } from './client';

export interface AppConfig {
  version: string;
  environment: 'development' | 'staging' | 'production';
  apiUrl: string;
  wsUrl?: string;
  features: Record<string, boolean>;
  settings: Record<string, any>;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  layout: string;
  fontSize: number;
  autoSave: boolean;
  notifications: boolean;
  analytics: boolean;
}

export interface APIKey {
  id: string;
  provider: string;
  keyType: string;
  createdAt: string;
  lastUsedAt?: string;
  expiresAt?: string;
  active: boolean;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  contextWindow: number;
  costPer1kTokens: number;
  costOutput?: number;
  description?: string;
  capabilities: string[];
  active: boolean;
}

export interface Provider {
  id: string;
  name: string;
  apiBaseUrl: string;
  isActive: boolean;
  models: string[];
  rateLimit?: number;
  description?: string;
}

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  rolloutPercentage?: number;
  description?: string;
  targetEnvironments: string[];
}

export class ConfigClient extends ApiClient {
  constructor(baseUrl: string = 'http://localhost:3000/api') {
    const config: ApiConfig = {
      baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    super(config);
  }

  // App Configuration
  async getAppConfig(): Promise<ApiResponse<AppConfig>> {
    return this.get<AppConfig>('/config/app');
  }

  async updateAppConfig(config: Partial<AppConfig>): Promise<ApiResponse<AppConfig>> {
    return this.patch<AppConfig>('/config/app', config);
  }

  // User Preferences
  async getUserPreferences(): Promise<ApiResponse<UserPreferences>> {
    return this.get<UserPreferences>('/config/preferences');
  }

  async updateUserPreferences(
    preferences: Partial<UserPreferences>
  ): Promise<ApiResponse<UserPreferences>> {
    return this.patch<UserPreferences>('/config/preferences', preferences);
  }

  async resetUserPreferences(): Promise<ApiResponse<UserPreferences>> {
    return this.post<UserPreferences>('/config/preferences/reset', {});
  }

  // API Keys
  async listAPIKeys(): Promise<ApiResponse<APIKey[]>> {
    return this.get<APIKey[]>('/config/api-keys');
  }

  async createAPIKey(
    provider: string,
    keyValue: string
  ): Promise<ApiResponse<APIKey>> {
    return this.post<APIKey>('/config/api-keys', {
      provider,
      keyValue,
    });
  }

  async updateAPIKey(
    keyId: string,
    updates: Partial<APIKey>
  ): Promise<ApiResponse<APIKey>> {
    return this.patch<APIKey>(`/config/api-keys/${keyId}`, updates);
  }

  async deleteAPIKey(keyId: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.post<{ success: boolean }>(`/config/api-keys/${keyId}/delete`, {});
  }

  async validateAPIKey(provider: string, keyValue: string): Promise<ApiResponse<{ valid: boolean }>> {
    return this.post<{ valid: boolean }>('/config/api-keys/validate', {
      provider,
      keyValue,
    });
  }

  // Models
  async listModels(): Promise<ApiResponse<Model[]>> {
    return this.get<Model[]>('/config/models');
  }

  async getModel(modelId: string): Promise<ApiResponse<Model>> {
    return this.get<Model>(`/config/models/${modelId}`);
  }

  async createModel(model: Omit<Model, 'id'>): Promise<ApiResponse<Model>> {
    return this.post<Model>('/config/models', model);
  }

  async updateModel(modelId: string, updates: Partial<Model>): Promise<ApiResponse<Model>> {
    return this.patch<Model>(`/config/models/${modelId}`, updates);
  }

  async deleteModel(modelId: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.post<{ success: boolean }>(`/config/models/${modelId}/delete`, {});
  }

  async getModelsByProvider(provider: string): Promise<ApiResponse<Model[]>> {
    return this.get<Model[]>(`/config/models?provider=${encodeURIComponent(provider)}`);
  }

  // Providers
  async listProviders(): Promise<ApiResponse<Provider[]>> {
    return this.get<Provider[]>('/config/providers');
  }

  async getProvider(providerId: string): Promise<ApiResponse<Provider>> {
    return this.get<Provider>(`/config/providers/${providerId}`);
  }

  async createProvider(provider: Omit<Provider, 'id'>): Promise<ApiResponse<Provider>> {
    return this.post<Provider>('/config/providers', provider);
  }

  async updateProvider(
    providerId: string,
    updates: Partial<Provider>
  ): Promise<ApiResponse<Provider>> {
    return this.patch<Provider>(`/config/providers/${providerId}`, updates);
  }

  async deleteProvider(providerId: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.post<{ success: boolean }>(`/config/providers/${providerId}/delete`, {});
  }

  async testProviderConnection(providerId: string): Promise<ApiResponse<{ connected: boolean }>> {
    return this.post<{ connected: boolean }>(`/config/providers/${providerId}/test`, {});
  }

  // Feature Flags
  async listFeatureFlags(): Promise<ApiResponse<FeatureFlag[]>> {
    return this.get<FeatureFlag[]>('/config/features');
  }

  async getFeatureFlag(flagName: string): Promise<ApiResponse<FeatureFlag>> {
    return this.get<FeatureFlag>(`/config/features/${encodeURIComponent(flagName)}`);
  }

  async updateFeatureFlag(
    flagName: string,
    updates: Partial<FeatureFlag>
  ): Promise<ApiResponse<FeatureFlag>> {
    return this.patch<FeatureFlag>(`/config/features/${encodeURIComponent(flagName)}`, updates);
  }

  async isFeatureEnabled(flagName: string): Promise<ApiResponse<{ enabled: boolean }>> {
    return this.get<{ enabled: boolean }>(
      `/config/features/${encodeURIComponent(flagName)}/enabled`
    );
  }

  // System Health
  async getSystemStatus(): Promise<ApiResponse<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    timestamp: string;
    services: Record<string, { status: string; latency?: number }>;
  }>> {
    return this.get<{
      status: 'healthy' | 'degraded' | 'unhealthy';
      timestamp: string;
      services: Record<string, { status: string; latency?: number }>;
    }>('/config/status');
  }

  async getVersion(): Promise<ApiResponse<{ version: string; buildTime: string }>> {
    return this.get<{ version: string; buildTime: string }>('/config/version');
  }

  // Settings
  async getAllSettings(): Promise<ApiResponse<Record<string, any>>> {
    return this.get<Record<string, any>>('/config/settings');
  }

  async getSetting(key: string): Promise<ApiResponse<any>> {
    return this.get<any>(`/config/settings/${encodeURIComponent(key)}`);
  }

  async updateSetting(key: string, value: any): Promise<ApiResponse<{ success: boolean }>> {
    return this.patch<{ success: boolean }>(`/config/settings/${encodeURIComponent(key)}`, {
      value,
    });
  }

  async deleteSetting(key: string): Promise<ApiResponse<{ success: boolean }>> {
    return this.post<{ success: boolean }>(`/config/settings/${encodeURIComponent(key)}/delete`, {});
  }
}
