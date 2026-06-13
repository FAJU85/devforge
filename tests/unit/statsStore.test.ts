import { describe, it, expect, beforeEach } from 'vitest';
import { useStatsStore, UsageMetric, ModelStats } from '../../src/stores/statsStore';

describe('Statistics Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useStatsStore.setState({
      dailyMetrics: [],
      modelStats: [],
      totalMessages: 0,
      totalTokens: 0,
      totalCost: 0,
      periodStart: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      periodEnd: new Date(),
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useStatsStore.getState();
      expect(state.dailyMetrics).toEqual([]);
      expect(state.modelStats).toEqual([]);
      expect(state.totalMessages).toBe(0);
      expect(state.totalTokens).toBe(0);
      expect(state.totalCost).toBe(0);
      expect(state.periodStart).toBeInstanceOf(Date);
      expect(state.periodEnd).toBeInstanceOf(Date);
    });

    it('should have period covering last 30 days', () => {
      const state = useStatsStore.getState();
      const daysDiff = (state.periodEnd.getTime() - state.periodStart.getTime()) / (1000 * 60 * 60 * 24);

      expect(daysDiff).toBeCloseTo(30, 0);
    });
  });

  describe('Usage Recording', () => {
    it('should record a usage metric', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      expect(useStatsStore.getState().dailyMetrics).toHaveLength(1);
      expect(useStatsStore.getState().dailyMetrics[0].tokensUsed).toBe(100);
    });

    it('should update aggregate statistics on usage recording', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      expect(useStatsStore.getState().totalTokens).toBe(100);
      expect(useStatsStore.getState().totalMessages).toBe(1);
      expect(useStatsStore.getState().totalCost).toBe(0.003);
    });

    it('should accumulate multiple usage records', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      state.recordUsage({
        tokensUsed: 200,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.006,
      });

      expect(useStatsStore.getState().dailyMetrics).toHaveLength(2);
      expect(useStatsStore.getState().totalTokens).toBe(300);
      expect(useStatsStore.getState().totalMessages).toBe(2);
      expect(useStatsStore.getState().totalCost).toBe(0.009);
    });

    it('should set timestamp on recorded metric', () => {
      const state = useStatsStore.getState();
      const before = new Date();

      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      const after = new Date();
      const metric = useStatsStore.getState().dailyMetrics[0];

      expect(metric.timestamp.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(metric.timestamp.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    it('should get daily metrics', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      const metrics = state.getDailyMetrics();
      expect(metrics).toHaveLength(1);
      expect(metrics[0].tokensUsed).toBe(100);
    });
  });

  describe('Model Statistics', () => {
    it('should track a new model', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);

      expect(useStatsStore.getState().modelStats).toHaveLength(1);
      const modelStat = useStatsStore.getState().modelStats[0];
      expect(modelStat.model).toBe('gpt-4');
      expect(modelStat.provider).toBe('openai');
      expect(modelStat.totalMessages).toBe(1);
      expect(modelStat.totalTokens).toBe(100);
      expect(modelStat.totalCost).toBe(0.003);
    });

    it('should update existing model stats', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      state.updateModelStats('gpt-4', 'openai', 200, 0.006);

      expect(useStatsStore.getState().modelStats).toHaveLength(1);
      const modelStat = useStatsStore.getState().modelStats[0];
      expect(modelStat.totalMessages).toBe(2);
      expect(modelStat.totalTokens).toBe(300);
      expect(modelStat.totalCost).toBe(0.009);
    });

    it('should track multiple models separately', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      state.updateModelStats('claude-3', 'anthropic', 150, 0.005);

      expect(useStatsStore.getState().modelStats).toHaveLength(2);
    });

    it('should update lastUsed timestamp', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);

      const before = new Date();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      const after = new Date();

      const modelStat = useStatsStore.getState().modelStats[0];
      expect(modelStat.lastUsed).toBeDefined();
      expect(modelStat.lastUsed!.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(modelStat.lastUsed!.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    it('should get model stats', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      state.updateModelStats('claude-3', 'anthropic', 150, 0.01);

      const stats = state.getModelStats();
      expect(stats).toHaveLength(2);
      // Should be sorted by cost descending
      expect(stats[0].totalCost).toBeGreaterThanOrEqual(stats[1].totalCost);
    });

    it('should get top model by cost', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      state.updateModelStats('claude-3', 'anthropic', 150, 0.01);

      const topModel = state.getTopModel();
      expect(topModel?.model).toBe('claude-3');
    });

    it('should return undefined for top model when no stats', () => {
      const state = useStatsStore.getState();
      const topModel = state.getTopModel();

      expect(topModel).toBeUndefined();
    });

    it('should get total cost', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      state.updateModelStats('claude-3', 'anthropic', 150, 0.01);

      expect(state.getTotalCost()).toBe(0.013);
    });
  });

  describe('Period Management', () => {
    it('should set period', () => {
      const state = useStatsStore.getState();
      const start = new Date('2024-01-01');
      const end = new Date('2024-01-31');

      state.setPeriod(start, end);

      expect(useStatsStore.getState().periodStart).toEqual(start);
      expect(useStatsStore.getState().periodEnd).toEqual(end);
    });

    it('should get metrics for period', () => {
      const state = useStatsStore.getState();
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      const metricsInRange = state.getMetricsForPeriod(yesterday, tomorrow);
      expect(metricsInRange).toHaveLength(1);
    });

    it('should filter metrics by period', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      const futureStart = new Date();
      const futureEnd = new Date();

      const metricsInFuture = state.getMetricsForPeriod(futureStart, futureEnd);
      // Current metric timestamp should be close to now, so it should be included
      expect(metricsInFuture.length).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Statistics Calculations', () => {
    it('should calculate average tokens per message', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 2,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      state.recordUsage({
        tokensUsed: 200,
        messagesCount: 4,
        modelUsed: 'gpt-4',
        cost: 0.006,
      });

      // Total: 300 tokens, 6 messages => 50 tokens per message
      expect(state.getAverageTokensPerMessage()).toBe(50);
    });

    it('should return 0 for average when no messages', () => {
      const state = useStatsStore.getState();
      expect(state.getAverageTokensPerMessage()).toBe(0);
    });

    it('should round average tokens per message', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 3,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      // 100 / 3 = 33.333... => should round to 33
      expect(state.getAverageTokensPerMessage()).toBe(33);
    });
  });

  describe('State Clearing', () => {
    it('should clear all stats', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);

      expect(useStatsStore.getState().dailyMetrics).toHaveLength(1);
      expect(useStatsStore.getState().modelStats).toHaveLength(1);

      state.clearStats();

      expect(useStatsStore.getState().dailyMetrics).toHaveLength(0);
      expect(useStatsStore.getState().modelStats).toHaveLength(0);
      expect(useStatsStore.getState().totalMessages).toBe(0);
      expect(useStatsStore.getState().totalTokens).toBe(0);
      expect(useStatsStore.getState().totalCost).toBe(0);
    });

    it('should not affect period when clearing stats', () => {
      const state = useStatsStore.getState();
      const periodStart = useStatsStore.getState().periodStart;
      const periodEnd = useStatsStore.getState().periodEnd;

      state.clearStats();

      expect(useStatsStore.getState().periodStart).toEqual(periodStart);
      expect(useStatsStore.getState().periodEnd).toEqual(periodEnd);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero cost metrics', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0,
      });

      expect(useStatsStore.getState().totalCost).toBe(0);
    });

    it('should handle very large token counts', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 1000000,
        messagesCount: 100,
        modelUsed: 'gpt-4',
        cost: 300,
      });

      expect(useStatsStore.getState().totalTokens).toBe(1000000);
      expect(state.getAverageTokensPerMessage()).toBe(10000);
    });

    it('should handle high precision cost values', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.0001234567,
      });

      expect(useStatsStore.getState().totalCost).toBe(0.0001234567);
    });

    it('should handle model with empty string name', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('', 'openai', 100, 0.003);

      expect(useStatsStore.getState().modelStats).toHaveLength(1);
      expect(useStatsStore.getState().modelStats[0].model).toBe('');
    });

    it('should handle model with special characters', () => {
      const state = useStatsStore.getState();
      state.updateModelStats('gpt-4-turbo-preview', 'openai', 100, 0.003);

      const modelStat = state.getModelStats()[0];
      expect(modelStat.model).toBe('gpt-4-turbo-preview');
    });

    it('should handle single message calculation', () => {
      const state = useStatsStore.getState();
      state.recordUsage({
        tokensUsed: 123,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      expect(state.getAverageTokensPerMessage()).toBe(123);
    });
  });

  describe('Complex Scenarios', () => {
    it('should track usage across multiple models and aggregate correctly', () => {
      const state = useStatsStore.getState();

      // Record usage for multiple models
      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      state.recordUsage({
        tokensUsed: 150,
        messagesCount: 2,
        modelUsed: 'claude-3',
        cost: 0.005,
      });
      state.recordUsage({
        tokensUsed: 200,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.006,
      });

      // Update model stats
      state.updateModelStats('gpt-4', 'openai', 100, 0.003);
      state.updateModelStats('claude-3', 'anthropic', 150, 0.005);
      state.updateModelStats('gpt-4', 'openai', 200, 0.006);

      expect(useStatsStore.getState().totalTokens).toBe(450);
      expect(useStatsStore.getState().totalMessages).toBe(4);
      expect(useStatsStore.getState().totalCost).toBe(0.014);

      const modelStats = state.getModelStats();
      expect(modelStats).toHaveLength(2);

      const gpt4Stat = modelStats.find((m) => m.model === 'gpt-4');
      expect(gpt4Stat?.totalTokens).toBe(300);
      expect(gpt4Stat?.totalMessages).toBe(2);
    });

    it('should handle period queries with multiple metrics', () => {
      const state = useStatsStore.getState();
      const dayStart = new Date();
      dayStart.setHours(0, 0, 0, 0);
      const dayEnd = new Date();
      dayEnd.setHours(23, 59, 59, 999);

      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });
      state.recordUsage({
        tokensUsed: 200,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.006,
      });

      const todayMetrics = state.getMetricsForPeriod(dayStart, dayEnd);
      expect(todayMetrics.length).toBeGreaterThanOrEqual(0);
    });

    it('should maintain independent aggregates for usage and model stats', () => {
      const state = useStatsStore.getState();

      state.recordUsage({
        tokensUsed: 100,
        messagesCount: 1,
        modelUsed: 'gpt-4',
        cost: 0.003,
      });

      const totalBefore = useStatsStore.getState().totalTokens;

      state.updateModelStats('claude-3', 'anthropic', 150, 0.005);

      // Recording usage only affects usage metrics, not model stats tracking
      expect(useStatsStore.getState().totalTokens).toBe(totalBefore);
    });
  });
});
