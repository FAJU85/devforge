/**
 * Request Batcher - batches multiple requests for efficiency
 */

export interface BatchRequest<T> {
  key: string;
  fn: () => Promise<T>;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
}

export interface BatchConfig {
  maxBatchSize?: number; // Default 10
  maxWaitTime?: number; // Default 50ms
  enabled?: boolean; // Default true
}

export class RequestBatcher {
  private queue: BatchRequest<any>[] = [];
  private timer: NodeJS.Timeout | null = null;
  private config: Required<BatchConfig>;
  private stats = {
    batchCount: 0,
    requestCount: 0,
    savedRequests: 0,
  };

  constructor(config: BatchConfig = {}) {
    this.config = {
      maxBatchSize: config.maxBatchSize ?? 10,
      maxWaitTime: config.maxWaitTime ?? 50,
      enabled: config.enabled ?? true,
    };
  }

  /**
   * Queue a request for batching
   */
  async queue<T>(key: string, fn: () => Promise<T>): Promise<T> {
    if (!this.config.enabled) {
      return fn();
    }

    return new Promise<T>((resolve, reject) => {
      this.queue.push({ key, fn, resolve, reject });
      this.stats.requestCount++;

      // Process batch if full
      if (this.queue.length >= this.config.maxBatchSize) {
        this.processBatch();
      } else if (!this.timer) {
        // Set timer for max wait time
        this.timer = setTimeout(() => this.processBatch(), this.config.maxWaitTime);
      }
    });
  }

  /**
   * Process current batch
   */
  private async processBatch(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    if (this.queue.length === 0) {
      return;
    }

    const batch = this.queue.splice(0, this.config.maxBatchSize);
    this.stats.batchCount++;
    this.stats.savedRequests += batch.length - 1;

    // Execute all requests in parallel
    const promises = batch.map(async (req) => {
      try {
        const result = await req.fn();
        req.resolve(result);
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        req.reject(err);
      }
    });

    await Promise.all(promises);

    // Process next batch if queue has items
    if (this.queue.length > 0) {
      if (this.queue.length >= this.config.maxBatchSize) {
        this.processBatch();
      } else {
        this.timer = setTimeout(() => this.processBatch(), this.config.maxWaitTime);
      }
    }
  }

  /**
   * Get queue size
   */
  getQueueSize(): number {
    return this.queue.length;
  }

  /**
   * Get batching statistics
   */
  getStats() {
    return {
      batchCount: this.stats.batchCount,
      requestCount: this.stats.requestCount,
      savedRequests: this.stats.savedRequests,
      efficiency:
        this.stats.requestCount > 0
          ? ((this.stats.savedRequests / this.stats.requestCount) * 100).toFixed(2) + '%'
          : '0%',
    };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = { batchCount: 0, requestCount: 0, savedRequests: 0 };
  }

  /**
   * Flush all pending requests
   */
  async flush(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    while (this.queue.length > 0) {
      await this.processBatch();
    }
  }

  /**
   * Enable/disable batching
   */
  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled;
    if (!enabled && this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}
