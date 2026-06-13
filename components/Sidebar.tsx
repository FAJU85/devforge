'use client';

export default function Sidebar() {
  const items = [
    { icon: '💬', label: 'Chat' },
    { icon: '📦', label: 'Repository' },
    { icon: '⚙️', label: 'Configuration' },
    { icon: '🔧', label: 'Tools' },
    { icon: '📊', label: 'Analytics' },
  ];

  return (
    <div className="w-64 border-r border-gray-200 dark:border-[#1a2228] bg-white dark:bg-[#131920] p-6 flex flex-col">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2">
        <span className="text-2xl">⚡</span>
        <span className="text-lg font-bold">DevForge</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2">
        {items.map((item) => (
          <button
            key={item.label}
            className="w-full flex items-center gap-3 rounded-lg px-4 py-2 text-left text-sm font-medium transition-colors hover:bg-gray-100 dark:hover:bg-[#1a2228]"
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Settings Footer */}
      <button className="flex w-full items-center gap-3 rounded-lg px-4 py-2 text-left text-sm font-medium transition-colors hover:bg-gray-100 dark:hover:bg-[#1a2228] border-t border-gray-200 dark:border-[#1a2228] pt-4">
        <span className="text-lg">⚙️</span>
        Settings
      </button>
    </div>
  );
}
