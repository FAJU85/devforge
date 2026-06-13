import { describe, it, expect, beforeEach, vi } from 'vitest';

interface TreeItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: TreeItem[];
}

class RepoTree {
  private root: TreeItem | null = null;
  private expandedNodes: Set<string> = new Set();
  private selectedNode: string | null = null;

  setRoot(root: TreeItem): void {
    this.root = root;
  }

  getRoot(): TreeItem | null {
    return this.root;
  }

  expandNode(nodeId: string): void {
    this.expandedNodes.add(nodeId);
  }

  collapseNode(nodeId: string): void {
    this.expandedNodes.delete(nodeId);
  }

  isExpanded(nodeId: string): boolean {
    return this.expandedNodes.has(nodeId);
  }

  selectNode(nodeId: string): void {
    this.selectedNode = nodeId;
  }

  getSelectedNode(): string | null {
    return this.selectedNode;
  }

  findNode(nodeId: string): TreeItem | null {
    const search = (node: TreeItem | null): TreeItem | null => {
      if (!node) return null;
      if (node.id === nodeId) return node;
      if (node.children) {
        for (const child of node.children) {
          const result = search(child);
          if (result) return result;
        }
      }
      return null;
    };
    return search(this.root);
  }

  getChildren(nodeId: string): TreeItem[] {
    const node = this.findNode(nodeId);
    return node?.children || [];
  }

  expandAll(): void {
    const expandRecursive = (node: TreeItem | null) => {
      if (!node) return;
      this.expandedNodes.add(node.id);
      if (node.children) {
        node.children.forEach(child => expandRecursive(child));
      }
    };
    expandRecursive(this.root);
  }

  collapseAll(): void {
    this.expandedNodes.clear();
  }
}

describe('RepoTree', () => {
  let tree: RepoTree;
  const mockRoot: TreeItem = {
    id: 'root',
    name: 'src',
    type: 'folder',
    children: [
      { id: 'file1', name: 'main.ts', type: 'file' },
      {
        id: 'folder1',
        name: 'utils',
        type: 'folder',
        children: [
          { id: 'file2', name: 'helper.ts', type: 'file' }
        ]
      }
    ]
  };

  beforeEach(() => {
    tree = new RepoTree();
    tree.setRoot(mockRoot);
  });

  it('should set and get root', () => {
    expect(tree.getRoot()?.id).toBe('root');
  });

  it('should expand node', () => {
    tree.expandNode('root');
    expect(tree.isExpanded('root')).toBe(true);
  });

  it('should collapse node', () => {
    tree.expandNode('root');
    tree.collapseNode('root');
    expect(tree.isExpanded('root')).toBe(false);
  });

  it('should select node', () => {
    tree.selectNode('file1');
    expect(tree.getSelectedNode()).toBe('file1');
  });

  it('should find node', () => {
    const found = tree.findNode('file1');
    expect(found?.name).toBe('main.ts');
  });

  it('should get children', () => {
    const children = tree.getChildren('folder1');
    expect(children).toHaveLength(1);
  });

  it('should expand all nodes', () => {
    tree.expandAll();
    expect(tree.isExpanded('root')).toBe(true);
    expect(tree.isExpanded('folder1')).toBe(true);
  });

  it('should collapse all nodes', () => {
    tree.expandAll();
    tree.collapseAll();
    expect(tree.isExpanded('root')).toBe(false);
  });

  it('should return null for nonexistent node', () => {
    expect(tree.findNode('nonexistent')).toBeNull();
  });
});
