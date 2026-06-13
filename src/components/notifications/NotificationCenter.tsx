'use client';

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface NotificationCenterProps {
  userId: string;
  maxNotifications?: number;
}

export default function NotificationCenter({
  userId,
  maxNotifications = 10,
}: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  // Initialize WebSocket
  const wsUrl = typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${userId}`
    : 'ws://localhost:3000/ws/default';

  const { on } = useWebSocket({
    url: wsUrl,
    autoConnect: true,
  });

  // Setup notification listener
  useEffect(() => {
    const unsubscribe = on('message', (message) => {
      const data = message.data as any;

      // Only process if it's a notification type message
      if (data.type !== 'notification') {
        return;
      }

      const notification: Notification = {
        id: `notif-${Date.now()}`,
        type: data.type || 'info',
        title: data.title || 'Notification',
        message: data.message || '',
        timestamp: new Date(),
        read: false,
      };

      setNotifications((prev) => {
        const updated = [notification, ...prev];
        return updated.slice(0, maxNotifications);
      });

      setUnreadCount((prev) => prev + 1);
    });

    return () => {
      unsubscribe?.();
    };
  }, [on, maxNotifications]);

  const getNotificationIcon = (type: string): string => {
    switch (type) {
      case 'success':
        return '✓';
      case 'warning':
        return '⚠';
      case 'error':
        return '✗';
      default:
        return 'ℹ';
    }
  };

  const getNotificationColor = (type: string): string => {
    switch (type) {
      case 'success':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }
  };

  const handleMarkAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((notif) =>
        notif.id === id ? { ...notif, read: true } : notif
      )
    );

    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  const handleDismiss = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id));
  }, []);

  const handleClearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative rounded-lg bg-gray-100 p-2 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700"
      >
        🔔
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center h-5 w-5 rounded-full bg-red-600 text-xs font-bold text-white">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-12 z-50 w-80 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-900">
          {/* Header */}
          <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                Notifications
              </h3>
              {notifications.length > 0 && (
                <button
                  onClick={handleClearAll}
                  className="text-xs text-blue-600 hover:underline dark:text-blue-400"
                >
                  Clear all
                </button>
              )}
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-600 dark:text-gray-400">
                <p className="text-sm">No notifications</p>
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`border-b border-gray-200 p-3 dark:border-gray-700 ${
                    notif.read ? 'opacity-60' : ''
                  }`}
                >
                  <div className="flex gap-3">
                    {/* Icon */}
                    <div
                      className={`flex-shrink-0 rounded-full p-2 text-lg ${getNotificationColor(notif.type)}`}
                    >
                      {getNotificationIcon(notif.type)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                        {notif.title}
                      </h4>
                      <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                        {notif.message}
                      </p>
                      <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                        {notif.timestamp.toLocaleTimeString()}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                      {notif.action && (
                        <button
                          onClick={notif.action.onClick}
                          className="text-xs text-blue-600 hover:underline dark:text-blue-400"
                        >
                          {notif.action.label}
                        </button>
                      )}
                      {!notif.read && (
                        <button
                          onClick={() => handleMarkAsRead(notif.id)}
                          className="text-xs text-gray-600 hover:underline dark:text-gray-400"
                        >
                          Mark read
                        </button>
                      )}
                      <button
                        onClick={() => handleDismiss(notif.id)}
                        className="text-xs text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
