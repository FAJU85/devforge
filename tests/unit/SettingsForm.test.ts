import { describe, it, expect, beforeEach, vi } from 'vitest';

interface FormSettings {
  apiKey: string;
  provider: string;
  model: string;
  temperature: number;
  maxTokens: number;
  theme: 'light' | 'dark';
}

class SettingsForm {
  private settings: FormSettings = {
    apiKey: '',
    provider: 'openai',
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 2000,
    theme: 'light'
  };

  private onSave: ((settings: FormSettings) => void) | null = null;
  private isDirty: boolean = false;

  getSettings(): FormSettings {
    return { ...this.settings };
  }

  setSetting<K extends keyof FormSettings>(key: K, value: FormSettings[K]): void {
    this.settings[key] = value;
    this.isDirty = true;
  }

  getSetting<K extends keyof FormSettings>(key: K): FormSettings[K] {
    return this.settings[key];
  }

  validate(): { valid: boolean; errors: Record<string, string> } {
    const errors: Record<string, string> = {};

    if (!this.settings.apiKey) {
      errors.apiKey = 'API key is required';
    }

    if (this.settings.temperature < 0 || this.settings.temperature > 2) {
      errors.temperature = 'Temperature must be between 0 and 2';
    }

    if (this.settings.maxTokens < 1 || this.settings.maxTokens > 32000) {
      errors.maxTokens = 'Max tokens must be between 1 and 32000';
    }

    return {
      valid: Object.keys(errors).length === 0,
      errors
    };
  }

  save(): boolean {
    const validation = this.validate();
    if (!validation.valid) {
      return false;
    }

    this.onSave?.(this.settings);
    this.isDirty = false;
    return true;
  }

  reset(): void {
    this.isDirty = false;
  }

  isDirty_(): boolean {
    return this.isDirty;
  }

  onSaveCallback(callback: (settings: FormSettings) => void): void {
    this.onSave = callback;
  }

  restoreDefaults(): void {
    this.settings = {
      apiKey: '',
      provider: 'openai',
      model: 'gpt-4',
      temperature: 0.7,
      maxTokens: 2000,
      theme: 'light'
    };
    this.isDirty = true;
  }
}

describe('SettingsForm', () => {
  let form: SettingsForm;

  beforeEach(() => {
    form = new SettingsForm();
  });

  it('should initialize with defaults', () => {
    const settings = form.getSettings();
    expect(settings.provider).toBe('openai');
    expect(settings.model).toBe('gpt-4');
    expect(settings.temperature).toBe(0.7);
  });

  it('should set and get settings', () => {
    form.setSetting('apiKey', 'test-key');
    expect(form.getSetting('apiKey')).toBe('test-key');
  });

  it('should track dirty state', () => {
    expect(form.isDirty_()).toBe(false);
    form.setSetting('apiKey', 'key');
    expect(form.isDirty_()).toBe(true);
  });

  it('should validate required fields', () => {
    const validation = form.validate();
    expect(validation.valid).toBe(false);
    expect(validation.errors.apiKey).toBeDefined();
  });

  it('should validate temperature range', () => {
    form.setSetting('apiKey', 'key');
    form.setSetting('temperature', 5);
    const validation = form.validate();
    expect(validation.valid).toBe(false);
    expect(validation.errors.temperature).toBeDefined();
  });

  it('should validate max tokens range', () => {
    form.setSetting('apiKey', 'key');
    form.setSetting('maxTokens', 50000);
    const validation = form.validate();
    expect(validation.valid).toBe(false);
    expect(validation.errors.maxTokens).toBeDefined();
  });

  it('should save valid form', () => {
    const callback = vi.fn();
    form.onSaveCallback(callback);
    form.setSetting('apiKey', 'valid-key');
    const saved = form.save();
    expect(saved).toBe(true);
    expect(callback).toHaveBeenCalled();
  });

  it('should not save invalid form', () => {
    const callback = vi.fn();
    form.onSaveCallback(callback);
    const saved = form.save();
    expect(saved).toBe(false);
    expect(callback).not.toHaveBeenCalled();
  });

  it('should clear dirty state after save', () => {
    form.setSetting('apiKey', 'valid-key');
    form.save();
    expect(form.isDirty_()).toBe(false);
  });

  it('should reset dirty state', () => {
    form.setSetting('apiKey', 'key');
    form.reset();
    expect(form.isDirty_()).toBe(false);
  });

  it('should restore defaults', () => {
    form.setSetting('temperature', 1.5);
    form.setSetting('theme', 'dark');
    form.restoreDefaults();
    expect(form.getSetting('temperature')).toBe(0.7);
    expect(form.getSetting('theme')).toBe('light');
  });

  it('should handle multiple settings', () => {
    form.setSetting('apiKey', 'key');
    form.setSetting('provider', 'anthropic');
    form.setSetting('model', 'claude-opus');
    form.setSetting('temperature', 0.5);

    const settings = form.getSettings();
    expect(settings.apiKey).toBe('key');
    expect(settings.provider).toBe('anthropic');
    expect(settings.model).toBe('claude-opus');
    expect(settings.temperature).toBe(0.5);
  });

  it('should validate temperature boundaries', () => {
    form.setSetting('apiKey', 'key');
    form.setSetting('temperature', 0);
    let validation = form.validate();
    expect(validation.valid).toBe(true);

    form.setSetting('temperature', 2);
    validation = form.validate();
    expect(validation.valid).toBe(true);

    form.setSetting('temperature', 2.1);
    validation = form.validate();
    expect(validation.valid).toBe(false);
  });

  it('should validate max tokens boundaries', () => {
    form.setSetting('apiKey', 'key');
    form.setSetting('maxTokens', 1);
    let validation = form.validate();
    expect(validation.valid).toBe(true);

    form.setSetting('maxTokens', 32000);
    validation = form.validate();
    expect(validation.valid).toBe(true);
  });
});
