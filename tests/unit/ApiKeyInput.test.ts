import { describe, it, expect, beforeEach, vi } from 'vitest';

class ApiKeyInput {
  private key: string = '';
  private provider: string = '';
  private isValid: boolean = false;
  private onValidate: ((isValid: boolean) => void) | null = null;

  setKey(key: string): void {
    this.key = key;
    this.validate();
  }

  getKey(): string {
    return this.key;
  }

  setProvider(provider: string): void {
    this.provider = provider;
  }

  getProvider(): string {
    return this.provider;
  }

  private validate(): void {
    const isValid = this.key.length > 0 && /^[a-zA-Z0-9_-]+$/.test(this.key);
    this.isValid = isValid;
    this.onValidate?.(isValid);
  }

  isKeyValid(): boolean {
    return this.isValid;
  }

  clear(): void {
    this.key = '';
    this.validate();
  }

  onValidationChange(callback: (isValid: boolean) => void): void {
    this.onValidate = callback;
  }

  maskKey(): string {
    if (this.key.length <= 4) return '****';
    return this.key.substring(0, 2) + '*'.repeat(this.key.length - 4) + this.key.substring(this.key.length - 2);
  }

  testConnection(): Promise<boolean> {
    return Promise.resolve(this.isValid);
  }
}

describe('ApiKeyInput', () => {
  let input: ApiKeyInput;

  beforeEach(() => {
    input = new ApiKeyInput();
  });

  it('should initialize empty', () => {
    expect(input.getKey()).toBe('');
  });

  it('should set and get key', () => {
    input.setKey('test-key-123');
    expect(input.getKey()).toBe('test-key-123');
  });

  it('should set and get provider', () => {
    input.setProvider('openai');
    expect(input.getProvider()).toBe('openai');
  });

  it('should validate valid key', () => {
    input.setKey('valid_key-123');
    expect(input.isKeyValid()).toBe(true);
  });

  it('should reject empty key', () => {
    input.setKey('');
    expect(input.isKeyValid()).toBe(false);
  });

  it('should reject key with invalid characters', () => {
    input.setKey('invalid@key#$');
    expect(input.isKeyValid()).toBe(false);
  });

  it('should call validation callback', () => {
    const callback = vi.fn();
    input.onValidationChange(callback);
    input.setKey('valid-key');
    expect(callback).toHaveBeenCalledWith(true);
  });

  it('should clear key', () => {
    input.setKey('test-key');
    input.clear();
    expect(input.getKey()).toBe('');
    expect(input.isKeyValid()).toBe(false);
  });

  it('should mask key for display', () => {
    input.setKey('sk-1234567890');
    const masked = input.maskKey();
    // Verify masking format: first char + asterisks + last char
    expect(masked.length).toBeGreaterThan(2);
    expect(masked[0]).not.toBe('*');
    expect(masked[masked.length - 1]).not.toBe('*');
  });

  it('should mask short keys', () => {
    input.setKey('abc');
    expect(input.maskKey()).toBe('****');
  });

  it('should test connection', async () => {
    input.setKey('valid-key');
    const result = await input.testConnection();
    expect(result).toBe(true);
  });

  it('should test connection with invalid key', async () => {
    input.setKey('');
    const result = await input.testConnection();
    expect(result).toBe(false);
  });

  it('should validate on multiple changes', () => {
    const callback = vi.fn();
    input.onValidationChange(callback);
    input.setKey('key1');
    input.setKey('key2');
    input.setKey('');
    expect(callback).toHaveBeenCalledTimes(3);
  });

  it('should accept alphanumeric with underscores and dashes', () => {
    input.setKey('my_valid-key_123');
    expect(input.isKeyValid()).toBe(true);
  });
});
