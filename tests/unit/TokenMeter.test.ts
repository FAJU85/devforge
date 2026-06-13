import { describe, it, expect, beforeEach } from 'vitest';

class TokenMeter {
  private current: number = 0;
  private max: number = 4096;
  private threshold: number = 0.85;

  constructor(max: number = 4096, threshold: number = 0.85) {
    this.max = max;
    this.threshold = threshold;
  }

  addTokens(count: number): void {
    this.current = Math.min(this.current + count, this.max);
  }

  removeTokens(count: number): void {
    this.current = Math.max(this.current - count, 0);
  }

  getCurrent(): number {
    return this.current;
  }

  getMax(): number {
    return this.max;
  }

  getUsagePercent(): number {
    return (this.current / this.max) * 100;
  }

  getRemaining(): number {
    return this.max - this.current;
  }

  isThresholdExceeded(): boolean {
    return this.getUsagePercent() >= this.threshold * 100;
  }

  reset(): void {
    this.current = 0;
  }

  setMax(max: number): void {
    this.max = max;
    if (this.current > max) {
      this.current = max;
    }
  }

  getStatus(): 'healthy' | 'warning' | 'critical' {
    const percent = this.getUsagePercent();
    if (percent >= 95) return 'critical';
    if (percent >= 85) return 'warning';
    return 'healthy';
  }
}

describe('TokenMeter', () => {
  let meter: TokenMeter;

  beforeEach(() => {
    meter = new TokenMeter(4096);
  });

  it('should initialize with default values', () => {
    expect(meter.getCurrent()).toBe(0);
    expect(meter.getMax()).toBe(4096);
  });

  it('should add tokens', () => {
    meter.addTokens(100);
    expect(meter.getCurrent()).toBe(100);
  });

  it('should remove tokens', () => {
    meter.addTokens(100);
    meter.removeTokens(30);
    expect(meter.getCurrent()).toBe(70);
  });

  it('should not go below zero', () => {
    meter.removeTokens(100);
    expect(meter.getCurrent()).toBe(0);
  });

  it('should not exceed max', () => {
    meter.addTokens(5000);
    expect(meter.getCurrent()).toBe(4096);
  });

  it('should calculate usage percent', () => {
    meter.addTokens(2048);
    expect(meter.getUsagePercent()).toBe(50);
  });

  it('should get remaining tokens', () => {
    meter.addTokens(1000);
    expect(meter.getRemaining()).toBe(3096);
  });

  it('should detect threshold exceeded', () => {
    meter.addTokens(3476); // 85%
    expect(meter.isThresholdExceeded()).toBe(true);
  });

  it('should detect threshold not exceeded', () => {
    meter.addTokens(2000); // ~49%
    expect(meter.isThresholdExceeded()).toBe(false);
  });

  it('should reset tokens', () => {
    meter.addTokens(1000);
    meter.reset();
    expect(meter.getCurrent()).toBe(0);
  });

  it('should update max limit', () => {
    meter.setMax(2048);
    expect(meter.getMax()).toBe(2048);
  });

  it('should cap current when max is reduced', () => {
    meter.addTokens(3000);
    meter.setMax(2000);
    expect(meter.getCurrent()).toBe(2000);
  });

  it('should return healthy status', () => {
    meter.addTokens(2000); // ~49%
    expect(meter.getStatus()).toBe('healthy');
  });

  it('should return warning status', () => {
    meter.addTokens(3476); // 85%
    expect(meter.getStatus()).toBe('warning');
  });

  it('should return critical status', () => {
    meter.addTokens(3887); // 95%
    expect(meter.getStatus()).toBe('critical');
  });

  it('should handle custom threshold', () => {
    const customMeter = new TokenMeter(1000, 0.9);
    customMeter.addTokens(850); // 85%, below 90%
    expect(customMeter.isThresholdExceeded()).toBe(false);
    customMeter.addTokens(100); // 95%, above 90%
    expect(customMeter.isThresholdExceeded()).toBe(true);
  });
});
