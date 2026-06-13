import { describe, it, expect, beforeEach, vi } from 'vitest';

interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: number;
}

class WebSocketClient {
  private url: string;
  private connected: boolean = false;
  private messageHandlers: Map<string, Array<(data: unknown) => void>> = new Map();
  private onConnect: (() => void) | null = null;
  private onDisconnect: (() => void) | null = null;
  private messageQueue: WebSocketMessage[] = [];

  constructor(url: string) {
    this.url = url;
  }

  async connect(): Promise<void> {
    this.connected = true;
    this.onConnect?.();
  }

  disconnect(): void {
    this.connected = false;
    this.onDisconnect?.();
  }

  isConnected(): boolean {
    return this.connected;
  }

  send(type: string, data: unknown): void {
    const message: WebSocketMessage = {
      type,
      data,
      timestamp: Date.now()
    };

    if (this.connected) {
      // Simulate sending
      this.messageQueue.push(message);
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  on(type: string, handler: (data: unknown) => void): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  off(type: string, handler: (data: unknown) => void): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  onConnected(callback: () => void): void {
    this.onConnect = callback;
  }

  onDisconnected(callback: () => void): void {
    this.onDisconnect = callback;
  }

  emit(type: string, data: unknown): void {
    const handlers = this.messageHandlers.get(type) || [];
    handlers.forEach(handler => handler(data));
  }

  getMessageQueue(): WebSocketMessage[] {
    return [...this.messageQueue];
  }

  clearQueue(): void {
    this.messageQueue = [];
  }

  getURL(): string {
    return this.url;
  }

  addEventListener(type: string, handler: (data: unknown) => void): void {
    this.on(type, handler);
  }

  removeEventListener(type: string, handler: (data: unknown) => void): void {
    this.off(type, handler);
  }

  ping(): Promise<boolean> {
    return Promise.resolve(this.connected);
  }
}

describe('WebSocketClient', () => {
  let client: WebSocketClient;

  beforeEach(() => {
    client = new WebSocketClient('ws://localhost:8080');
  });

  it('should initialize disconnected', () => {
    expect(client.isConnected()).toBe(false);
  });

  it('should connect', async () => {
    await client.connect();
    expect(client.isConnected()).toBe(true);
  });

  it('should disconnect', async () => {
    await client.connect();
    client.disconnect();
    expect(client.isConnected()).toBe(false);
  });

  it('should call onConnected callback', async () => {
    const callback = vi.fn();
    client.onConnected(callback);
    await client.connect();
    expect(callback).toHaveBeenCalled();
  });

  it('should call onDisconnected callback', async () => {
    const callback = vi.fn();
    client.onDisconnected(callback);
    await client.connect();
    client.disconnect();
    expect(callback).toHaveBeenCalled();
  });

  it('should send message when connected', async () => {
    await client.connect();
    client.send('test', { message: 'hello' });
    const queue = client.getMessageQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].type).toBe('test');
  });

  it('should throw error when sending while disconnected', async () => {
    expect(() => client.send('test', {})).toThrow();
  });

  it('should register message handler', () => {
    const handler = vi.fn();
    client.on('test', handler);
    client.emit('test', { data: 'hello' });
    expect(handler).toHaveBeenCalledWith({ data: 'hello' });
  });

  it('should unregister message handler', () => {
    const handler = vi.fn();
    client.on('test', handler);
    client.off('test', handler);
    client.emit('test', { data: 'hello' });
    expect(handler).not.toHaveBeenCalled();
  });

  it('should handle multiple handlers', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    client.on('test', handler1);
    client.on('test', handler2);
    client.emit('test', { data: 'hello' });
    expect(handler1).toHaveBeenCalled();
    expect(handler2).toHaveBeenCalled();
  });

  it('should emit messages to correct type', () => {
    const handler1 = vi.fn();
    const handler2 = vi.fn();
    client.on('type1', handler1);
    client.on('type2', handler2);
    client.emit('type1', { data: 'hello' });
    expect(handler1).toHaveBeenCalled();
    expect(handler2).not.toHaveBeenCalled();
  });

  it('should get message queue', async () => {
    await client.connect();
    client.send('msg1', { id: 1 });
    client.send('msg2', { id: 2 });
    const queue = client.getMessageQueue();
    expect(queue).toHaveLength(2);
  });

  it('should clear message queue', async () => {
    await client.connect();
    client.send('test', {});
    client.clearQueue();
    expect(client.getMessageQueue()).toHaveLength(0);
  });

  it('should get URL', () => {
    expect(client.getURL()).toBe('ws://localhost:8080');
  });

  it('should use addEventListener alias', () => {
    const handler = vi.fn();
    client.addEventListener('test', handler);
    client.emit('test', { data: 'hello' });
    expect(handler).toHaveBeenCalled();
  });

  it('should use removeEventListener alias', () => {
    const handler = vi.fn();
    client.addEventListener('test', handler);
    client.removeEventListener('test', handler);
    client.emit('test', { data: 'hello' });
    expect(handler).not.toHaveBeenCalled();
  });

  it('should ping when connected', async () => {
    await client.connect();
    const result = await client.ping();
    expect(result).toBe(true);
  });

  it('should fail ping when disconnected', async () => {
    const result = await client.ping();
    expect(result).toBe(false);
  });

  it('should handle rapid connect/disconnect', async () => {
    await client.connect();
    client.disconnect();
    await client.connect();
    expect(client.isConnected()).toBe(true);
  });

  it('should preserve message timestamps', async () => {
    await client.connect();
    const before = Date.now();
    client.send('test', {});
    const after = Date.now();
    const queue = client.getMessageQueue();
    expect(queue[0].timestamp).toBeGreaterThanOrEqual(before);
    expect(queue[0].timestamp).toBeLessThanOrEqual(after);
  });
});
