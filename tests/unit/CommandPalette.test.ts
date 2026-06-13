import { describe, it, expect, beforeEach, vi } from 'vitest';

interface Command {
  id: string;
  label: string;
  description?: string;
  shortcut?: string;
  execute: () => void;
}

class CommandPalette {
  private commands: Command[] = [];
  private isOpen: boolean = false;
  private searchQuery: string = '';
  private selectedIndex: number = -1;

  addCommand(command: Command): void {
    if (!this.commands.find(c => c.id === command.id)) {
      this.commands.push(command);
    }
  }

  open(): void {
    this.isOpen = true;
  }

  close(): void {
    this.isOpen = false;
    this.searchQuery = '';
    this.selectedIndex = -1;
  }

  isOpen_(): boolean {
    return this.isOpen;
  }

  setSearchQuery(query: string): void {
    this.searchQuery = query;
    this.selectedIndex = -1;
  }

  getSearchQuery(): string {
    return this.searchQuery;
  }

  getFilteredCommands(): Command[] {
    if (!this.searchQuery) return this.commands;
    const lower = this.searchQuery.toLowerCase();
    return this.commands.filter(c =>
      c.label.toLowerCase().includes(lower) ||
      c.description?.toLowerCase().includes(lower)
    );
  }

  selectCommand(index: number): void {
    const filtered = this.getFilteredCommands();
    if (index >= 0 && index < filtered.length) {
      filtered[index].execute();
      this.close();
    }
  }

  moveSelection(direction: 'up' | 'down'): void {
    const filtered = this.getFilteredCommands();
    if (direction === 'down') {
      this.selectedIndex = Math.min(this.selectedIndex + 1, filtered.length - 1);
    } else {
      this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
    }
  }

  getSelectedIndex(): number {
    return this.selectedIndex;
  }
}

describe('CommandPalette', () => {
  let palette: CommandPalette;

  beforeEach(() => {
    palette = new CommandPalette();
  });

  it('should initialize closed', () => {
    expect(palette.isOpen_()).toBe(false);
  });

  it('should open and close', () => {
    palette.open();
    expect(palette.isOpen_()).toBe(true);
    palette.close();
    expect(palette.isOpen_()).toBe(false);
  });

  it('should add commands', () => {
    const cmd: Command = { id: 'save', label: 'Save', execute: vi.fn() };
    palette.addCommand(cmd);
    expect(palette.getFilteredCommands()).toHaveLength(1);
  });

  it('should search commands', () => {
    palette.addCommand({ id: 'save', label: 'Save File', execute: vi.fn() });
    palette.addCommand({ id: 'open', label: 'Open File', execute: vi.fn() });
    palette.setSearchQuery('save');
    expect(palette.getFilteredCommands()).toHaveLength(1);
  });

  it('should execute command', () => {
    const execute = vi.fn();
    palette.addCommand({ id: 'test', label: 'Test', execute });
    palette.open();
    palette.selectCommand(0);
    expect(execute).toHaveBeenCalled();
  });

  it('should close after execution', () => {
    const execute = vi.fn();
    palette.addCommand({ id: 'test', label: 'Test', execute });
    palette.open();
    palette.selectCommand(0);
    expect(palette.isOpen_()).toBe(false);
  });

  it('should move selection', () => {
    palette.addCommand({ id: '1', label: 'Cmd 1', execute: vi.fn() });
    palette.addCommand({ id: '2', label: 'Cmd 2', execute: vi.fn() });
    palette.moveSelection('down');
    expect(palette.getSelectedIndex()).toBe(0);
  });

  it('should filter by description', () => {
    palette.addCommand({ id: '1', label: 'Cmd', description: 'Save document', execute: vi.fn() });
    palette.setSearchQuery('save');
    expect(palette.getFilteredCommands()).toHaveLength(1);
  });
});
