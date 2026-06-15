'use client';

import { type Dispatch, type SetStateAction } from 'react';
import HFLoginButton from '@/components/HFLoginButton';

interface HeaderProps {
  isDark: boolean;
  onThemeToggle: () => void;
  activeTab: string;
  setActiveTab: Dispatch<SetStateAction<'chat' | 'repo' | 'config' | 'debug'>>;
}

export default function Header({ isDark, onThemeToggle, setActiveTab }: HeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-gray-200 dark:border-[#1a2228] bg-white dark:bg-[#131920] px-6 py-4">
      <div className="flex items-center gap-3">
        <span className="text-2xl font-bold">
          <span className="text-[#e19200]">⚡</span> DevForge
        </span>
      </div>

      <div className="flex items-center gap-3">
        <HFLoginButton />
        <button
          onClick={onThemeToggle}
          className="dev-button-secondary"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? '☀️ Light' : '🌙 Dark'}
        </button>
        <button
          onClick={() => setActiveTab('config')}
          className="dev-button-primary"
          title="Open settings"
        >
          ⚙️ Settings
        </button>
      </div>
    </div>
  );
}
