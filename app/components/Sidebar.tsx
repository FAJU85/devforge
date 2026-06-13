import React from 'react';
import Link from 'next/link';
import {
  Home,
  CheckSquare,
  Plus,
  Code2,
  Settings,
  LogOut,
  LayoutGrid,
  Zap
} from 'lucide-react';

export function Sidebar() {
  const menuItems = [
    { icon: Home, label: 'Dashboard', href: '/dashboard' },
    { icon: CheckSquare, label: 'Tasks', href: '/tasks' },
    { icon: Plus, label: 'Create Task', href: '/create-task' },
    { icon: Code2, label: 'API Docs', href: '/api' },
    { icon: Settings, label: 'Settings', href: '/settings' }
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-lg bg-[#76cd1d] flex items-center justify-center">
            <Zap className="w-6 h-6 text-black" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">
              DevForge
            </h1>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              v2.0.0
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        {menuItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition group"
          >
            <item.icon className="w-5 h-5 group-hover:text-[#76cd1d] transition" />
            <span className="font-medium">{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 space-y-2">
        <div className="px-4 py-3 rounded-lg bg-slate-50 dark:bg-slate-900">
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Status: <span className="text-green-600 font-bold">Connected</span>
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
            All APIs online
          </p>
        </div>
        <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
