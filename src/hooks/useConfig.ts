/**
 * useConfig Hook - custom hook for configuration operations
 */

import { useCallback } from 'react';
import { useConfigStore } from '../stores/configStore';
import { ConfigService } from '../services/configService';

export interface UseConfigReturn {
  // State
  providers: ReturnType<typeof useConfigStore>['providers'];
  activeProvider: ReturnType<typeof useConfigStore>['activeProvider'];
  models: ReturnType<typeof useConfigStore>['models'];
  activeModel: ReturnType<typeof useConfigStore>['activeModel'];
  featureFlags: ReturnType<typeof useConfigStore>['featureFlags'];

  // Providers
  loadProviders: () => Promise<any[]>;
  addProvider: (provider: any) => void;
  updateProvider: (id: string, updates: any) => void;
  deleteProvider: (id: string) => void;
  setActiveProvider: (id: string) => void;
  testProviderConnection: (providerId: string) => Promise<boolean>;

  // Models
  loadModels: () => Promise<any[]>;
  getModel: (modelId: string) => Promise<any>;
  createModel: (model: any) => Promise<any>;
  updateModel: (modelId: string, updates: any) => Promise<any>;
  deleteModel: (modelId: string) => Promise<boolean>;
  setActiveModel: (id: string) => void;

  // API Keys
  loadAPIKeys: () => Promise<any[]>;
  createAPIKey: (provider: string, keyValue: string) => Promise<any>;
  validateAPIKey: (provider: string, keyValue: string) => Promise<boolean>;
  deleteAPIKey: (keyId: string) => Promise<boolean>;

  // Feature Flags
  loadFeatureFlags: () => Promise<any[]>;
  isFeatureEnabled: (flagName: string) => boolean;
  setFeatureFlag: (flagName: string, enabled: boolean) => void;
  toggleFeatureFlag: (flagName: string) => void;

  // System
  getSystemStatus: () => Promise<any>;
  getAppVersion: () => Promise<any>;

  // State Setters
  setModelConfig: (config: any) => void;
}

export function useConfig(apiBaseUrl: string = 'http://localhost:3000/api'): UseConfigReturn {
  const configStore = useConfigStore();
  const configService = new ConfigService(apiBaseUrl);

  const loadProviders = useCallback(
    async () => {
      try {
        return await configService.loadProviders();
      } catch (error) {
        console.error('Failed to load providers:', error);
        throw error;
      }
    },
    [configService]
  );

  const addProvider = useCallback(
    (provider: any) => {
      configStore.addProvider(provider);
    },
    [configStore]
  );

  const updateProvider = useCallback(
    (id: string, updates: any) => {
      configStore.updateProvider(id, updates);
    },
    [configStore]
  );

  const deleteProvider = useCallback(
    (id: string) => {
      configStore.deleteProvider(id);
    },
    [configStore]
  );

  const setActiveProvider = useCallback(
    (id: string) => {
      configStore.setActiveProvider(id);
    },
    [configStore]
  );

  const testProviderConnection = useCallback(
    async (providerId: string) => {
      try {
        return await configService.testProviderConnection(providerId);
      } catch (error) {
        console.error('Failed to test provider connection:', error);
        throw error;
      }
    },
    [configService]
  );

  const loadModels = useCallback(
    async () => {
      try {
        return await configService.loadModels();
      } catch (error) {
        console.error('Failed to load models:', error);
        throw error;
      }
    },
    [configService]
  );

  const getModel = useCallback(
    async (modelId: string) => {
      try {
        return await configService.getModel(modelId);
      } catch (error) {
        console.error('Failed to get model:', error);
        throw error;
      }
    },
    [configService]
  );

  const createModel = useCallback(
    async (model: any) => {
      try {
        return await configService.createModel(model);
      } catch (error) {
        console.error('Failed to create model:', error);
        throw error;
      }
    },
    [configService]
  );

  const updateModel = useCallback(
    async (modelId: string, updates: any) => {
      try {
        return await configService.updateModel(modelId, updates);
      } catch (error) {
        console.error('Failed to update model:', error);
        throw error;
      }
    },
    [configService]
  );

  const deleteModel = useCallback(
    async (modelId: string) => {
      try {
        return await configService.deleteModel(modelId);
      } catch (error) {
        console.error('Failed to delete model:', error);
        throw error;
      }
    },
    [configService]
  );

  const setActiveModel = useCallback(
    (id: string) => {
      configStore.setActiveModel(id);
    },
    [configStore]
  );

  const loadAPIKeys = useCallback(
    async () => {
      try {
        return await configService.loadAPIKeys();
      } catch (error) {
        console.error('Failed to load API keys:', error);
        throw error;
      }
    },
    [configService]
  );

  const createAPIKey = useCallback(
    async (provider: string, keyValue: string) => {
      try {
        return await configService.createAPIKey(provider, keyValue);
      } catch (error) {
        console.error('Failed to create API key:', error);
        throw error;
      }
    },
    [configService]
  );

  const validateAPIKey = useCallback(
    async (provider: string, keyValue: string) => {
      try {
        return await configService.validateAPIKey(provider, keyValue);
      } catch (error) {
        console.error('Failed to validate API key:', error);
        throw error;
      }
    },
    [configService]
  );

  const deleteAPIKey = useCallback(
    async (keyId: string) => {
      try {
        return await configService.deleteAPIKey(keyId);
      } catch (error) {
        console.error('Failed to delete API key:', error);
        throw error;
      }
    },
    [configService]
  );

  const loadFeatureFlags = useCallback(
    async () => {
      try {
        return await configService.loadFeatureFlags();
      } catch (error) {
        console.error('Failed to load feature flags:', error);
        throw error;
      }
    },
    [configService]
  );

  const isFeatureEnabled = useCallback(
    (flagName: string) => {
      return configStore.isFeatureEnabled(flagName);
    },
    [configStore]
  );

  const setFeatureFlag = useCallback(
    (flagName: string, enabled: boolean) => {
      configStore.setFeatureFlag(flagName, enabled);
    },
    [configStore]
  );

  const toggleFeatureFlag = useCallback(
    (flagName: string) => {
      configStore.toggleFeatureFlag(flagName);
    },
    [configStore]
  );

  const getSystemStatus = useCallback(
    async () => {
      try {
        return await configService.getSystemStatus();
      } catch (error) {
        console.error('Failed to get system status:', error);
        throw error;
      }
    },
    [configService]
  );

  const getAppVersion = useCallback(
    async () => {
      try {
        return await configService.getAppVersion();
      } catch (error) {
        console.error('Failed to get app version:', error);
        throw error;
      }
    },
    [configService]
  );

  const setModelConfig = useCallback(
    (config: any) => {
      configStore.setModelConfig(config);
    },
    [configStore]
  );

  return {
    providers: configStore.providers,
    activeProvider: configStore.activeProvider,
    models: configStore.models,
    activeModel: configStore.activeModel,
    featureFlags: configStore.featureFlags,
    loadProviders,
    addProvider,
    updateProvider,
    deleteProvider,
    setActiveProvider,
    testProviderConnection,
    loadModels,
    getModel,
    createModel,
    updateModel,
    deleteModel,
    setActiveModel,
    loadAPIKeys,
    createAPIKey,
    validateAPIKey,
    deleteAPIKey,
    loadFeatureFlags,
    isFeatureEnabled,
    setFeatureFlag,
    toggleFeatureFlag,
    getSystemStatus,
    getAppVersion,
    setModelConfig,
  };
}
