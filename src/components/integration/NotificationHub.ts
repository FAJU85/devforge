/**
 * NotificationHub component - centralized notification management
 */

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
  actions?: { label: string; onClick: () => void }[];
}

export interface NotificationHubOptions {
  maxNotifications?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export function createNotificationHub(options?: NotificationHubOptions): HTMLDivElement {
  const hub = document.createElement('div');
  hub.className = 'notification-hub';

  const position = options?.position || 'top-right';
  const positionStyles: { [key: string]: string } = {
    'top-right': 'top: 20px; right: 20px;',
    'top-left': 'top: 20px; left: 20px;',
    'bottom-right': 'bottom: 20px; right: 20px;',
    'bottom-left': 'bottom: 20px; left: 20px;',
  };

  hub.style.cssText = `
    position: fixed;
    ${positionStyles[position]}
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 400px;
    z-index: 9999;
  `;

  const notifications: Notification[] = [];

  const addNotification = (notification: Notification) => {
    notifications.push(notification);

    const container = document.createElement('div');
    container.className = `notification notification-${notification.type}`;
    container.id = notification.id;

    const colors: { [key: string]: { bg: string; text: string; icon: string } } = {
      success: { bg: 'rgba(16, 185, 129, 0.1)', text: 'var(--green)', icon: '✓' },
      error: { bg: 'rgba(239, 68, 68, 0.1)', text: 'var(--red)', icon: '✕' },
      info: { bg: 'rgba(59, 130, 246, 0.1)', text: 'var(--accent)', icon: 'ℹ' },
      warning: { bg: 'rgba(245, 158, 11, 0.1)', text: 'var(--yellow)', icon: '⚠' },
    };

    const color = colors[notification.type];

    container.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 12px;
      background-color: ${color.bg};
      border-left: 3px solid ${color.text};
      border-radius: 6px;
      color: var(--text);
      font-size: 13px;
      animation: slideIn 0.3s ease-out;
    `;

    // Header with icon and title
    const header = document.createElement('div');
    header.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
    `;

    const icon = document.createElement('span');
    icon.textContent = color.icon;
    icon.style.cssText = `
      color: ${color.text};
      font-weight: bold;
      font-size: 16px;
    `;

    const title = document.createElement('span');
    title.textContent = notification.title;
    title.style.cssText = `
      font-weight: 600;
      color: var(--text);
    `;

    const close = document.createElement('button');
    close.textContent = '✕';
    close.style.cssText = `
      background: none;
      border: none;
      color: ${color.text};
      cursor: pointer;
      font-size: 16px;
      padding: 0;
      margin-left: auto;
      transition: opacity 0.2s;
    `;

    close.addEventListener('click', () => {
      container.style.animation = 'slideOut 0.2s ease-in';
      setTimeout(() => {
        container.remove();
        notifications.splice(notifications.indexOf(notification), 1);
      }, 200);
    });

    header.appendChild(icon);
    header.appendChild(title);
    header.appendChild(close);
    container.appendChild(header);

    // Message
    if (notification.message) {
      const message = document.createElement('div');
      message.textContent = notification.message;
      message.style.cssText = `
        color: var(--text-secondary);
        font-size: 12px;
        line-height: 1.4;
      `;
      container.appendChild(message);
    }

    // Actions
    if (notification.actions && notification.actions.length > 0) {
      const actions = document.createElement('div');
      actions.style.cssText = `
        display: flex;
        gap: 8px;
        margin-top: 8px;
      `;

      notification.actions.forEach((action) => {
        const btn = document.createElement('button');
        btn.textContent = action.label;
        btn.style.cssText = `
          padding: 4px 10px;
          border: 1px solid ${color.text};
          border-radius: 3px;
          background-color: transparent;
          color: ${color.text};
          cursor: pointer;
          font-size: 11px;
          font-weight: 500;
          transition: all 0.2s;
          font-family: inherit;
        `;

        btn.addEventListener('mouseover', () => {
          btn.backgroundColor = color.text;
          btn.style.color = 'white';
        });

        btn.addEventListener('mouseout', () => {
          btn.style.backgroundColor = 'transparent';
          btn.style.color = color.text;
        });

        btn.addEventListener('click', () => {
          action.onClick();
          close.click();
        });

        actions.appendChild(btn);
      });

      container.appendChild(actions);
    }

    hub.appendChild(container);

    // Auto-dismiss
    if (notification.duration !== 0) {
      const duration = notification.duration || 3000;
      setTimeout(() => {
        close.click();
      }, duration);
    }
  };

  // Animations
  const style = document.createElement('style');
  if (!document.head.querySelector('style[data-notification-animations]')) {
    style.setAttribute('data-notification-animations', 'true');
    style.textContent = `
      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateX(${position.includes('right') ? '400px' : '-400px'});
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }

      @keyframes slideOut {
        to {
          opacity: 0;
          transform: translateX(${position.includes('right') ? '400px' : '-400px'});
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Expose methods
  (hub as any).notify = addNotification;
  (hub as any).success = (title: string, message: string) => {
    addNotification({
      id: `notification-${Date.now()}`,
      title,
      message,
      type: 'success',
    });
  };
  (hub as any).error = (title: string, message: string) => {
    addNotification({
      id: `notification-${Date.now()}`,
      title,
      message,
      type: 'error',
    });
  };
  (hub as any).info = (title: string, message: string) => {
    addNotification({
      id: `notification-${Date.now()}`,
      title,
      message,
      type: 'info',
    });
  };
  (hub as any).warning = (title: string, message: string) => {
    addNotification({
      id: `notification-${Date.now()}`,
      title,
      message,
      type: 'warning',
    });
  };

  return hub;
}

export const NotificationHub = {
  create: createNotificationHub,
};
