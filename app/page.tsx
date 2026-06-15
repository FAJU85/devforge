'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ChatTab from '@/components/tabs/ChatTab';
import RepositoryTab from '@/components/tabs/RepositoryTab';
import ConfigurationTab from '@/components/tabs/ConfigurationTab';
import DebugTab from '@/components/tabs/DebugTab';
import GenerateTab from '@/components/tabs/GenerateTab';

type TabType = 'chat' | 'repo' | 'config' | 'debug' | 'generate';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabType>('chat');
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const prefersDark =
      localStorage.getItem('theme') === 'dark' ||
      (!localStorage.getItem('theme') &&
        window.matchMedia('(prefers-color-scheme: dark)').matches);
    setIsDark(prefersDark);
  }, []);

  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark');
  };

  const tabs = [
    { id: 'chat' as TabType, label: '💬 Chat', component: ChatTab },
    { id: 'generate' as TabType, label: '⚡ Generate', component: GenerateTab },
    { id: 'repo' as TabType, label: '📦 Repository', component: RepositoryTab },
    { id: 'config' as TabType, label: '⚙️ Configuration', component: ConfigurationTab },
    { id: 'debug' as TabType, label: '🐛 Debug', component: DebugTab },
  ];

  return (
    <div className="flex h-screen bg-white dark:bg-[#0d1116]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Header isDark={isDark} onThemeToggle={toggleTheme} activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Tab Navigation */}
        <div className="flex gap-8 border-b border-gray-200 dark:border-[#1a2228] bg-white dark:bg-[#0d1116] px-6 py-3 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`dev-tab ${activeTab === tab.id ? 'active' : ''}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'chat' && <ChatTab />}
          {activeTab === 'generate' && <GenerateTab />}
          {activeTab === 'repo' && <RepositoryTab />}
          {activeTab === 'config' && <ConfigurationTab />}
          {activeTab === 'debug' && <DebugTab />}
        </div>
      </div>
    </div>
  );
}
