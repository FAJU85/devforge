import { describe, it, expect, beforeEach, vi } from 'vitest';

interface BatchRequest {
  id: string;
  operation: string;
  data: unknown;
}

class RequestBatcher {
  private queue: BatchRequest[] = [];
  private batchSize: number = 10;
  private flushInterval: number = 1000;
  private onBatchReady: ((batch: BatchRequest[]) => Promise<void>) | null = null;
  private timer: NodeJS.Timeout | null = null;

  constructor(batchSize: number = 10, flushInterval: number = 1000) {
    this.batchSize = batchSize;
    this.flushInterval = flushInterval;
  }

  add(request: BatchRequest): void {
    this.queue.push(request);
    if (this.queue.length >= this.batchSize) {
      this.flush();
    } else if (!this.timer) {
      this.startTimer();
    }
  }

  startTimer(): void {
    this.timer = setTimeout(() => {
      this.flush();
    }, this.flushInterval);
  }

  async flush(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    if (this.queue.length === 0) return;

    const batch = [...this.queue];
    this.queue = [];

    if (this.onBatchReady) {
      await this.onBatchReady(batch);
    }
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  onBatch(callback: (batch: BatchRequest[]) => Promise<void>): void {
    this.onBatchReady = callback;
  }

  clear(): void {
    this.queue = [];
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  getPendingRequests(): BatchRequest[] {
    return [...this.queue];
  }
}

describe('RequestBatcher', () => {
  let batcher: RequestBatcher;

  beforeEach(() => {
    vi.useFakeTimers();
    batcher = new RequestBatcher(3, 500);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize empty', () => {
    expect(batcher.getQueueSize()).toBe(0);
  });

  it('should add request to queue', () => {
    const req: BatchRequest = { id: '1', operation: 'create', data: {} };
    batcher.add(req);
    expect(batcher.getQueueSize()).toBe(1);
  });

  it('should batch when size limit reached', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);

    batcher.add({ id: '1', operation: 'create', data: {} });
    batcher.add({ id: '2', operation: 'create', data: {} });
    batcher.add({ id: '3', operation: 'create', data: {} });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(batcher.getQueueSize()).toBe(0);
  });

  it('should flush on timer', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);

    batcher.add({ id: '1', operation: 'create', data: {} });
    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should handle multiple batches', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);

    // First batch
    batcher.add({ id: '1', operation: 'create', data: {} });
    batcher.add({ id: '2', operation: 'create', data: {} });
    batcher.add({ id: '3', operation: 'create', data: {} });

    expect(callback).toHaveBeenCalledTimes(1);

    // Second batch
    batcher.add({ id: '4', operation: 'create', data: {} });
    batcher.add({ id: '5', operation: 'create', data: {} });
    batcher.add({ id: '6', operation: 'create', data: {} });

    expect(callback).toHaveBeenCalledTimes(2);
  });

  it('should clear queue', async () => {
    batcher.add({ id: '1', operation: 'create', data: {} });
    batcher.add({ id: '2', operation: 'create', data: {} });
    batcher.clear();
    expect(batcher.getQueueSize()).toBe(0);
  });

  it('should get pending requests', () => {
    const req1 = { id: '1', operation: 'create', data: {} };
    const req2 = { id: '2', operation: 'update', data: {} };
    batcher.add(req1);
    batcher.add(req2);
    const pending = batcher.getPendingRequests();
    expect(pending).toHaveLength(2);
    expect(pending[0].id).toBe('1');
  });

  it('should not call callback with empty queue', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);
    await batcher.flush();
    expect(callback).not.toHaveBeenCalled();
  });

  it('should batch different operation types', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);

    batcher.add({ id: '1', operation: 'create', data: {} });
    batcher.add({ id: '2', operation: 'update', data: {} });
    batcher.add({ id: '3', operation: 'delete', data: {} });

    const calledBatch = callback.mock.calls[0][0];
    expect(calledBatch).toHaveLength(3);
  });

  it('should maintain request order', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);

    batcher.add({ id: '1', operation: 'first', data: {} });
    batcher.add({ id: '2', operation: 'second', data: {} });
    batcher.add({ id: '3', operation: 'third', data: {} });

    const batch = callback.mock.calls[0][0];
    expect(batch[0].operation).toBe('first');
    expect(batch[1].operation).toBe('second');
    expect(batch[2].operation).toBe('third');
  });

  it('should handle partial batches', async () => {
    const callback = vi.fn().mockResolvedValue(undefined);
    batcher.onBatch(callback);

    batcher.add({ id: '1', operation: 'create', data: {} });
    batcher.add({ id: '2', operation: 'create', data: {} });

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledTimes(1);
    const batch = callback.mock.calls[0][0];
    expect(batch).toHaveLength(2);
  });
});

function afterEach(callback: () => void) {
  callback();
}
