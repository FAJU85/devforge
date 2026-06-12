/**
 * Configuration Store - provider and model settings
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface ProviderConfig {
  id: string;
  name: string;
  apiKey?: string;
  isConfigured: boolean;
  baseUrl?: string;
  customSettings?: Record<string, any>;
}

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  contextWindow: number;
  costPer1kTokens?: {
    input: number;
    output: number;
  };
}

export interface ConfigState {
  // Providers
  providers: ProviderConfig[];
  activeProviderId: string | null;

  // Models
  models: ModelConfig[];
  activeModelId: string | null;

  // Settings
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  topK?: number;

  // Feature flags
  featureFlags: Record<string, boolean>;

  // Actions
  addProvider: (provider: ProviderConfig) => void;
  updateProvider: (id: string, updates: Partial<ProviderConfig>) => void;
  removeProvider: (id: string) => void;
  setActiveProvider: (id: string | null) => void;

  // Model actions
  addModel: (model: ModelConfig) => void;
  updateModel: (id: string, updates: Partial<ModelConfig>) => void;
  removeModel: (id: string) => void;
  setActiveModel: (id: string | null) => void;

  // Settings
  updateSettings: (settings: Partial<Omit<ConfigState, keyof typeof updateSettings>>) => void;

  // Feature flags
  setFeatureFlag: (flag: string, enabled: boolean) => void;
  toggleFeatureFlag: (flag: string) => void;
  isFeatureEnabled: (flag: string) => boolean;

  // Getters
  getActiveProvider: () => ProviderConfig | undefined;
  getActiveModel: () => ModelConfig | undefined;
  getProviderModels: (providerId: string) => ModelConfig[];
  isConfigurationValid: () => boolean;
}

export const useConfigStore = create<ConfigState>()(
  devtools(
    persist(
      (set, get) => ({
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

        addProvider: (provider) =>
          set((state) => ({
            providers: [...state.providers, provider],
            activeProviderId: state.activeProviderId || provider.id,
          })),

        updateProvider: (id, updates) =>
          set((state) => ({
            providers: state.providers.map((p) => (p.id === id ? { ...p, ...updates } : p)),
          })),

        removeProvider: (id) =>
          set((state) => ({
            providers: state.providers.filter((p) => p.id !== id),
            activeProviderId: state.activeProviderId === id ? null : state.activeProviderId,
          })),

        setActiveProvider: (id) => set({ activeProviderId: id }),

        addModel: (model) =>
          set((state) => ({
            models: [...state.models, model],
            activeModelId: state.activeModelId || model.id,
          })),

        updateModel: (id, updates) =>
          set((state) => ({
            models: state.models.map((m) => (m.id === id ? { ...m, ...updates } : m)),
          })),

        removeModel: (id) =>
          set((state) => ({
            models: state.models.filter((m) => m.id !== id),
            activeModelId: state.activeModelId === id ? null : state.activeModelId,
          })),

        setActiveModel: (id) => set({ activeModelId: id }),

        updateSettings: (settings) => set(settings as Partial<ConfigState>),

        setFeatureFlag: (flag, enabled) =>
          set((state) => ({
            featureFlags: { ...state.featureFlags, [flag]: enabled },
          })),

        toggleFeatureFlag: (flag) =>
          set((state) => ({
            featureFlags: {
              ...state.featureFlags,
              [flag]: !state.featureFlags[flag],
            },
          })),

        isFeatureEnabled: (flag) => get().featureFlags[flag] || false,

        getActiveProvider: () => {
          const state = get();
          return state.providers.find((p) => p.id === state.activeProviderId);
        },

        getActiveModel: () => {
          const state = get();
          return state.models.find((m) => m.id === state.activeModelId);
        },

        getProviderModels: (providerId) => {
          const state = get();
          return state.models.filter((m) => m.provider === providerId);
        },

        isConfigurationValid: () => {
          const state = get();
          const provider = state.getActiveProvider?.();
          const model = state.getActiveModel?.();
          return !!(provider?.isConfigured && model);
        },
      }),
      {
        name: 'config-store',
        version: 1,
      }
    ),
    { name: 'ConfigStore' }
  )
);
