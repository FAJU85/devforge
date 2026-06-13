/**
 * Request Deduplicator - prevents duplicate concurrent requests
 */

export interface PendingRequest<T> {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
  count: number;
}

export class RequestDeduplicator {
  private pending = new Map<string, PendingRequest<any>>();
  private stats = {
    deduped: 0,
    executed: 0,
  };

  /**
   * Execute function only once for duplicate requests
   */
  async dedupe<T>(key: string, fn: () => Promise<T>): Promise<T> {
    // Check if request is already pending
    const existing = this.pending.get(key);
    if (existing) {
      existing.count++;
      this.stats.deduped++;
      return existing.promise;
    }

    // Create new pending request
    let resolve: (value: T) => void;
    let reject: (error: Error) => void;

    const promise = new Promise<T>((res, rej) => {
      resolve = res;
      reject = rej;
    });

    const pending: PendingRequest<T> = {
      promise,
      resolve: resolve!,
      reject: reject!,
      count: 1,
    };

    this.pending.set(key, pending);
    this.stats.executed++;

    try {
      const result = await fn();
      pending.resolve(result);
      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      pending.reject(err);
      throw err;
    } finally {
      this.pending.delete(key);
    }
  }

  /**
   * Get number of pending requests
   */
  getPendingCount(): number {
    return this.pending.size;
  }

  /**
   * Get deduplication statistics
   */
  getStats() {
    return {
      deduped: this.stats.deduped,
      executed: this.stats.executed,
      pending: this.pending.size,
      ratio:
        this.stats.executed > 0
          ? ((this.stats.deduped / (this.stats.deduped + this.stats.executed)) * 100).toFixed(2) +
            '%'
          : '0%',
    };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = { deduped: 0, executed: 0 };
  }

  /**
   * Clear all pending requests
   */
  clear(): void {
    this.pending.clear();
  }
}
