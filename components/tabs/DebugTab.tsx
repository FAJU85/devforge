'use client';

import { useEffect, useState } from 'react';

interface SystemInfo {
  userAgent: string;
  platform: string;
  memory?: string;
  cores?: number;
}

export default function DebugTab() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    // Capture system information
    const info: SystemInfo = {
      userAgent: navigator.userAgent.substring(0, 80),
      platform: navigator.platform,
    };

    if ((navigator as any).deviceMemory) {
      info.memory = `${(navigator as any).deviceMemory} GB`;
    }

    if ((navigator as any).hardwareConcurrency) {
      info.cores = (navigator as any).hardwareConcurrency;
    }

    setSystemInfo(info);

    // Capture console logs
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    const captureLog = (level: string, args: unknown[]) => {
      const message = args
        .map((arg) =>
          typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
        )
        .join(' ');
      setLogs((prev) => [...prev.slice(-99), `[${level}] ${message}`]);
    };

    console.log = (...args) => {
      originalLog(...args);
      captureLog('LOG', args);
    };

    console.error = (...args) => {
      originalError(...args);
      captureLog('ERROR', args);
    };

    console.warn = (...args) => {
      originalWarn(...args);
      captureLog('WARN', args);
    };

    return () => {
      console.log = originalLog;
      console.error = originalError;
      console.warn = originalWarn;
    };
  }, []);

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden p-6">
      <div className="dev-card">
        <h3 className="mb-4 text-lg font-semibold">System Information</h3>
        {systemInfo && (
          <div className="space-y-2 font-mono text-sm">
            <p>Platform: <span className="text-gray-600 dark:text-gray-400">{systemInfo.platform}</span></p>
            <p>User Agent: <span className="text-gray-600 dark:text-gray-400 truncate">{systemInfo.userAgent}</span></p>
            {systemInfo.memory && <p>Memory: <span className="text-gray-600 dark:text-gray-400">{systemInfo.memory}</span></p>}
            {systemInfo.cores && <p>CPU Cores: <span className="text-gray-600 dark:text-gray-400">{systemInfo.cores}</span></p>}
            <p>Status: <span className="text-green-600">Connected</span></p>
          </div>
        )}
      </div>

      <div className="dev-card flex-1">
        <h3 className="mb-4 text-lg font-semibold">Console Output</h3>
        <div className="bg-black dark:bg-gray-900 rounded-lg p-3 font-mono text-xs text-green-400 overflow-y-auto h-full space-y-1">
          {logs.length === 0 ? (
            <p className="text-gray-600">Waiting for console output...</p>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="whitespace-pre-wrap break-words">
                {log}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
