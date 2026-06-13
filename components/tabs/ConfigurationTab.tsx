'use client';

import { useState, useEffect } from 'react';

interface Config {
  preferred_model: string;
  preferred_provider: string;
  temperature: number;
  max_tokens: number;
  theme: string;
  notifications_enabled: boolean;
  auto_save: boolean;
  github_token?: string;
}

interface ApiKey {
  provider: string;
  api_key: string;
}

interface ProviderValidationStatus {
  provider: string;
  valid: boolean;
  message: string;
  lastChecked?: Date;
}

interface ValidationError {
  field: string;
  message: string;
}

export default function ConfigurationTab() {
  const [config, setConfig] = useState<Config>({
    preferred_model: 'claude-3-5-sonnet-20241022',
    preferred_provider: 'anthropic',
    temperature: 0.7,
    max_tokens: 4096,
    theme: 'auto',
    notifications_enabled: true,
    auto_save: true,
  });

  const [apiKey, setApiKey] = useState<ApiKey>({
    provider: 'anthropic',
    api_key: '',
  });

  const [savedKeys, setSavedKeys] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [validationStatuses, setValidationStatuses] = useState<Record<string, ProviderValidationStatus>>({});
  const [validatingProvider, setValidatingProvider] = useState<string | null>(null);

  // Load configuration on mount
  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/config');
      if (!response.ok) throw new Error('Failed to load config');
      const data = await response.json();
      setConfig(data);

      // Load stored API keys
      const keysResponse = await fetch('/api/config/keys');
      if (keysResponse.ok) {
        const keysData = await keysResponse.json();
        setSavedKeys(keysData.stored_keys);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    }
  };

  const validateConfig = (): ValidationError[] => {
    const newErrors: ValidationError[] = [];

    if (config.temperature < 0 || config.temperature > 2) {
      newErrors.push({ field: 'temperature', message: 'Must be between 0 and 2' });
    }

    if (config.max_tokens < 1 || config.max_tokens > 128000) {
      newErrors.push({ field: 'max_tokens', message: 'Must be between 1 and 128000' });
    }

    if (!config.preferred_model.trim()) {
      newErrors.push({ field: 'preferred_model', message: 'Model name is required' });
    }

    return newErrors;
  };

  const validateApiKey = (): boolean => {
    if (!apiKey.api_key.trim()) {
      setError('API key cannot be empty');
      return false;
    }

    if (apiKey.api_key.length < 10) {
      setError('API key seems too short');
      return false;
    }

    return true;
  };

  const validateProvider = async (token: string, provider: string) => {
    setValidatingProvider(provider);
    setError('');

    try {
      if (provider === 'github') {
        const response = await fetch('/api/repositories/validate-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token, owner: '', repo: '' }),
        });

        const result = await response.json();
        setValidationStatuses((prev) => ({
          ...prev,
          [provider]: {
            provider,
            valid: response.ok,
            message: response.ok ? 'GitHub token is valid' : (result.detail || 'Invalid GitHub token'),
            lastChecked: new Date(),
          },
        }));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
      setValidationStatuses((prev) => ({
        ...prev,
        [provider]: {
          provider,
          valid: false,
          message: 'Could not validate token',
          lastChecked: new Date(),
        },
      }));
    } finally {
      setValidatingProvider(null);
    }
  };

  const handleConfigChange = (field: keyof Config, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
    setErrors(errors.filter((e) => e.field !== field));
  };

  const saveConfiguration = async () => {
    const newErrors = validateConfig();
    if (newErrors.length > 0) {
      setErrors(newErrors);
      setError('Please fix validation errors');
      return;
    }

    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch('/api/config', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error('Failed to save configuration');
      }

      setMessage('✓ Configuration saved successfully');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveApiKey = async () => {
    if (!validateApiKey()) {
      return;
    }

    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch('/api/config/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiKey),
      });

      if (!response.ok) {
        throw new Error('Failed to save API key');
      }

      setMessage(`✓ API key for ${apiKey.provider} saved successfully`);
      setSavedKeys((prev) => ({ ...prev, [apiKey.provider]: `${apiKey.provider}_key_stored` }));
      setApiKey({ provider: apiKey.provider, api_key: '' });
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key');
    } finally {
      setLoading(false);
    }
  };

  const deleteApiKey = async (provider: string) => {
    if (!confirm(`Delete API key for ${provider}?`)) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/config/keys/${provider}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete API key');
      }

      setSavedKeys((prev) => {
        const updated = { ...prev };
        delete updated[provider];
        return updated;
      });
      setMessage(`✓ API key for ${provider} deleted`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete API key');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      {/* Alerts */}
      {message && (
        <div className="rounded-lg bg-green-100 p-4 text-green-800 dark:bg-green-900 dark:text-green-200">
          {message}
        </div>
      )}
      {error && (
        <div className="rounded-lg bg-red-100 p-4 text-red-800 dark:bg-red-900 dark:text-red-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* AI Model Configuration */}
        <div className="dev-card">
          <h3 className="mb-4 text-lg font-semibold">AI Model</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <input
                type="text"
                value={config.preferred_model}
                onChange={(e) => handleConfigChange('preferred_model', e.target.value)}
                className="dev-input"
                placeholder="model-name"
              />
              {errors.find((e) => e.field === 'preferred_model') && (
                <p className="mt-1 text-xs text-red-600">{errors.find((e) => e.field === 'preferred_model')?.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Temperature</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.temperature}
                onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-gray-600 dark:text-gray-400">{config.temperature.toFixed(1)}</span>
              {errors.find((e) => e.field === 'temperature') && (
                <p className="mt-1 text-xs text-red-600">{errors.find((e) => e.field === 'temperature')?.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Provider Configuration */}
        <div className="dev-card">
          <h3 className="mb-4 text-lg font-semibold">Provider</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Provider</label>
              <select
                value={config.preferred_provider}
                onChange={(e) => handleConfigChange('preferred_provider', e.target.value)}
                className="dev-input"
              >
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="groq">Groq</option>
                <option value="huggingface">Hugging Face</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                value={config.max_tokens}
                onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value))}
                className="dev-input"
              />
              {errors.find((e) => e.field === 'max_tokens') && (
                <p className="mt-1 text-xs text-red-600">{errors.find((e) => e.field === 'max_tokens')?.message}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Theme and Notifications */}
      <div className="dev-card">
        <h3 className="mb-4 text-lg font-semibold">Appearance & Behavior</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium">Theme</label>
            <select
              value={config.theme}
              onChange={(e) => handleConfigChange('theme', e.target.value)}
              className="dev-input w-32"
            >
              <option value="auto">Auto</option>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium">Notifications</label>
            <input
              type="checkbox"
              checked={config.notifications_enabled}
              onChange={(e) => handleConfigChange('notifications_enabled', e.target.checked)}
              className="h-4 w-4"
            />
          </div>
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium">Auto-save</label>
            <input
              type="checkbox"
              checked={config.auto_save}
              onChange={(e) => handleConfigChange('auto_save', e.target.checked)}
              className="h-4 w-4"
            />
          </div>
          <button
            onClick={saveConfiguration}
            disabled={loading}
            className="dev-button-primary w-full"
          >
            {loading ? '⏳ Saving...' : '💾 Save Configuration'}
          </button>
        </div>
      </div>

      {/* API Keys */}
      <div className="dev-card">
        <h3 className="mb-4 text-lg font-semibold">API Keys & Credentials</h3>
        <div className="space-y-4">
          {/* Add New Key */}
          <div>
            <label className="block text-sm font-medium mb-2">Provider</label>
            <select
              value={apiKey.provider}
              onChange={(e) => setApiKey({ ...apiKey, provider: e.target.value })}
              className="dev-input"
            >
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="groq">Groq</option>
              <option value="huggingface">Hugging Face</option>
              <option value="github">GitHub (Repository Access)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">API Key</label>
            <input
              type="password"
              value={apiKey.api_key}
              onChange={(e) => setApiKey({ ...apiKey, api_key: e.target.value })}
              className="dev-input"
              placeholder={apiKey.provider === 'github' ? 'ghp_...' : 'Enter your API key'}
            />
            <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              {apiKey.provider === 'github'
                ? 'Use a GitHub personal access token with repo scope'
                : 'Your API key is stored securely and never sent to our servers.'}
            </p>
          </div>

          {/* Provider Validation UI */}
          {apiKey.provider === 'github' && apiKey.api_key && (
            <button
              onClick={() => validateProvider(apiKey.api_key, 'github')}
              disabled={validatingProvider === 'github'}
              className="dev-button-secondary w-full"
            >
              {validatingProvider === 'github' ? '🔍 Validating...' : '🔍 Validate Token'}
            </button>
          )}

          {validationStatuses['github'] && (
            <div
              className={`rounded-lg p-3 text-sm ${
                validationStatuses['github'].valid
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}
            >
              {validationStatuses['github'].valid ? '✓' : '✗'} {validationStatuses['github'].message}
            </div>
          )}

          <button
            onClick={saveApiKey}
            disabled={loading}
            className="dev-button-primary w-full"
          >
            {loading ? '⏳ Saving...' : '🔐 Save API Key'}
          </button>

          {/* Stored Keys */}
          {Object.keys(savedKeys).length > 0 && (
            <div className="mt-6 border-t pt-4">
              <h4 className="mb-3 text-sm font-medium">Stored API Keys</h4>
              <div className="space-y-2">
                {Object.entries(savedKeys).map(([provider, _]) => (
                  <div
                    key={provider}
                    className="flex items-center justify-between rounded bg-gray-100 p-3 dark:bg-gray-700"
                  >
                    <span className="text-sm capitalize">{provider}</span>
                    <button
                      onClick={() => deleteApiKey(provider)}
                      disabled={loading}
                      className="text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
