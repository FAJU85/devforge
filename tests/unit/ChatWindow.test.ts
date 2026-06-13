import { describe, it, expect, beforeEach, vi } from 'vitest';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

class ChatWindow {
  private messages: ChatMessage[] = [];
  private isLoading: boolean = false;
  private autoScroll: boolean = true;
  private onMessageSubmit: ((content: string) => void) | null = null;

  addMessage(message: ChatMessage): void {
    this.messages.push(message);
  }

  getMessages(): ChatMessage[] {
    return [...this.messages];
  }

  setLoading(loading: boolean): void {
    this.isLoading = loading;
  }

  isLoading_(): boolean {
    return this.isLoading;
  }

  clearMessages(): void {
    this.messages = [];
  }

  removeMessage(id: string): boolean {
    const index = this.messages.findIndex(m => m.id === id);
    if (index > -1) {
      this.messages.splice(index, 1);
      return true;
    }
    return false;
  }

  setAutoScroll(enabled: boolean): void {
    this.autoScroll = enabled;
  }

  isAutoScroll(): boolean {
    return this.autoScroll;
  }

  onSubmit(callback: (content: string) => void): void {
    this.onMessageSubmit = callback;
  }

  submit(content: string): void {
    if (content.trim()) {
      this.onMessageSubmit?.(content);
    }
  }

  scrollToBottom(): void {
    // Scroll implementation
  }

  getLastMessage(): ChatMessage | undefined {
    return this.messages[this.messages.length - 1];
  }

  getMessageCount(): number {
    return this.messages.length;
  }
}

describe('ChatWindow', () => {
  let window: ChatWindow;

  beforeEach(() => {
    window = new ChatWindow();
  });

  it('should initialize empty', () => {
    expect(window.getMessageCount()).toBe(0);
  });

  it('should add message', () => {
    const msg: ChatMessage = { id: '1', role: 'user', content: 'Hello' };
    window.addMessage(msg);
    expect(window.getMessageCount()).toBe(1);
  });

  it('should get messages', () => {
    window.addMessage({ id: '1', role: 'user', content: 'Hi' });
    window.addMessage({ id: '2', role: 'assistant', content: 'Hello' });
    expect(window.getMessages()).toHaveLength(2);
  });

  it('should clear messages', () => {
    window.addMessage({ id: '1', role: 'user', content: 'Test' });
    window.clearMessages();
    expect(window.getMessageCount()).toBe(0);
  });

  it('should remove message', () => {
    window.addMessage({ id: '1', role: 'user', content: 'Remove me' });
    expect(window.removeMessage('1')).toBe(true);
    expect(window.getMessageCount()).toBe(0);
  });

  it('should handle loading state', () => {
    window.setLoading(true);
    expect(window.isLoading_()).toBe(true);
    window.setLoading(false);
    expect(window.isLoading_()).toBe(false);
  });

  it('should handle auto scroll', () => {
    expect(window.isAutoScroll()).toBe(true);
    window.setAutoScroll(false);
    expect(window.isAutoScroll()).toBe(false);
  });

  it('should call submit callback', () => {
    const callback = vi.fn();
    window.onSubmit(callback);
    window.submit('Test message');
    expect(callback).toHaveBeenCalledWith('Test message');
  });

  it('should get last message', () => {
    window.addMessage({ id: '1', role: 'user', content: 'First' });
    window.addMessage({ id: '2', role: 'assistant', content: 'Last' });
    const last = window.getLastMessage();
    expect(last?.content).toBe('Last');
  });

  it('should scroll to bottom', () => {
    expect(() => window.scrollToBottom()).not.toThrow();
  });

  it('should not submit empty message', () => {
    const callback = vi.fn();
    window.onSubmit(callback);
    window.submit('   ');
    expect(callback).not.toHaveBeenCalled();
  });
});
