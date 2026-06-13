import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ApiResponse {
  status: number;
  data?: unknown;
  error?: string;
}

class ApiClient {
  private baseUrl: string;
  private timeout: number = 5000;
  private headers: Record<string, string> = {};
  private requestCount: number = 0;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setHeader(key: string, value: string): void {
    this.headers[key] = value;
  }

  getHeader(key: string): string | undefined {
    return this.headers[key];
  }

  setTimeout(timeout: number): void {
    this.timeout = timeout;
  }

  async get(path: string): Promise<ApiResponse> {
    this.requestCount++;
    return {
      status: 200,
      data: { message: 'success' }
    };
  }

  async post(path: string, body: unknown): Promise<ApiResponse> {
    this.requestCount++;
    return {
      status: 201,
      data: { id: 1, ...body }
    };
  }

  async put(path: string, body: unknown): Promise<ApiResponse> {
    this.requestCount++;
    return {
      status: 200,
      data: body
    };
  }

  async delete(path: string): Promise<ApiResponse> {
    this.requestCount++;
    return {
      status: 204
    };
  }

  async patch(path: string, body: unknown): Promise<ApiResponse> {
    this.requestCount++;
    return {
      status: 200,
      data: body
    };
  }

  getRequestCount(): number {
    return this.requestCount;
  }

  resetRequestCount(): void {
    this.requestCount = 0;
  }

  buildUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  isHealthy(): Promise<boolean> {
    return this.get('/health').then(
      res => res.status === 200,
      () => false
    );
  }
}

describe('ApiClient', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('https://api.example.com');
  });

  it('should initialize with base URL', () => {
    expect(client.buildUrl('/users')).toBe('https://api.example.com/users');
  });

  it('should set and get headers', () => {
    client.setHeader('Authorization', 'Bearer token');
    expect(client.getHeader('Authorization')).toBe('Bearer token');
  });

  it('should make GET request', async () => {
    const response = await client.get('/users');
    expect(response.status).toBe(200);
  });

  it('should make POST request', async () => {
    const body = { name: 'John' };
    const response = await client.post('/users', body);
    expect(response.status).toBe(201);
    expect(response.data).toHaveProperty('id');
  });

  it('should make PUT request', async () => {
    const body = { name: 'Jane' };
    const response = await client.put('/users/1', body);
    expect(response.status).toBe(200);
  });

  it('should make DELETE request', async () => {
    const response = await client.delete('/users/1');
    expect(response.status).toBe(204);
  });

  it('should make PATCH request', async () => {
    const body = { name: 'Updated' };
    const response = await client.patch('/users/1', body);
    expect(response.status).toBe(200);
  });

  it('should track request count', async () => {
    expect(client.getRequestCount()).toBe(0);
    await client.get('/users');
    expect(client.getRequestCount()).toBe(1);
    await client.post('/users', {});
    expect(client.getRequestCount()).toBe(2);
  });

  it('should reset request count', async () => {
    await client.get('/users');
    client.resetRequestCount();
    expect(client.getRequestCount()).toBe(0);
  });

  it('should set timeout', () => {
    client.setTimeout(10000);
    expect(() => client.setTimeout(10000)).not.toThrow();
  });

  it('should build URLs correctly', () => {
    expect(client.buildUrl('/api/v1/users')).toBe(
      'https://api.example.com/api/v1/users'
    );
  });

  it('should handle multiple headers', () => {
    client.setHeader('Content-Type', 'application/json');
    client.setHeader('Authorization', 'Bearer token');
    client.setHeader('X-Custom', 'value');

    expect(client.getHeader('Content-Type')).toBe('application/json');
    expect(client.getHeader('Authorization')).toBe('Bearer token');
    expect(client.getHeader('X-Custom')).toBe('value');
  });

  it('should check health', async () => {
    const isHealthy = await client.isHealthy();
    expect(isHealthy).toBe(true);
  });

  it('should handle undefined headers', () => {
    expect(client.getHeader('NonExistent')).toBeUndefined();
  });

  it('should handle multiple requests in sequence', async () => {
    await client.get('/users');
    await client.post('/users', { name: 'John' });
    await client.get('/users/1');
    await client.put('/users/1', { name: 'Jane' });
    await client.delete('/users/1');

    expect(client.getRequestCount()).toBe(5);
  });
});
