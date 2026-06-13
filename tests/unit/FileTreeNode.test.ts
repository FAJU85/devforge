import { describe, it, expect, beforeEach, vi } from 'vitest';

interface TreeNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: TreeNode[];
  expanded?: boolean;
  selected?: boolean;
}

class FileTreeNode {
  private node: TreeNode;
  private onToggle: ((nodeId: string) => void) | null = null;
  private onSelect: ((nodeId: string) => void) | null = null;

  constructor(node: TreeNode) {
    this.node = { ...node };
  }

  getName(): string {
    return this.node.name;
  }

  getType(): 'file' | 'folder' {
    return this.node.type;
  }

  getId(): string {
    return this.node.id;
  }

  getChildren(): TreeNode[] {
    return this.node.children || [];
  }

  toggle(): void {
    this.node.expanded = !this.node.expanded;
    this.onToggle?.(this.node.id);
  }

  select(): void {
    this.node.selected = true;
    this.onSelect?.(this.node.id);
  }

  deselect(): void {
    this.node.selected = false;
  }

  isExpanded(): boolean {
    return this.node.expanded || false;
  }

  isSelected(): boolean {
    return this.node.selected || false;
  }

  isFolder(): boolean {
    return this.node.type === 'folder';
  }

  isFile(): boolean {
    return this.node.type === 'file';
  }

  hasChildren(): boolean {
    return (this.node.children?.length || 0) > 0;
  }

  getChildCount(): number {
    return this.node.children?.length || 0;
  }

  addChild(child: TreeNode): void {
    if (!this.node.children) {
      this.node.children = [];
    }
    this.node.children.push(child);
  }

  removeChild(childId: string): boolean {
    if (!this.node.children) return false;
    const index = this.node.children.findIndex(c => c.id === childId);
    if (index > -1) {
      this.node.children.splice(index, 1);
      return true;
    }
    return false;
  }

  onToggleCallback(callback: (nodeId: string) => void): void {
    this.onToggle = callback;
  }

  onSelectCallback(callback: (nodeId: string) => void): void {
    this.onSelect = callback;
  }

  getPath(): string {
    return this.node.id; // Simplified - would be built from parents
  }
}

describe('FileTreeNode', () => {
  let node: FileTreeNode;

  beforeEach(() => {
    const treeNode: TreeNode = {
      id: 'root',
      name: 'src',
      type: 'folder',
      children: [
        { id: 'file1', name: 'main.ts', type: 'file' },
        { id: 'folder1', name: 'utils', type: 'folder', children: [] }
      ]
    };
    node = new FileTreeNode(treeNode);
  });

  it('should get node properties', () => {
    expect(node.getName()).toBe('src');
    expect(node.getType()).toBe('folder');
    expect(node.getId()).toBe('root');
  });

  it('should detect if folder', () => {
    expect(node.isFolder()).toBe(true);
    expect(node.isFile()).toBe(false);
  });

  it('should detect if file', () => {
    const fileNode = new FileTreeNode({
      id: 'file',
      name: 'test.ts',
      type: 'file'
    });
    expect(fileNode.isFile()).toBe(true);
    expect(fileNode.isFolder()).toBe(false);
  });

  it('should toggle expanded state', () => {
    expect(node.isExpanded()).toBe(false);
    node.toggle();
    expect(node.isExpanded()).toBe(true);
    node.toggle();
    expect(node.isExpanded()).toBe(false);
  });

  it('should select and deselect', () => {
    expect(node.isSelected()).toBe(false);
    node.select();
    expect(node.isSelected()).toBe(true);
    node.deselect();
    expect(node.isSelected()).toBe(false);
  });

  it('should call toggle callback', () => {
    const callback = vi.fn();
    node.onToggleCallback(callback);
    node.toggle();
    expect(callback).toHaveBeenCalledWith('root');
  });

  it('should call select callback', () => {
    const callback = vi.fn();
    node.onSelectCallback(callback);
    node.select();
    expect(callback).toHaveBeenCalledWith('root');
  });

  it('should get children', () => {
    expect(node.getChildren()).toHaveLength(2);
  });

  it('should detect if has children', () => {
    expect(node.hasChildren()).toBe(true);
    const emptyFolder = new FileTreeNode({
      id: 'empty',
      name: 'empty',
      type: 'folder'
    });
    expect(emptyFolder.hasChildren()).toBe(false);
  });

  it('should get child count', () => {
    expect(node.getChildCount()).toBe(2);
  });

  it('should add child', () => {
    const newChild: TreeNode = { id: 'new', name: 'new.ts', type: 'file' };
    node.addChild(newChild);
    expect(node.getChildCount()).toBe(3);
  });

  it('should remove child', () => {
    const removed = node.removeChild('file1');
    expect(removed).toBe(true);
    expect(node.getChildCount()).toBe(1);
  });

  it('should return false when removing nonexistent child', () => {
    const removed = node.removeChild('nonexistent');
    expect(removed).toBe(false);
  });

  it('should get path', () => {
    expect(node.getPath()).toBe('root');
  });

  it('should handle single file node', () => {
    const fileNode = new FileTreeNode({
      id: 'single',
      name: 'index.ts',
      type: 'file'
    });
    expect(fileNode.hasChildren()).toBe(false);
    expect(fileNode.getChildCount()).toBe(0);
  });

  it('should handle multiple toggles', () => {
    node.toggle();
    expect(node.isExpanded()).toBe(true);
    node.toggle();
    node.toggle();
    expect(node.isExpanded()).toBe(true);
  });
});
