/**
 * ChatMessage component - individual chat message with role and content
 */

export interface ChatMessageOptions {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
  tokens?: number;
  onCopy?: () => void;
  onDelete?: () => void;
}

export function createChatMessage(options: ChatMessageOptions): HTMLDivElement {
  const message = document.createElement('div');
  message.className = `chat-message chat-message-${options.role}`;

  const isUser = options.role === 'user';

  message.style.cssText = `
    display: flex;
    gap: 12px;
    padding: 12px;
    background-color: ${isUser ? 'transparent' : 'var(--panel)'};
    border-radius: 6px;
    animation: slideIn 0.3s ease-out;
  `;

  // Avatar
  const avatar = document.createElement('div');
  avatar.style.cssText = `
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    background-color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    color: var(--bg);
    font-weight: bold;
  `;
  avatar.textContent = isUser ? '👤' : '🤖';

  // Content container
  const contentContainer = document.createElement('div');
  contentContainer.style.cssText = `
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;

  // Header with role and timestamp
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  `;

  const role = document.createElement('span');
  role.textContent = isUser ? 'You' : 'Assistant';
  role.style.cssText = `
    font-weight: 600;
    font-size: 13px;
    color: var(--text);
  `;

  const meta = document.createElement('div');
  meta.style.cssText = `
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 12px;
    color: var(--text-secondary);
  `;

  if (options.timestamp) {
    const time = document.createElement('span');
    time.textContent = options.timestamp.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    meta.appendChild(time);
  }

  if (options.tokens) {
    const tokens = document.createElement('span');
    tokens.textContent = `${options.tokens} tokens`;
    meta.appendChild(tokens);
  }

  header.appendChild(role);
  header.appendChild(meta);

  // Content text
  const contentText = document.createElement('p');
  contentText.textContent = options.content;
  contentText.style.cssText = `
    margin: 0;
    color: var(--text);
    font-size: 14px;
    line-height: 1.5;
    word-wrap: break-word;
    white-space: pre-wrap;
  `;

  // Actions
  const actions = document.createElement('div');
  actions.style.cssText = `
    display: flex;
    gap: 8px;
    opacity: 0;
    transition: opacity 0.2s;
  `;

  const copyBtn = document.createElement('button');
  copyBtn.textContent = '📋 Copy';
  copyBtn.style.cssText = `
    padding: 4px 8px;
    border: 1px solid var(--border);
    background-color: transparent;
    color: var(--text-secondary);
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;
    font-family: inherit;
  `;

  copyBtn.addEventListener('mouseover', () => {
    copyBtn.style.backgroundColor = 'var(--border)';
  });

  copyBtn.addEventListener('mouseout', () => {
    copyBtn.style.backgroundColor = 'transparent';
  });

  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(options.content);
    copyBtn.textContent = '✓ Copied';
    setTimeout(() => {
      copyBtn.textContent = '📋 Copy';
    }, 2000);
    options.onCopy?.();
  });

  if (!isUser) {
    actions.appendChild(copyBtn);
  }

  if (options.onDelete) {
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '🗑️ Delete';
    deleteBtn.style.cssText = `
      padding: 4px 8px;
      border: 1px solid var(--border);
      background-color: transparent;
      color: var(--text-secondary);
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
      font-family: inherit;
    `;

    deleteBtn.addEventListener('mouseover', () => {
      deleteBtn.style.backgroundColor = 'var(--red)';
      deleteBtn.style.color = 'white';
    });

    deleteBtn.addEventListener('mouseout', () => {
      deleteBtn.style.backgroundColor = 'transparent';
      deleteBtn.style.color = 'var(--text-secondary)';
    });

    deleteBtn.addEventListener('click', () => {
      options.onDelete?.();
    });

    actions.appendChild(deleteBtn);
  }

  message.addEventListener('mouseover', () => {
    actions.style.opacity = '1';
  });

  message.addEventListener('mouseout', () => {
    actions.style.opacity = '0';
  });

  contentContainer.appendChild(header);
  contentContainer.appendChild(contentText);
  if (actions.children.length > 0) {
    contentContainer.appendChild(actions);
  }

  message.appendChild(avatar);
  message.appendChild(contentContainer);

  // Animations
  const style = document.createElement('style');
  if (!document.head.querySelector('style[data-animations="chat"]')) {
    style.setAttribute('data-animations', 'chat');
    style.textContent = `
      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
    document.head.appendChild(style);
  }

  return message;
}

export const ChatMessage = {
  create: createChatMessage,
};
