import { describe, it, expect, beforeEach, vi } from 'vitest';

interface PanelState {
  isVisible: boolean;
  width: number;
  content: string;
}

class MainPanel {
  private state: PanelState = {
    isVisible: true,
    width: 500,
    content: ''
  };

  private onChange: ((state: PanelState) => void) | null = null;

  getState(): PanelState {
    return { ...this.state };
  }

  show(): void {
    this.setState({ isVisible: true });
  }

  hide(): void {
    this.setState({ isVisible: false });
  }

  setWidth(width: number): void {
    this.setState({ width: Math.max(200, Math.min(800, width)) });
  }

  setContent(content: string): void {
    this.setState({ content });
  }

  setState(partial: Partial<PanelState>): void {
    this.state = { ...this.state, ...partial };
    this.onChange?.(this.state);
  }

  isVisible_(): boolean {
    return this.state.isVisible;
  }

  getWidth(): number {
    return this.state.width;
  }

  getContent(): string {
    return this.state.content;
  }

  onChange_(callback: (state: PanelState) => void): void {
    this.onChange = callback;
  }

  reset(): void {
    this.setState({ isVisible: true, width: 500, content: '' });
  }
}

describe('MainPanel', () => {
  let panel: MainPanel;

  beforeEach(() => {
    panel = new MainPanel();
  });

  it('should initialize visible', () => {
    expect(panel.isVisible_()).toBe(true);
    expect(panel.getWidth()).toBe(500);
  });

  it('should show panel', () => {
    panel.hide();
    panel.show();
    expect(panel.isVisible_()).toBe(true);
  });

  it('should hide panel', () => {
    panel.hide();
    expect(panel.isVisible_()).toBe(false);
  });

  it('should set width', () => {
    panel.setWidth(600);
    expect(panel.getWidth()).toBe(600);
  });

  it('should enforce min width', () => {
    panel.setWidth(100);
    expect(panel.getWidth()).toBe(200);
  });

  it('should enforce max width', () => {
    panel.setWidth(1000);
    expect(panel.getWidth()).toBe(800);
  });

  it('should set content', () => {
    panel.setContent('Test content');
    expect(panel.getContent()).toBe('Test content');
  });

  it('should call onChange callback', () => {
    const callback = vi.fn();
    panel.onChange_(callback);
    panel.show();
    expect(callback).toHaveBeenCalled();
  });

  it('should reset panel', () => {
    panel.hide();
    panel.setWidth(600);
    panel.setContent('Test');
    panel.reset();
    expect(panel.isVisible_()).toBe(true);
    expect(panel.getWidth()).toBe(500);
    expect(panel.getContent()).toBe('');
  });
});
