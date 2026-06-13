import { describe, it, expect, beforeEach, vi } from 'vitest';

class RequestDeduplicator {
  private pending: Map<string, Promise<unknown>> = new Map();

  execute<T>(key: string, fn: () => Promise<T>): Promise<T> {
    if (this.pending.has(key)) {
      return this.pending.get(key) as Promise<T>;
    }

    const promise = fn().finally(() => {
      this.pending.delete(key);
    });

    this.pending.set(key, promise);
    return promise;
  }

  getPendingCount(): number {
    return this.pending.size;
  }

  clear(): void {
    this.pending.clear();
  }

  hasPending(key: string): boolean {
    return this.pending.has(key);
  }
}

describe('RequestDeduplicator', () => {
  let deduplicator: RequestDeduplicator;

  beforeEach(() => {
    vi.useFakeTimers();
    deduplicator = new RequestDeduplicator();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should deduplicate requests', async () => {
    const fn = vi.fn().mockResolvedValue('result');

    const promise1 = deduplicator.execute('key1', fn);
    const promise2 = deduplicator.execute('key1', fn);

    expect(promise1).toBe(promise2);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('should execute different keys', async () => {
    const fn1 = vi.fn().mockResolvedValue('result1');
    const fn2 = vi.fn().mockResolvedValue('result2');

    await deduplicator.execute('key1', fn1);
    await deduplicator.execute('key2', fn2);

    expect(fn1).toHaveBeenCalledTimes(1);
    expect(fn2).toHaveBeenCalledTimes(1);
  });

  it('should track pending requests', async () => {
    const fn = vi.fn().mockResolvedValue('result');

    const promise = deduplicator.execute('key1', fn);
    expect(deduplicator.getPendingCount()).toBe(1);

    await promise;
    expect(deduplicator.getPendingCount()).toBe(0);
  });

  it('should clear pending', async () => {
    const fn = vi.fn().mockResolvedValue('result');
    deduplicator.execute('key1', fn);
    deduplicator.clear();
    expect(deduplicator.getPendingCount()).toBe(0);
  });

  it('should check if key has pending', async () => {
    const fn = vi.fn().mockResolvedValue('result');
    deduplicator.execute('key1', fn);
    expect(deduplicator.hasPending('key1')).toBe(true);
  });

  it('should clean up after completion', async () => {
    const fn = vi.fn().mockResolvedValue('result');
    const promise = deduplicator.execute('key1', fn);
    await promise;
    expect(deduplicator.hasPending('key1')).toBe(false);
  });
});

function afterEach(callback: () => void) {
  callback();
}
