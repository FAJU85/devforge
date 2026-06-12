/**
 * FileTreeNode component - tree node for files and folders
 */

export interface FileTreeNodeOptions {
  name: string;
  type: 'file' | 'folder';
  path: string;
  isOpen?: boolean;
  children?: FileTreeNodeOptions[];
  onSelect?: (path: string) => void;
  onToggle?: (path: string, isOpen: boolean) => void;
}

export function createFileTreeNode(options: FileTreeNodeOptions, depth: number = 0): HTMLDivElement {
  const container = document.createElement('div');
  container.className = `file-tree-node depth-${depth}`;

  container.style.cssText = `
    display: flex;
    flex-direction: column;
  `;

  // Node item
  const nodeItem = document.createElement('button');
  nodeItem.className = 'file-tree-item';
  nodeItem.style.cssText = `
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    margin-left: ${depth * 16}px;
    border: none;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
    font-family: inherit;
    text-align: left;
    width: calc(100% - ${depth * 16}px);
  `;

  const isFolder = options.type === 'folder';
  const hasChildren = isFolder && options.children && options.children.length > 0;

  // Toggle icon
  const toggleIcon = document.createElement('span');
  toggleIcon.style.cssText = `
    display: ${hasChildren ? 'inline' : 'none'};
    font-size: 12px;
    transition: transform 0.2s;
    transform: rotate(${options.isOpen ? 90 : 0}deg);
  `;
  toggleIcon.textContent = '▶';

  // File/folder icon
  const fileIcon = document.createElement('span');
  fileIcon.style.fontSize = '14px';

  if (options.type === 'folder') {
    fileIcon.textContent = options.isOpen ? '📂' : '📁';
  } else {
    // Determine file icon by extension
    const ext = options.name.split('.').pop()?.toLowerCase();
    const icons: { [key: string]: string } = {
      js: '📜',
      ts: '📘',
      tsx: '⚛️',
      jsx: '⚛️',
      json: '📋',
      css: '🎨',
      scss: '🎨',
      html: '🌐',
      md: '📝',
      py: '🐍',
      go: '🐹',
      rs: '⚙️',
      java: '☕',
      cpp: '⚙️',
      c: '⚙️',
      git: '📦',
    };
    fileIcon.textContent = icons[ext || ''] || '📄';
  }

  // File name
  const fileName = document.createElement('span');
  fileName.textContent = options.name;
  fileName.style.cssText = `
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  `;

  nodeItem.addEventListener('mouseover', () => {
    nodeItem.style.backgroundColor = 'var(--border)';
  });

  nodeItem.addEventListener('mouseout', () => {
    nodeItem.style.backgroundColor = 'transparent';
  });

  nodeItem.addEventListener('click', (e) => {
    e.stopPropagation();
    if (hasChildren) {
      const childrenContainer = container.querySelector('.file-tree-children') as HTMLElement;
      const isCurrentlyOpen = childrenContainer && childrenContainer.style.display !== 'none';
      const newOpenState = !isCurrentlyOpen;

      if (childrenContainer) {
        childrenContainer.style.display = newOpenState ? 'block' : 'none';
      }

      toggleIcon.style.transform = `rotate(${newOpenState ? 90 : 0}deg)`;
      fileIcon.textContent = newOpenState ? '📂' : '📁';
      options.onToggle?.(options.path, newOpenState);
    } else {
      options.onSelect?.(options.path);
    }
  });

  nodeItem.appendChild(toggleIcon);
  nodeItem.appendChild(fileIcon);
  nodeItem.appendChild(fileName);

  container.appendChild(nodeItem);

  // Children
  if (hasChildren) {
    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'file-tree-children';
    childrenContainer.style.cssText = `
      display: ${options.isOpen ? 'block' : 'none'};
    `;

    options.children!.forEach((child) => {
      const childNode = createFileTreeNode(child, depth + 1);
      childrenContainer.appendChild(childNode);
    });

    container.appendChild(childrenContainer);
  }

  return container;
}

export const FileTreeNode = {
  create: createFileTreeNode,
};
