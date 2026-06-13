/**
 * Zustand store for UI state: modals, panels, toasts
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { ToastMessage } from '@types/ui';

export interface UIState {
  // Toast messages
  toasts: ToastMessage[];
  addToast: (message: Omit<ToastMessage, 'id'>) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;

  // Modal visibility
  showSettingsModal: boolean;
  showCommandPalette: boolean;
  showDiffViewer: boolean;
  showWritePanel: boolean;
  showBatchPanel: boolean;

  // Modal setters
  setSettingsModal: (show: boolean) => void;
  setCommandPalette: (show: boolean) => void;
  setDiffViewer: (show: boolean) => void;
  setWritePanel: (show: boolean) => void;
  setBatchPanel: (show: boolean) => void;

  // Panel visibility
  sidebarCollapsed: boolean;
  showContextPanel: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setContextPanel: (show: boolean) => void;

  // Theme
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
}

let toastIdCounter = 0;

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      // Toast initial state
      toasts: [],
      addToast: (message) => {
        const id = `toast-${toastIdCounter++}`;
        const duration = message.duration ?? 3000;

        set((state) => ({
          toasts: [...state.toasts, { ...message, id }],
        }));

        // Auto-remove after duration
        if (duration > 0) {
          setTimeout(() => {
            set((state) => ({
              toasts: state.toasts.filter((t) => t.id !== id),
            }));
          }, duration);
        }

        return id;
      },
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
      clearToasts: () => set({ toasts: [] }),

      // Modal visibility initial state
      showSettingsModal: false,
      showCommandPalette: false,
      showDiffViewer: false,
      showWritePanel: false,
      showBatchPanel: false,

      // Modal setters
      setSettingsModal: (show) => set({ showSettingsModal: show }),
      setCommandPalette: (show) => set({ showCommandPalette: show }),
      setDiffViewer: (show) => set({ showDiffViewer: show }),
      setWritePanel: (show) => set({ showWritePanel: show }),
      setBatchPanel: (show) => set({ showBatchPanel: show }),

      // Panel visibility initial state
      sidebarCollapsed: false,
      showContextPanel: true,
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setContextPanel: (show) => set({ showContextPanel: show }),

      // Theme initial state
      theme: 'dark' as const,
      setTheme: (theme) => {
        set({ theme });
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('devforge-theme', theme);
      },
    }),
    { name: 'UIStore' }
  )
);
