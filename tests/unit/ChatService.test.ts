import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

class ChatService {
  private messages: Message[] = [];
  private messageId: number = 0;
  private onMessageAdded: ((message: Message) => void) | null = null;

  addMessage(role: 'user' | 'assistant', content: string): Message {
    const message: Message = {
      id: `msg-${++this.messageId}`,
      role,
      content,
      timestamp: Date.now()
    };
    this.messages.push(message);
    this.onMessageAdded?.(message);
    return message;
  }

  getMessages(): Message[] {
    return [...this.messages];
  }

  getMessageCount(): number {
    return this.messages.length;
  }

  clearMessages(): void {
    this.messages = [];
    this.messageId = 0;
  }

  deleteMessage(id: string): boolean {
    const index = this.messages.findIndex(m => m.id === id);
    if (index > -1) {
      this.messages.splice(index, 1);
      return true;
    }
    return false;
  }

  getMessage(id: string): Message | undefined {
    return this.messages.find(m => m.id === id);
  }

  getConversationLength(): number {
    return this.messages.reduce((sum, msg) => sum + msg.content.length, 0);
  }

  getLastMessage(): Message | undefined {
    return this.messages[this.messages.length - 1];
  }

  onNewMessage(callback: (message: Message) => void): void {
    this.onMessageAdded = callback;
  }

  exportConversation(): string {
    return this.messages
      .map(m => `${m.role.toUpperCase()}: ${m.content}`)
      .join('\n\n');
  }

  searchMessages(query: string): Message[] {
    return this.messages.filter(m =>
      m.content.toLowerCase().includes(query.toLowerCase())
    );
  }
}

describe('ChatService', () => {
  let service: ChatService;

  beforeEach(() => {
    service = new ChatService();
  });

  it('should initialize empty', () => {
    expect(service.getMessageCount()).toBe(0);
  });

  it('should add user message', () => {
    const msg = service.addMessage('user', 'Hello');
    expect(msg.role).toBe('user');
    expect(msg.content).toBe('Hello');
  });

  it('should add assistant message', () => {
    const msg = service.addMessage('assistant', 'Hi there!');
    expect(msg.role).toBe('assistant');
    expect(msg.content).toBe('Hi there!');
  });

  it('should increment message count', () => {
    service.addMessage('user', 'Message 1');
    service.addMessage('assistant', 'Response 1');
    expect(service.getMessageCount()).toBe(2);
  });

  it('should get all messages', () => {
    service.addMessage('user', 'Hello');
    service.addMessage('assistant', 'Hi');
    const messages = service.getMessages();
    expect(messages).toHaveLength(2);
  });

  it('should clear messages', () => {
    service.addMessage('user', 'Test');
    service.clearMessages();
    expect(service.getMessageCount()).toBe(0);
  });

  it('should delete message by id', () => {
    const msg = service.addMessage('user', 'Delete me');
    expect(service.deleteMessage(msg.id)).toBe(true);
    expect(service.getMessageCount()).toBe(0);
  });

  it('should return false when deleting nonexistent message', () => {
    expect(service.deleteMessage('invalid-id')).toBe(false);
  });

  it('should get message by id', () => {
    const msg = service.addMessage('user', 'Find me');
    const found = service.getMessage(msg.id);
    expect(found?.content).toBe('Find me');
  });

  it('should return undefined for nonexistent message', () => {
    expect(service.getMessage('invalid-id')).toBeUndefined();
  });

  it('should calculate conversation length', () => {
    service.addMessage('user', 'Hello'); // 5
    service.addMessage('assistant', 'Hi'); // 2
    expect(service.getConversationLength()).toBe(7);
  });

  it('should get last message', () => {
    service.addMessage('user', 'First');
    const last = service.addMessage('assistant', 'Last');
    expect(service.getLastMessage()?.id).toBe(last.id);
  });

  it('should call onNewMessage callback', () => {
    const callback = vi.fn();
    service.onNewMessage(callback);
    const msg = service.addMessage('user', 'Test');
    expect(callback).toHaveBeenCalledWith(msg);
  });

  it('should export conversation', () => {
    service.addMessage('user', 'Hello');
    service.addMessage('assistant', 'Hi');
    const exported = service.exportConversation();
    expect(exported).toContain('USER: Hello');
    expect(exported).toContain('ASSISTANT: Hi');
  });

  it('should search messages', () => {
    service.addMessage('user', 'Looking for Python');
    service.addMessage('assistant', 'Java is great');
    service.addMessage('user', 'Python rules');
    const results = service.searchMessages('python');
    expect(results).toHaveLength(2);
  });

  it('should search case-insensitive', () => {
    service.addMessage('user', 'HELLO');
    const results = service.searchMessages('hello');
    expect(results).toHaveLength(1);
  });
});
