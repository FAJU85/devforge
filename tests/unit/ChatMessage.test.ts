import { describe, it, expect, beforeEach } from 'vitest';

interface Message {
  id: string;
  author: string;
  content: string;
  timestamp: number;
  role: 'user' | 'assistant';
  tokens?: number;
}

class ChatMessage {
  private message: Message;

  constructor(message: Message) {
    this.message = message;
  }

  render(): string {
    const timestamp = new Date(this.message.timestamp).toLocaleTimeString();
    return `[${timestamp}] ${this.message.author}: ${this.message.content}`;
  }

  getHTML(): string {
    const role = this.message.role;
    return `<div class="message ${role}"><span class="author">${this.message.author}</span><p>${this.message.content}</p></div>`;
  }

  getId(): string {
    return this.message.id;
  }

  getRole(): 'user' | 'assistant' {
    return this.message.role;
  }

  getTokenCount(): number {
    return this.message.tokens || this.estimateTokens();
  }

  private estimateTokens(): number {
    return Math.ceil(this.message.content.split(/\s+/).length / 0.75);
  }

  editContent(newContent: string): void {
    this.message.content = newContent;
  }
}

describe('ChatMessage', () => {
  let message: Message;

  beforeEach(() => {
    message = {
      id: 'msg-1',
      author: 'User',
      content: 'Hello, how are you?',
      timestamp: Date.now(),
      role: 'user',
      tokens: 5
    };
  });

  it('should create a message', () => {
    const chatMsg = new ChatMessage(message);
    expect(chatMsg.getId()).toBe('msg-1');
  });

  it('should render message text', () => {
    const chatMsg = new ChatMessage(message);
    const rendered = chatMsg.render();
    expect(rendered).toContain('User');
    expect(rendered).toContain('Hello, how are you?');
  });

  it('should generate HTML representation', () => {
    const chatMsg = new ChatMessage(message);
    const html = chatMsg.getHTML();
    expect(html).toContain('class="message user"');
    expect(html).toContain('class="author"');
    expect(html).toContain('Hello, how are you?');
  });

  it('should get role correctly', () => {
    const chatMsg = new ChatMessage(message);
    expect(chatMsg.getRole()).toBe('user');
  });

  it('should return token count', () => {
    const chatMsg = new ChatMessage(message);
    expect(chatMsg.getTokenCount()).toBe(5);
  });

  it('should estimate tokens when not provided', () => {
    const msgWithoutTokens: Message = {
      ...message,
      tokens: undefined
    };
    const chatMsg = new ChatMessage(msgWithoutTokens);
    expect(chatMsg.getTokenCount()).toBeGreaterThan(0);
  });

  it('should edit content', () => {
    const chatMsg = new ChatMessage(message);
    chatMsg.editContent('Updated content');
    const rendered = chatMsg.render();
    expect(rendered).toContain('Updated content');
  });

  it('should handle assistant messages', () => {
    message.role = 'assistant';
    message.author = 'Assistant';
    const chatMsg = new ChatMessage(message);
    const html = chatMsg.getHTML();
    expect(html).toContain('class="message assistant"');
  });

  it('should preserve message ID', () => {
    const chatMsg = new ChatMessage(message);
    expect(chatMsg.getId()).toBe(message.id);
  });

  it('should handle long messages', () => {
    message.content = 'a '.repeat(100);
    message.tokens = undefined;
    const chatMsg = new ChatMessage(message);
    const tokens = chatMsg.getTokenCount();
    expect(tokens).toBeGreaterThan(50);
  });
});
