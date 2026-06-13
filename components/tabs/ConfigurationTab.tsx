'use client';

import { useState } from 'react';

export default function ConfigurationTab() {
  const [config, setConfig] = useState({
    model: 'meta-llama/Llama-2-7b-chat-hf',
    provider: 'huggingface',
    temperature: 0.7,
    maxTokens: 512,
    apiKey: '',
  });

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* AI Model Configuration */}
        <div className="dev-card">
          <h3 className="mb-4 text-lg font-semibold">AI Model</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <input
                type="text"
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
                className="dev-input"
                placeholder="model-name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Temperature</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.temperature}
                onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
              <span className="text-xs text-gray-600 dark:text-gray-400">{config.temperature}</span>
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
                value={config.provider}
                onChange={(e) => setConfig({ ...config, provider: e.target.value })}
                className="dev-input"
              >
                <option value="huggingface">Hugging Face</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="groq">Groq</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                value={config.maxTokens}
                onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) })}
                className="dev-input"
              />
            </div>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className="dev-card">
        <h3 className="mb-4 text-lg font-semibold">API Keys & Credentials</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">API Key</label>
            <input
              type="password"
              value={config.apiKey}
              onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
              className="dev-input"
              placeholder="Enter your API key"
            />
            <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              Your API key is stored locally and never sent to our servers.
            </p>
          </div>
          <button className="dev-button-primary">💾 Save Configuration</button>
        </div>
      </div>
    </div>
  );
}
