'use client';

import { useState, useEffect } from 'react';

interface HFUser {
  username: string;
  name: string;
  avatar_url: string;
  profile_url: string;
  has_hf_token: boolean;
}

export default function HFLoginButton() {
  const [user, setUser] = useState<HFUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/hf/me')
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
            fetch('/api/auth/hf/logout', { method: 'POST' }).then(() => {
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
      href="/api/auth/hf/login"
      className="flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold text-sm
                 bg-[#FFD21E] text-gray-900 hover:bg-[#FFE066] transition-colors"
    >
      <svg viewBox="0 0 95 88" className="w-4 h-4 fill-current" aria-hidden="true">
        <path d="M47.2 0C21.2 0 0 19.7 0 44c0 8.8 2.7 17 7.3 23.8L0 88l21.7-6.9C29.3 84.8 38 87 47.2 87 73.2 87 95 67.3 95 43S73.2 0 47.2 0z" />
      </svg>
      Sign in with Hugging Face
    </a>
  );
}
