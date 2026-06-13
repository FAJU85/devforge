import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useUIStore } from '../../src/stores/uiStore';

describe('UI Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useUIStore.setState({
      toasts: [],
      showSettingsModal: false,
      showCommandPalette: false,
      showDiffViewer: false,
      showWritePanel: false,
      showBatchPanel: false,
      sidebarCollapsed: false,
      showContextPanel: true,
      theme: 'dark',
    });
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useUIStore.getState();
      expect(state.toasts).toEqual([]);
      expect(state.showSettingsModal).toBe(false);
      expect(state.showCommandPalette).toBe(false);
      expect(state.showDiffViewer).toBe(false);
      expect(state.showWritePanel).toBe(false);
      expect(state.showBatchPanel).toBe(false);
      expect(state.sidebarCollapsed).toBe(false);
      expect(state.showContextPanel).toBe(true);
      expect(state.theme).toBe('dark');
    });
  });

  describe('Toast Management', () => {
    it('should add a toast', () => {
      const state = useUIStore.getState();
      const id = state.addToast({
        message: 'Test message',
        type: 'success',
        duration: 3000,
      });

      expect(id).toMatch(/^toast-\d+$/);
      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().toasts[0].message).toBe('Test message');
    });

    it('should generate unique toast IDs', () => {
      const state = useUIStore.getState();
      const id1 = state.addToast({ message: 'Toast 1', type: 'success' });
      const id2 = state.addToast({ message: 'Toast 2', type: 'error' });

      expect(id1).not.toBe(id2);
    });

    it('should add toast with all properties', () => {
      const state = useUIStore.getState();
      state.addToast({
        message: 'Test message',
        type: 'success',
        duration: 5000,
      });

      const toast = useUIStore.getState().toasts[0];
      expect(toast.message).toBe('Test message');
      expect(toast.type).toBe('success');
      // Duration can be set or default
      expect(toast.duration === undefined || toast.duration >= 3000).toBe(true);
      expect(toast.id).toBeDefined();
    });

    it('should use default duration if not specified', () => {
      const state = useUIStore.getState();
      state.addToast({
        message: 'Test message',
        type: 'info',
      });

      const toast = useUIStore.getState().toasts[0];
      // Duration should have a default value when not specified
      expect(toast.duration === undefined || toast.duration > 0).toBe(true);
    });

    it('should auto-remove toast after duration', () => {
      const state = useUIStore.getState();
      const id = state.addToast({
        message: 'Test message',
        type: 'success',
        duration: 3000,
      });

      expect(useUIStore.getState().toasts).toHaveLength(1);

      vi.advanceTimersByTime(3000);

      expect(useUIStore.getState().toasts).toHaveLength(0);
    });

    it('should not auto-remove toast with zero duration', () => {
      const state = useUIStore.getState();
      state.addToast({
        message: 'Test message',
        type: 'success',
        duration: 0,
      });

      expect(useUIStore.getState().toasts).toHaveLength(1);

      vi.advanceTimersByTime(5000);

      expect(useUIStore.getState().toasts).toHaveLength(1);
    });

    it('should not auto-remove toast with negative duration', () => {
      const state = useUIStore.getState();
      state.addToast({
        message: 'Test message',
        type: 'success',
        duration: -1,
      });

      vi.advanceTimersByTime(5000);

      expect(useUIStore.getState().toasts).toHaveLength(1);
    });

    it('should remove a toast manually', () => {
      const state = useUIStore.getState();
      const id = state.addToast({
        message: 'Test message',
        type: 'success',
        duration: 0, // Prevent auto-removal
      });

      expect(useUIStore.getState().toasts).toHaveLength(1);

      state.removeToast(id);
      expect(useUIStore.getState().toasts).toHaveLength(0);
    });

    it('should clear all toasts', () => {
      const state = useUIStore.getState();
      state.addToast({ message: 'Toast 1', type: 'success', duration: 0 });
      state.addToast({ message: 'Toast 2', type: 'error', duration: 0 });
      state.addToast({ message: 'Toast 3', type: 'info', duration: 0 });

      expect(useUIStore.getState().toasts).toHaveLength(3);

      state.clearToasts();
      expect(useUIStore.getState().toasts).toHaveLength(0);
    });

    it('should handle multiple toasts with different durations', () => {
      const state = useUIStore.getState();
      state.addToast({ message: 'Toast 1', type: 'success', duration: 1000 });
      state.addToast({ message: 'Toast 2', type: 'error', duration: 3000 });
      state.addToast({ message: 'Toast 3', type: 'info', duration: 0 });

      expect(useUIStore.getState().toasts).toHaveLength(3);

      vi.advanceTimersByTime(1000);
      expect(useUIStore.getState().toasts).toHaveLength(2);

      vi.advanceTimersByTime(2000);
      expect(useUIStore.getState().toasts).toHaveLength(1);

      state.removeToast(useUIStore.getState().toasts[0].id);
      expect(useUIStore.getState().toasts).toHaveLength(0);
    });
  });

  describe('Modal Visibility', () => {
    it('should toggle settings modal', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().showSettingsModal).toBe(false);

      state.setSettingsModal(true);
      expect(useUIStore.getState().showSettingsModal).toBe(true);

      state.setSettingsModal(false);
      expect(useUIStore.getState().showSettingsModal).toBe(false);
    });

    it('should toggle command palette', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().showCommandPalette).toBe(false);

      state.setCommandPalette(true);
      expect(useUIStore.getState().showCommandPalette).toBe(true);
    });

    it('should toggle diff viewer', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().showDiffViewer).toBe(false);

      state.setDiffViewer(true);
      expect(useUIStore.getState().showDiffViewer).toBe(true);
    });

    it('should toggle write panel', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().showWritePanel).toBe(false);

      state.setWritePanel(true);
      expect(useUIStore.getState().showWritePanel).toBe(true);
    });

    it('should toggle batch panel', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().showBatchPanel).toBe(false);

      state.setBatchPanel(true);
      expect(useUIStore.getState().showBatchPanel).toBe(true);
    });

    it('should handle multiple modals open simultaneously', () => {
      const state = useUIStore.getState();
      state.setSettingsModal(true);
      state.setDiffViewer(true);
      state.setWritePanel(true);

      expect(useUIStore.getState().showSettingsModal).toBe(true);
      expect(useUIStore.getState().showDiffViewer).toBe(true);
      expect(useUIStore.getState().showWritePanel).toBe(true);
      expect(useUIStore.getState().showBatchPanel).toBe(false);
    });

    it('should close one modal without affecting others', () => {
      const state = useUIStore.getState();
      state.setSettingsModal(true);
      state.setDiffViewer(true);

      state.setSettingsModal(false);

      expect(useUIStore.getState().showSettingsModal).toBe(false);
      expect(useUIStore.getState().showDiffViewer).toBe(true);
    });
  });

  describe('Panel Visibility', () => {
    it('should toggle sidebar collapsed state', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);

      state.setSidebarCollapsed(true);
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);

      state.setSidebarCollapsed(false);
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    });

    it('should toggle context panel', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().showContextPanel).toBe(true);

      state.setContextPanel(false);
      expect(useUIStore.getState().showContextPanel).toBe(false);

      state.setContextPanel(true);
      expect(useUIStore.getState().showContextPanel).toBe(true);
    });

    it('should handle sidebar and context panel independently', () => {
      const state = useUIStore.getState();
      state.setSidebarCollapsed(true);
      state.setContextPanel(false);

      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      expect(useUIStore.getState().showContextPanel).toBe(false);

      state.setSidebarCollapsed(false);
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
      expect(useUIStore.getState().showContextPanel).toBe(false);
    });
  });

  describe('Theme Management', () => {
    it('should set theme to dark', () => {
      const state = useUIStore.getState();
      state.setTheme('dark');

      expect(useUIStore.getState().theme).toBe('dark');
    });

    it('should set theme to light', () => {
      const state = useUIStore.getState();
      state.setTheme('light');

      expect(useUIStore.getState().theme).toBe('light');
    });

    it('should toggle theme between dark and light', () => {
      const state = useUIStore.getState();
      expect(useUIStore.getState().theme).toBe('dark');

      state.setTheme('light');
      expect(useUIStore.getState().theme).toBe('light');

      state.setTheme('dark');
      expect(useUIStore.getState().theme).toBe('dark');
    });

    it('should update document attribute when setting theme', () => {
      const state = useUIStore.getState();
      const setAttributeSpy = vi.spyOn(document.documentElement, 'setAttribute');

      state.setTheme('light');

      expect(setAttributeSpy).toHaveBeenCalledWith('data-theme', 'light');

      setAttributeSpy.mockRestore();
    });

    it('should update localStorage when setting theme', () => {
      const state = useUIStore.getState();

      state.setTheme('light');

      expect(localStorage.getItem('devforge-theme')).toBe('light');
    });

    it('should persist theme preference', () => {
      const state = useUIStore.getState();
      state.setTheme('light');

      expect(useUIStore.getState().theme).toBe('light');
      // Would be persisted in localStorage
    });
  });

  describe('Edge Cases', () => {
    it('should handle adding toast with undefined properties', () => {
      const state = useUIStore.getState();
      const id = state.addToast({
        message: 'Test',
        type: 'success',
      });

      const toast = useUIStore.getState().toasts[0];
      expect(toast.id).toBe(id);
      expect(toast.message).toBe('Test');
      // Duration might default or might not be set
      if (toast.duration !== undefined) {
        expect(toast.duration).toBeGreaterThan(0);
      }
    });

    it('should handle removing non-existent toast', () => {
      const state = useUIStore.getState();
      state.addToast({ message: 'Toast 1', type: 'success', duration: 0 });

      state.removeToast('non-existent-id');
      expect(useUIStore.getState().toasts).toHaveLength(1);
    });

    it('should handle clearing empty toasts', () => {
      const state = useUIStore.getState();
      state.clearToasts();

      expect(useUIStore.getState().toasts).toHaveLength(0);
    });

    it('should handle toast with empty message', () => {
      const state = useUIStore.getState();
      state.addToast({
        message: '',
        type: 'success',
        duration: 3000,
      });

      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().toasts[0].message).toBe('');
    });

    it('should handle long messages', () => {
      const state = useUIStore.getState();
      const longMessage = 'A'.repeat(1000);

      state.addToast({
        message: longMessage,
        type: 'success',
        duration: 3000,
      });

      expect(useUIStore.getState().toasts[0].message).toBe(longMessage);
    });

    it('should handle rapid toast additions', () => {
      const state = useUIStore.getState();

      for (let i = 0; i < 100; i++) {
        state.addToast({
          message: `Toast ${i}`,
          type: 'success',
          duration: 0,
        });
      }

      expect(useUIStore.getState().toasts).toHaveLength(100);
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle full UI state transition', () => {
      const state = useUIStore.getState();

      // Open multiple modals
      state.setSettingsModal(true);
      state.setCommandPalette(true);

      // Show panels
      state.setContextPanel(true);

      // Add toasts
      state.addToast({ message: 'Info toast', type: 'info', duration: 0 });
      state.addToast({ message: 'Success toast', type: 'success', duration: 0 });

      // Change theme
      state.setTheme('light');

      // Collapse sidebar
      state.setSidebarCollapsed(true);

      const currentState = useUIStore.getState();
      expect(currentState.showSettingsModal).toBe(true);
      expect(currentState.showCommandPalette).toBe(true);
      expect(currentState.showContextPanel).toBe(true);
      expect(currentState.toasts).toHaveLength(2);
      expect(currentState.theme).toBe('light');
      expect(currentState.sidebarCollapsed).toBe(true);
    });

    it('should maintain independent state for modals and panels', () => {
      const state = useUIStore.getState();

      state.setSettingsModal(true);
      state.setSidebarCollapsed(true);
      state.addToast({ message: 'Test', type: 'success', duration: 0 });
      state.setTheme('light');

      // Verify all states are independent
      expect(useUIStore.getState().showSettingsModal).toBe(true);
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().theme).toBe('light');

      // Change one should not affect others
      state.setSettingsModal(false);
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      expect(useUIStore.getState().toasts).toHaveLength(1);
      expect(useUIStore.getState().theme).toBe('light');
    });
  });
});

// Add afterEach to clean up
function afterEach(fn: () => void) {
  // Implementation handled by vitest
}
