/**
 * Base API Client - shared HTTP client with common configuration
 */

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
  headers: Record<string, string>;
}

export interface ApiConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
  onError?: (error: Error, response?: Response) => void;
  onSuccess?: (response: Response) => void;
}

export class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private headers: Record<string, string>;
  private onError?: (error: Error, response?: Response) => void;
  private onSuccess?: (response: Response) => void;

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl;
    this.timeout = config.timeout || 30000;
    this.headers = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
    this.onError = config.onError;
    this.onSuccess = config.onSuccess;
  }

  private async withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), ms)
      ),
    ]);
  }

  async get<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await this.withTimeout(
        fetch(url, {
          ...options,
          headers: {
            ...this.headers,
            ...options.headers,
          },
        }),
        this.timeout
      );

      this.onSuccess?.(response);

      const data = await this.parseResponse<T>(response);

      return {
        data,
        status: response.status,
        headers: Object.fromEntries(response.headers.entries()),
      };
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.onError?.(err);

      return {
        error: err.message,
        status: 500,
        headers: {},
      };
    }
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    if (contentType?.includes('application/json')) {
      return response.json();
    }

    if (contentType?.includes('text')) {
      const text = await response.text();
      return text as unknown as T;
    }

    return response as unknown as T;
  }

  setAuthHeader(token: string, type: string = 'Bearer'): void {
    this.headers['Authorization'] = `${type} ${token}`;
  }

  clearAuthHeader(): void {
    delete this.headers['Authorization'];
  }

  addHeader(key: string, value: string): void {
    this.headers[key] = value;
  }

  removeHeader(key: string): void {
    delete this.headers[key];
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }
}
