'use client';

export default function RepositoryTab() {
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-6">
      <div className="dev-card">
        <h2 className="mb-4 text-xl font-bold">Repository Browser</h2>
        <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
          Connect your GitHub repository to start working with your code.
        </p>
        <button className="dev-button-primary">
          🔗 Connect Repository
        </button>
      </div>

      <div className="dev-card">
        <h3 className="mb-4 text-lg font-semibold">Recent Repositories</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          No repositories connected yet. Use the button above to add one.
        </p>
      </div>
    </div>
  );
}
