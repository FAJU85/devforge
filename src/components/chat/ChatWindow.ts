/**
 * ChatWindow component - main chat message container
 */

export interface ChatWindowOptions {
  onScroll?: (scrollTop: number) => void;
}

export function createChatWindow(options?: ChatWindowOptions): HTMLDivElement {
  const chatWindow = document.createElement('div');
  chatWindow.className = 'chat-window';

  chatWindow.style.cssText = `
    display: flex;
    flex-direction: column;
    flex: 1;
    background-color: var(--bg);
    border-radius: 8px;
    border: 1px solid var(--border);
    overflow: hidden;
  `;

  // Messages container
  const messagesContainer = document.createElement('div');
  messagesContainer.className = 'messages-container';

  messagesContainer.style.cssText = `
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  `;

  // Scroll event listener
  messagesContainer.addEventListener('scroll', () => {
    options?.onScroll?.(messagesContainer.scrollTop);
  });

  // Auto-scroll to bottom using requestAnimationFrame for better performance
  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      if (messagesContainer.parentNode) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    });
  };

  // Empty state
  const emptyState = document.createElement('div');
  emptyState.className = 'chat-empty-state';
  emptyState.style.cssText = `
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    text-align: center;
    gap: 12px;
  `;

  const emptyIcon = document.createElement('div');
  emptyIcon.textContent = '💬';
  emptyIcon.style.fontSize = '48px';

  const emptyText = document.createElement('p');
  emptyText.textContent = 'No messages yet. Start a conversation!';
  emptyText.style.cssText = `
    margin: 0;
    font-size: 14px;
    max-width: 200px;
  `;

  emptyState.appendChild(emptyIcon);
  emptyState.appendChild(emptyText);
  messagesContainer.appendChild(emptyState);

  // Expose methods
  (chatWindow as any).addMessage = (element: HTMLElement) => {
    if (emptyState.parentNode === messagesContainer) {
      emptyState.remove();
    }
    messagesContainer.appendChild(element);
    scrollToBottom();
  };

  (chatWindow as any).clearMessages = () => {
    messagesContainer.innerHTML = '';
    const newEmptyState = document.createElement('div');
    newEmptyState.className = 'chat-empty-state';
    newEmptyState.style.cssText = emptyState.style.cssText;
    newEmptyState.appendChild(emptyIcon.cloneNode(true));
    newEmptyState.appendChild(emptyText.cloneNode(true));
    messagesContainer.appendChild(newEmptyState);
  };

  (chatWindow as any).getMessagesContainer = () => messagesContainer;

  chatWindow.appendChild(messagesContainer);

  return chatWindow;
}

export const ChatWindow = {
  create: createChatWindow,
};
