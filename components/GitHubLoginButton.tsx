'use client';

import { useState, useEffect } from 'react';

interface GitHubUser {
  username: string;
  name: string;
  avatar_url: string;
  profile_url: string;
  has_github_token: boolean;
}

export default function GitHubLoginButton() {
  const [user, setUser] = useState<GitHubUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/github/me')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return null;

  if (user) {
    return (
      <div className="flex items-center gap-2">
        {user.avatar_url && (
          <img
            src={user.avatar_url}
            alt={user.username}
            className="w-7 h-7 rounded-full border border-gray-300 dark:border-gray-600"
          />
        )}
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200 hidden sm:block">
          {user.username}
        </span>
        <button
          onClick={() =>
            fetch('/api/auth/github/logout', { method: 'POST' }).then(() => {
              setUser(null);
              window.location.reload();
            })
          }
          className="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600
                     text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800
                     transition-colors"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <a
      href="/api/auth/github/login"
      className="flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold text-sm
                 bg-gray-900 dark:bg-white text-white dark:text-gray-900
                 hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
    >
      <svg viewBox="0 0 16 16" className="w-4 h-4 fill-current" aria-hidden="true">
        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
      </svg>
      Sign in with GitHub
    </a>
  );
}
