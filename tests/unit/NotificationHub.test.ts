import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Notification {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
}

class NotificationHub {
  private notifications: Notification[] = [];
  private onAdd: ((notification: Notification) => void) | null = null;
  private onRemove: ((id: string) => void) | null = null;

  add(notification: Omit<Notification, 'id'>): string {
    const id = `notif-${Date.now()}`;
    const notif: Notification = { ...notification, id };
    this.notifications.push(notif);
    this.onAdd?.(notif);

    if (notification.duration) {
      setTimeout(() => this.remove(id), notification.duration);
    }

    return id;
  }

  remove(id: string): boolean {
    const index = this.notifications.findIndex(n => n.id === id);
    if (index > -1) {
      this.notifications.splice(index, 1);
      this.onRemove?.(id);
      return true;
    }
    return false;
  }

  getAll(): Notification[] {
    return [...this.notifications];
  }

  clear(): void {
    this.notifications = [];
  }

  getCount(): number {
    return this.notifications.length;
  }

  onNotificationAdded(callback: (notification: Notification) => void): void {
    this.onAdd = callback;
  }

  onNotificationRemoved(callback: (id: string) => void): void {
    this.onRemove = callback;
  }

  success(message: string, duration?: number): string {
    return this.add({ message, type: 'success', duration });
  }

  error(message: string, duration?: number): string {
    return this.add({ message, type: 'error', duration });
  }

  warning(message: string, duration?: number): string {
    return this.add({ message, type: 'warning', duration });
  }

  info(message: string, duration?: number): string {
    return this.add({ message, type: 'info', duration });
  }
}

describe('NotificationHub', () => {
  let hub: NotificationHub;

  beforeEach(() => {
    vi.useFakeTimers();
    hub = new NotificationHub();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize empty', () => {
    expect(hub.getCount()).toBe(0);
  });

  it('should add notification', () => {
    hub.add({ message: 'Test', type: 'info' });
    expect(hub.getCount()).toBe(1);
  });

  it('should remove notification', () => {
    const id = hub.add({ message: 'Test', type: 'info' });
    expect(hub.remove(id)).toBe(true);
    expect(hub.getCount()).toBe(0);
  });

  it('should call onNotificationAdded', () => {
    const callback = vi.fn();
    hub.onNotificationAdded(callback);
    hub.add({ message: 'Test', type: 'info' });
    expect(callback).toHaveBeenCalled();
  });

  it('should call onNotificationRemoved', () => {
    const callback = vi.fn();
    const id = hub.add({ message: 'Test', type: 'info' });
    hub.onNotificationRemoved(callback);
    hub.remove(id);
    expect(callback).toHaveBeenCalledWith(id);
  });

  it('should add success notification', () => {
    hub.success('Success!');
    const notif = hub.getAll()[0];
    expect(notif.type).toBe('success');
  });

  it('should add error notification', () => {
    hub.error('Error!');
    const notif = hub.getAll()[0];
    expect(notif.type).toBe('error');
  });

  it('should add warning notification', () => {
    hub.warning('Warning!');
    const notif = hub.getAll()[0];
    expect(notif.type).toBe('warning');
  });

  it('should add info notification', () => {
    hub.info('Info!');
    const notif = hub.getAll()[0];
    expect(notif.type).toBe('info');
  });

  it('should auto-remove after duration', () => {
    hub.add({ message: 'Test', type: 'info', duration: 1000 });
    expect(hub.getCount()).toBe(1);

    vi.advanceTimersByTime(1000);
    expect(hub.getCount()).toBe(0);
  });

  it('should clear all notifications', () => {
    hub.add({ message: 'Test 1', type: 'info' });
    hub.add({ message: 'Test 2', type: 'info' });
    hub.clear();
    expect(hub.getCount()).toBe(0);
  });

  it('should return false when removing nonexistent', () => {
    expect(hub.remove('invalid')).toBe(false);
  });
});

function afterEach(callback: () => void) {
  callback();
}
