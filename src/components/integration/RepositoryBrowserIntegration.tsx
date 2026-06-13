/**
 * Repository Browser Component Integration Example
 * Shows how to integrate useRepository hook with file explorer components
 */

import React, { useEffect, useState } from 'react';
import { useRepository } from '../hooks/useRepository';

interface RepositoryBrowserIntegrationProps {
  apiBaseUrl?: string;
  initialRepoPath?: string;
  onError?: (error: Error) => void;
}

export const RepositoryBrowserIntegration: React.FC<RepositoryBrowserIntegrationProps> = ({
  apiBaseUrl = 'http://localhost:3000/api',
  initialRepoPath = '/home/user/devforge',
  onError,
}) => {
  const repo = useRepository(apiBaseUrl);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [languages, setLanguages] = useState<Record<string, number>>({});

  // Load repository on mount
  useEffect(() => {
    const loadRepo = async () => {
      try {
        setIsLoading(true);
        setError(null);

        await repo.loadRepository(initialRepoPath);
        await repo.loadFileTree(initialRepoPath, 3);

        const langs = await repo.getLanguages(initialRepoPath);
        if (langs) {
          setLanguages(langs);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error.message);
        onError?.(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadRepo();
  }, [initialRepoPath]);

  // Load file content when selected
  useEffect(() => {
    const loadFileContent = async () => {
      if (!selectedFilePath) {
        setFileContent(null);
        return;
      }

      try {
        setIsLoading(true);
        const file = await repo.getFileContent(initialRepoPath, selectedFilePath);
        if (file?.content) {
          setFileContent(file.content);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(`Failed to load file: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadFileContent();
  }, [selectedFilePath, initialRepoPath]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      setIsLoading(true);
      const results = await repo.searchFiles(initialRepoPath, searchQuery);
      setSearchResults(results);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(`Search failed: ${error.message}`);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeRepo = async () => {
    try {
      setIsLoading(true);
      const analysis = await repo.analyzeRepository(initialRepoPath);
      console.log('Repository Analysis:', analysis);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(`Analysis failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="repository-browser-integration">
      {/* Error Display */}
      {error && (
        <div className="error-banner" role="alert">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Header */}
      <div className="repo-header">
        <h2>{initialRepoPath}</h2>
        <div className="repo-actions">
          <button onClick={handleAnalyzeRepo} disabled={isLoading}>
            Analyze Repository
          </button>
        </div>
      </div>

      {/* Language Stats */}
      {Object.keys(languages).length > 0 && (
        <div className="language-stats">
          <h4>Languages</h4>
          <ul>
            {Object.entries(languages)
              .sort((a, b) => b[1] - a[1])
              .map(([lang, count]) => (
                <li key={lang}>
                  {lang}: {count.toLocaleString()} bytes
                </li>
              ))}
          </ul>
        </div>
      )}

      <div className="repo-layout">
        {/* File Tree */}
        <div className="file-tree-panel">
          <h3>Files</h3>
          {isLoading && <div className="loading">Loading...</div>}
          {repo.fileTree && (
            <FileTreeNode
              node={repo.fileTree}
              onSelectFile={setSelectedFilePath}
              selectedPath={selectedFilePath}
            />
          )}
        </div>

        {/* File Content */}
        <div className="file-content-panel">
          {selectedFilePath ? (
            <>
              <div className="file-header">
                <h4>{selectedFilePath}</h4>
                <button
                  className="btn-close"
                  onClick={() => setSelectedFilePath(null)}
                >
                  ×
                </button>
              </div>
              {fileContent ? (
                <pre className="file-content">
                  <code>{fileContent}</code>
                </pre>
              ) : (
                <div className="loading">Loading file...</div>
              )}
            </>
          ) : (
            <div className="empty-state">Select a file to view its contents</div>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="search-panel">
        <h3>Search Files</h3>
        <div className="search-input">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search for files..."
            disabled={isLoading}
          />
          <button onClick={handleSearch} disabled={isLoading || !searchQuery.trim()}>
            Search
          </button>
        </div>

        {searchResults.length > 0 && (
          <ul className="search-results">
            {searchResults.map((result, idx) => (
              <li key={idx}>
                <button
                  onClick={() => setSelectedFilePath(result.path)}
                  className="result-item"
                >
                  {result.path}
                  {result.matches && (
                    <span className="match-count">({result.matches} matches)</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

interface FileTreeNodeProps {
  node: any;
  onSelectFile: (path: string) => void;
  selectedPath: string | null;
  depth?: number;
}

const FileTreeNode: React.FC<FileTreeNodeProps> = ({
  node,
  onSelectFile,
  selectedPath,
  depth = 0,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="tree-node" style={{ marginLeft: `${depth * 20}px` }}>
      <div
        className={`tree-node-content ${selectedPath === node.path ? 'selected' : ''}`}
      >
        {node.children && node.children.length > 0 && (
          <button className="expand-button" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? '▼' : '▶'}
          </button>
        )}
        <button
          className="node-name"
          onClick={() => {
            if (!node.children || node.children.length === 0) {
              onSelectFile(node.path);
            }
          }}
        >
          {node.name}
        </button>
      </div>

      {isOpen && node.children && node.children.length > 0 && (
        <div className="tree-children">
          {node.children.map((child: any, idx: number) => (
            <FileTreeNode
              key={idx}
              node={child}
              onSelectFile={onSelectFile}
              selectedPath={selectedPath}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};
