'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Repository {
  id: number;
  name: string;
  full_name: string;
  description: string;
  url: string;
  private: boolean;
  language: string;
  stars: number;
  forks: number;
  updated_at: string;
  default_branch: string;
}

interface RepositoryListProps {
  token: string;
  onSelectRepository?: (repo: Repository) => void;
}

export default function RepositoryList({ token, onSelectRepository }: RepositoryListProps) {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [sortBy, setSortBy] = useState<'updated' | 'stars' | 'name'>('updated');

  useEffect(() => {
    loadRepositories();
  }, [page, perPage, sortBy, token]);

  const loadRepositories = async () => {
    if (!token) {
      setError('GitHub token is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/repositories/list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          per_page: perPage,
          page,
          sort: sortBy,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to load repositories');
      }

      const data = await response.json();
      setRepositories(data.repositories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repositories');
      setRepositories([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      {/* Header with Controls */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Repositories</h2>

        {/* Controls */}
        <div className="flex flex-col gap-3 rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
          <div className="flex flex-wrap gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">Sort by</label>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value as typeof sortBy);
                  setPage(1);
                }}
                className="dev-input text-sm"
              >
                <option value="updated">Recently Updated</option>
                <option value="stars">Most Stars</option>
                <option value="name">Name (A-Z)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Per Page</label>
              <select
                value={perPage}
                onChange={(e) => {
                  setPerPage(parseInt(e.target.value));
                  setPage(1);
                }}
                className="dev-input text-sm"
              >
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={loadRepositories}
                disabled={loading}
                className="dev-button-primary text-sm"
              >
                {loading ? '⏳ Loading...' : '🔄 Refresh'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg bg-red-100 p-4 text-red-800 dark:bg-red-900 dark:text-red-200">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && !repositories.length && (
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <p className="text-gray-600 dark:text-gray-400">Loading repositories...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && repositories.length === 0 && !error && (
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <p className="text-gray-600 dark:text-gray-400">No repositories found</p>
          </div>
        </div>
      )}

      {/* Repository List */}
      {repositories.length > 0 && (
        <div className="space-y-3">
          {repositories.map((repo) => (
            <div
              key={repo.id}
              onClick={() => onSelectRepository?.(repo)}
              className="dev-card cursor-pointer transition-all hover:shadow-lg"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold truncate">{repo.name}</h3>
                    {repo.private && (
                      <span className="inline-flex items-center rounded-full bg-gray-200 px-2 py-1 text-xs font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                        🔒 Private
                      </span>
                    )}
                  </div>

                  {repo.description && (
                    <p className="mb-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {repo.description}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-4 text-xs text-gray-600 dark:text-gray-400">
                    {repo.language && (
                      <span>📝 {repo.language}</span>
                    )}
                    <span>⭐ {repo.stars}</span>
                    <span>🍴 {repo.forks}</span>
                    <span>📅 {formatDate(repo.updated_at)}</span>
                  </div>
                </div>

                <a
                  href={repo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center rounded-lg bg-blue-100 p-2 text-blue-600 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800"
                  onClick={(e) => e.stopPropagation()}
                >
                  →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {repositories.length > 0 && (
        <div className="flex items-center justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1 || loading}
            className="dev-button-primary disabled:opacity-50"
          >
            ← Previous
          </button>

          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {page}
          </span>

          <button
            onClick={() => setPage(page + 1)}
            disabled={repositories.length < perPage || loading}
            className="dev-button-primary disabled:opacity-50"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
