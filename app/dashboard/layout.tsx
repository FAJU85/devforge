import React from 'react';
import { Sidebar } from '../components/Sidebar';

export default function DashboardLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 overflow-auto ml-64">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
