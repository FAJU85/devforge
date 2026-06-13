/**
 * Statistics Store - usage metrics and analytics
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface UsageMetric {
  timestamp: Date;
  tokensUsed: number;
  messagesCount: number;
  modelUsed: string;
  cost: number;
}

export interface ModelStats {
  model: string;
  provider: string;
  totalMessages: number;
  totalTokens: number;
  totalCost: number;
  lastUsed?: Date;
}

export interface StatsState {
  // Daily metrics
  dailyMetrics: UsageMetric[];

  // Model statistics
  modelStats: ModelStats[];

  // Aggregates
  totalMessages: number;
  totalTokens: number;
  totalCost: number;

  // Time period
  periodStart: Date;
  periodEnd: Date;

  // Actions
  recordUsage: (metric: Omit<UsageMetric, 'timestamp'>) => void;
  updateModelStats: (model: string, provider: string, tokens: number, cost: number) => void;
  clearStats: () => void;
  setPeriod: (start: Date, end: Date) => void;

  // Getters
  getDailyMetrics: () => UsageMetric[];
  getMetricsForPeriod: (start: Date, end: Date) => UsageMetric[];
  getModelStats: () => ModelStats[];
  getTopModel: () => ModelStats | undefined;
  getTotalCost: () => number;
  getAverageTokensPerMessage: () => number;
}

export const useStatsStore = create<StatsState>()(
  devtools(
    persist(
      (set, get) => ({
        dailyMetrics: [],
        modelStats: [],
        totalMessages: 0,
        totalTokens: 0,
        totalCost: 0,
        periodStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
        periodEnd: new Date(),

        recordUsage: (metric) =>
          set((state) => ({
            dailyMetrics: [...state.dailyMetrics, { ...metric, timestamp: new Date() }],
            totalMessages: state.totalMessages + metric.messagesCount,
            totalTokens: state.totalTokens + metric.tokensUsed,
            totalCost: parseFloat((state.totalCost + metric.cost).toFixed(10)),
          })),

        updateModelStats: (model, provider, tokens, cost) =>
          set((state) => {
            const existing = state.modelStats.find((m) => m.model === model);

            if (existing) {
              return {
                modelStats: state.modelStats.map((m) =>
                  m.model === model
                    ? {
                        ...m,
                        totalMessages: m.totalMessages + 1,
                        totalTokens: m.totalTokens + tokens,
                        totalCost: parseFloat((m.totalCost + cost).toFixed(10)),
                        lastUsed: new Date(),
                      }
                    : m
                ),
              };
            }

            return {
              modelStats: [
                ...state.modelStats,
                {
                  model,
                  provider,
                  totalMessages: 1,
                  totalTokens: tokens,
                  totalCost: cost,
                  lastUsed: new Date(),
                },
              ],
            };
          }),

        clearStats: () =>
          set({
            dailyMetrics: [],
            modelStats: [],
            totalMessages: 0,
            totalTokens: 0,
            totalCost: 0,
          }),

        setPeriod: (start, end) => set({ periodStart: start, periodEnd: end }),

        getDailyMetrics: () => get().dailyMetrics,

        getMetricsForPeriod: (start, end) => {
          const state = get();
          return state.dailyMetrics.filter(
            (m) => m.timestamp >= start && m.timestamp <= end
          );
        },

        getModelStats: () => {
          const state = get();
          return state.modelStats.sort((a, b) => b.totalCost - a.totalCost);
        },

        getTopModel: () => {
          const state = get();
          if (state.modelStats.length === 0) return undefined;
          return state.modelStats.reduce((top, current) =>
            current.totalCost > top.totalCost ? current : top
          );
        },

        getTotalCost: () => {
          const state = get();
          return parseFloat(state.modelStats.reduce((sum, m) => sum + m.totalCost, 0).toFixed(10));
        },

        getAverageTokensPerMessage: () => {
          const state = get();
          return state.totalMessages > 0
            ? Math.round(state.totalTokens / state.totalMessages)
            : 0;
        },
      }),
      {
        name: 'stats-store',
        version: 1,
      }
    ),
    { name: 'StatsStore' }
  )
);
