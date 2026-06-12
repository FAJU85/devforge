/**
 * Context Manager Component Integration Example
 * Shows how to integrate useContextValue hook with context management
 */

import React, { useState } from 'react';
import { useContextValue } from '../hooks/useContext';

interface ContextManagerIntegrationProps {
  repoPath: string;
  apiBaseUrl?: string;
  onError?: (error: Error) => void;
}

export const ContextManagerIntegration: React.FC<ContextManagerIntegrationProps> = ({
  repoPath,
  apiBaseUrl = 'http://localhost:3000/api',
  onError,
}) => {
  const context = useContextValue(apiBaseUrl);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [maxTokenInput, setMaxTokenInput] = useState(context.maxTokens.toString());

  const handleAddFile = async (filePath: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const file = await context.addFile(repoPath, filePath);
      if (file) {
        console.log('File added to context:', file);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveFile = async (fileId: string) => {
    try {
      setIsLoading(true);
      await context.removeFile(fileId);
      console.log('File removed from context');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchAndAdd = async () => {
    if (!searchQuery.trim()) {
      return;
    }

    try {
      setIsLoading(true);
      const files = await context.searchAndAddFiles(repoPath, searchQuery, 5);
      console.log(`Added ${files.length} files to context`);
      setSearchQuery('');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMaxTokenChange = async () => {
    try {
      const newMax = parseInt(maxTokenInput, 10);
      if (newMax > 0) {
        context.setMaxTokens(newMax);
        setError(null);
      } else {
        setError('Max tokens must be greater than 0');
      }
    } catch (err) {
      setError('Invalid token value');
    }
  };

  const summary = context.getContextSummary();

  return (
    <div className="context-manager-integration">
      {/* Error Display */}
      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Token Usage */}
      <div className="context-stats">
        <h3>Context Usage</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Files</div>
            <div className="stat-value">{summary.filesCount}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tokens Used</div>
            <div className="stat-value">{summary.totalTokens.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Available</div>
            <div className="stat-value">{summary.availableTokens.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Usage</div>
            <div className="stat-value">{summary.percentageUsed.toFixed(1)}%</div>
          </div>
        </div>

        {/* Token Bar */}
        <div className="token-bar">
          <div
            className="token-used"
            style={{ width: `${summary.percentageUsed}%` }}
          />
        </div>
        <div className="token-label">
          {summary.totalTokens} / {summary.maxTokens} tokens
        </div>
      </div>

      {/* Max Token Configuration */}
      <div className="max-token-config">
        <label>
          Max Tokens:
          <input
            type="number"
            value={maxTokenInput}
            onChange={(e) => setMaxTokenInput(e.target.value)}
            disabled={isLoading}
            min="100"
            step="100"
          />
        </label>
        <button onClick={handleMaxTokenChange} disabled={isLoading}>
          Update
        </button>
      </div>

      {/* Search and Add */}
      <div className="search-add-section">
        <h4>Search and Add Files</h4>
        <div className="search-input">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearchAndAdd()}
            placeholder="Search for files (e.g., 'component', 'store')..."
            disabled={isLoading}
          />
          <button
            onClick={handleSearchAndAdd}
            disabled={isLoading || !searchQuery.trim() || !context.hasRoom(100)}
          >
            Search & Add
          </button>
        </div>
        {!context.hasRoom(100) && (
          <div className="warning">Context is full. Remove files to add more.</div>
        )}
      </div>

      {/* Context Files */}
      <div className="context-files">
        <h4>Files in Context</h4>
        {context.files.length === 0 ? (
          <div className="empty-state">No files in context</div>
        ) : (
          <div className="files-list">
            {context.files.map((file) => (
              <div key={file.id} className="file-item">
                <div className="file-info">
                  <div className="file-path">{file.path}</div>
                  <div className="file-stats">
                    {file.tokens} tokens
                    {file.language && <span className="language">{file.language}</span>}
                  </div>
                </div>
                <button
                  className="btn-remove"
                  onClick={() => handleRemoveFile(file.id)}
                  disabled={isLoading}
                  title="Remove from context"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Context Management Actions */}
      <div className="context-actions">
        <button
          onClick={() => context.clearContext()}
          disabled={isLoading || context.files.length === 0}
          className="btn-danger"
        >
          Clear All Files
        </button>
      </div>

      {/* Usage Tips */}
      <div className="usage-tips">
        <h4>Tips</h4>
        <ul>
          <li>Add related files to provide better context for AI analysis</li>
          <li>Monitor token usage to avoid exceeding context limits</li>
          <li>Use search to quickly find and add relevant files</li>
          <li>Remove unused files to make room for new ones</li>
        </ul>
      </div>
    </div>
  );
};
