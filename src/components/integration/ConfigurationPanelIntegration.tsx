/**
 * Configuration Panel Component Integration Example
 * Shows how to integrate useConfig hook with settings and configuration components
 */

import React, { useEffect, useState } from 'react';
import { useConfig } from '../hooks/useConfig';

interface ConfigurationPanelIntegrationProps {
  apiBaseUrl?: string;
  onError?: (error: Error) => void;
}

export const ConfigurationPanelIntegration: React.FC<ConfigurationPanelIntegrationProps> = ({
  apiBaseUrl = 'http://localhost:3000/api',
  onError,
}) => {
  const config = useConfig(apiBaseUrl);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'providers' | 'models' | 'features'>('providers');

  // Load configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        setIsLoading(true);
        setError(null);

        await Promise.all([
          config.loadProviders(),
          config.loadModels(),
          config.loadFeatureFlags(),
        ]);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error.message);
        onError?.(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadConfig();
  }, []);

  const handleProviderTest = async (providerId: string) => {
    try {
      setIsLoading(true);
      const connected = await config.testProviderConnection(providerId);
      setError(connected ? null : `Provider ${providerId} is not responding`);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(`Connection test failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleFeature = async (flagName: string) => {
    try {
      config.toggleFeatureFlag(flagName);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(`Failed to toggle feature: ${error.message}`);
    }
  };

  return (
    <div className="configuration-panel-integration">
      {/* Error Display */}
      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Tabs */}
      <div className="config-tabs">
        <button
          className={activeTab === 'providers' ? 'active' : ''}
          onClick={() => setActiveTab('providers')}
        >
          Providers
        </button>
        <button
          className={activeTab === 'models' ? 'active' : ''}
          onClick={() => setActiveTab('models')}
        >
          Models
        </button>
        <button
          className={activeTab === 'features' ? 'active' : ''}
          onClick={() => setActiveTab('features')}
        >
          Feature Flags
        </button>
      </div>

      {isLoading && <div className="loading">Loading configuration...</div>}

      {/* Providers Tab */}
      {activeTab === 'providers' && !isLoading && (
        <div className="config-section">
          <h3>API Providers</h3>
          {config.providers.length === 0 ? (
            <div className="empty-state">No providers configured</div>
          ) : (
            <div className="providers-list">
              {config.providers.map((provider) => (
                <div
                  key={provider.id}
                  className={`provider-card ${provider.isActive ? 'active' : ''}`}
                >
                  <div className="provider-header">
                    <h4>{provider.name}</h4>
                    <button
                      className={`btn-status ${provider.isActive ? 'active' : ''}`}
                      onClick={() => config.setActiveProvider(provider.id)}
                    >
                      {provider.isActive ? '✓ Active' : 'Inactive'}
                    </button>
                  </div>
                  <div className="provider-info">
                    <p>
                      <strong>API URL:</strong> {provider.baseUrl}
                    </p>
                    {provider.rateLimit && (
                      <p>
                        <strong>Rate Limit:</strong> {provider.rateLimit} req/min
                      </p>
                    )}
                  </div>
                  <button
                    className="btn-test"
                    onClick={() => handleProviderTest(provider.id)}
                    disabled={isLoading}
                  >
                    Test Connection
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && !isLoading && (
        <div className="config-section">
          <h3>Available Models</h3>
          {config.models.length === 0 ? (
            <div className="empty-state">No models configured</div>
          ) : (
            <div className="models-list">
              {config.models.map((model) => (
                <div
                  key={model.id}
                  className={`model-card ${model.id === config.activeModel?.id ? 'active' : ''}`}
                >
                  <div className="model-header">
                    <h4>{model.name}</h4>
                    <button
                      className={`btn-select ${model.id === config.activeModel?.id ? 'selected' : ''}`}
                      onClick={() => config.setActiveModel(model.id)}
                    >
                      {model.id === config.activeModel?.id ? '✓ Selected' : 'Select'}
                    </button>
                  </div>
                  <div className="model-info">
                    <p>
                      <strong>Provider:</strong> {model.provider}
                    </p>
                    <p>
                      <strong>Context Window:</strong> {model.contextWindow.toLocaleString()} tokens
                    </p>
                    <p>
                      <strong>Cost:</strong> ${model.costPer1kTokens}/1K tokens
                    </p>
                    {model.capabilities && model.capabilities.length > 0 && (
                      <div className="capabilities">
                        <strong>Capabilities:</strong>
                        <ul>
                          {model.capabilities.map((cap, idx) => (
                            <li key={idx}>{cap}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Feature Flags Tab */}
      {activeTab === 'features' && !isLoading && (
        <div className="config-section">
          <h3>Feature Flags</h3>
          <div className="features-list">
            {config.featureFlags &&
              Object.entries(config.featureFlags).map(([flagName, enabled]) => (
                <div key={flagName} className="feature-item">
                  <label className="feature-label">
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={() => handleToggleFeature(flagName)}
                      disabled={isLoading}
                    />
                    <span className="flag-name">{flagName}</span>
                  </label>
                  <span className={`badge ${enabled ? 'enabled' : 'disabled'}`}>
                    {enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* System Status */}
      <div className="system-status">
        <h4>System Status</h4>
        <button
          onClick={async () => {
            try {
              const status = await config.getSystemStatus();
              console.log('System Status:', status);
            } catch (err) {
              const error = err instanceof Error ? err : new Error(String(err));
              setError(`Failed to get status: ${error.message}`);
            }
          }}
          disabled={isLoading}
        >
          Check Status
        </button>
      </div>
    </div>
  );
};
