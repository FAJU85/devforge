import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Config {
  apiKey: string;
  provider: string;
  model: string;
  temperature: number;
}

class ConfigService {
  private config: Config = {
    apiKey: '',
    provider: 'openai',
    model: 'gpt-4',
    temperature: 0.7
  };

  private onConfigChange: ((config: Config) => void) | null = null;

  getConfig(): Config {
    return { ...this.config };
  }

  setConfig(newConfig: Partial<Config>): void {
    this.config = { ...this.config, ...newConfig };
    this.onConfigChange?.(this.config);
  }

  getSetting<K extends keyof Config>(key: K): Config[K] {
    return this.config[key];
  }

  setSetting<K extends keyof Config>(key: K, value: Config[K]): void {
    this.setConfig({ [key]: value } as Partial<Config>);
  }

  resetToDefaults(): void {
    this.config = {
      apiKey: '',
      provider: 'openai',
      model: 'gpt-4',
      temperature: 0.7
    };
    this.onConfigChange?.(this.config);
  }

  validate(): boolean {
    return this.config.apiKey.length > 0 && this.config.temperature >= 0 && this.config.temperature <= 2;
  }

  onConfigurationChange(callback: (config: Config) => void): void {
    this.onConfigChange = callback;
  }

  export(): string {
    return JSON.stringify(this.config);
  }

  import(data: string): boolean {
    try {
      const parsed = JSON.parse(data);
      this.setConfig(parsed);
      return true;
    } catch {
      return false;
    }
  }
}

describe('ConfigService', () => {
  let service: ConfigService;

  beforeEach(() => {
    service = new ConfigService();
  });

  it('should initialize with defaults', () => {
    const config = service.getConfig();
    expect(config.provider).toBe('openai');
    expect(config.temperature).toBe(0.7);
  });

  it('should set config', () => {
    service.setConfig({ apiKey: 'test-key' });
    expect(service.getSetting('apiKey')).toBe('test-key');
  });

  it('should get setting', () => {
    expect(service.getSetting('provider')).toBe('openai');
  });

  it('should set individual setting', () => {
    service.setSetting('temperature', 0.5);
    expect(service.getSetting('temperature')).toBe(0.5);
  });

  it('should call onConfigChange callback', () => {
    const callback = vi.fn();
    service.onConfigurationChange(callback);
    service.setConfig({ apiKey: 'key' });
    expect(callback).toHaveBeenCalled();
  });

  it('should validate config', () => {
    expect(service.validate()).toBe(false);
    service.setSetting('apiKey', 'valid-key');
    expect(service.validate()).toBe(true);
  });

  it('should reset to defaults', () => {
    service.setConfig({ temperature: 1.5, apiKey: 'key' });
    service.resetToDefaults();
    expect(service.getSetting('temperature')).toBe(0.7);
    expect(service.getSetting('apiKey')).toBe('');
  });

  it('should export config', () => {
    service.setConfig({ apiKey: 'test-key' });
    const exported = service.export();
    expect(exported).toContain('test-key');
  });

  it('should import config', () => {
    const data = JSON.stringify({ apiKey: 'imported-key', temperature: 0.9 });
    expect(service.import(data)).toBe(true);
    expect(service.getSetting('apiKey')).toBe('imported-key');
  });

  it('should handle invalid import', () => {
    expect(service.import('invalid json')).toBe(false);
  });
});
