/**
 * RepoTree component - complete repository file explorer
 */

import { createFileTreeNode, FileTreeNodeOptions } from './FileTreeNode';

export interface RepoTreeOptions {
  files: FileTreeNodeOptions[];
  onFileSelect?: (path: string) => void;
  onFolderToggle?: (path: string, isOpen: boolean) => void;
}

export function createRepoTree(options: RepoTreeOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'repo-tree';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    height: 100%;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    background-color: var(--panel);
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 12px;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg);
  `;

  const title = document.createElement('h3');
  title.textContent = 'Files';
  title.style.cssText = `
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `;

  header.appendChild(title);

  // Tree container
  const treeContainer = document.createElement('div');
  treeContainer.className = 'file-tree-container';
  treeContainer.style.cssText = `
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 8px;
  `;

  // Render tree nodes
  options.files.forEach((file) => {
    const node = createFileTreeNode(
      file,
      0
    );
    treeContainer.appendChild(node);
  });

  // Expose methods
  (container as any).updateTree = (files: FileTreeNodeOptions[]) => {
    treeContainer.innerHTML = '';
    files.forEach((file) => {
      const node = createFileTreeNode(file, 0);
      treeContainer.appendChild(node);
    });
  };

  (container as any).expandAll = () => {
    treeContainer.querySelectorAll('.file-tree-children').forEach((el) => {
      if (el instanceof HTMLElement) {
        el.style.display = 'block';
      }
    });
    treeContainer.querySelectorAll('[style*="transform"]').forEach((el) => {
      if (el instanceof HTMLElement) {
        el.style.transform = 'rotate(90deg)';
      }
    });
  };

  (container as any).collapseAll = () => {
    treeContainer.querySelectorAll('.file-tree-children').forEach((el) => {
      if (el instanceof HTMLElement) {
        el.style.display = 'none';
      }
    });
    treeContainer.querySelectorAll('[style*="transform"]').forEach((el) => {
      if (el instanceof HTMLElement) {
        el.style.transform = 'rotate(0deg)';
      }
    });
  };

  container.appendChild(header);
  container.appendChild(treeContainer);

  return container;
}

export const RepoTree = {
  create: createRepoTree,
};
