/**
 * FileList component - scrollable list of files with line numbers
 */

export interface FileItem {
  id: string;
  path: string;
  name: string;
  language?: string;
  lines?: number;
  selected?: boolean;
  onSelect?: () => void;
}

export interface FileListOptions {
  files: FileItem[];
  onSelect?: (file: FileItem) => void;
  onRemove?: (id: string) => void;
}

export function createFileList(options: FileListOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'file-list';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background-color: var(--panel);
    overflow: hidden;
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 12px;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg);
    display: flex;
    justify-content: space-between;
    align-items: center;
  `;

  const title = document.createElement('h3');
  title.textContent = 'Files';
  title.style.cssText = `
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `;

  const count = document.createElement('span');
  count.textContent = `${options.files.length}`;
  count.style.cssText = `
    font-size: 11px;
    padding: 2px 6px;
    background-color: var(--border);
    border-radius: 3px;
    color: var(--text-secondary);
  `;

  header.appendChild(title);
  header.appendChild(count);

  // Files container
  const filesContainer = document.createElement('div');
  filesContainer.className = 'files-container';
  filesContainer.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px;
    max-height: 500px;
    overflow-y: auto;
  `;

  // Get file language icon
  const getLanguageIcon = (lang?: string): string => {
    const icons: { [key: string]: string } = {
      typescript: '📘',
      javascript: '📜',
      python: '🐍',
      go: '🐹',
      rust: '⚙️',
      java: '☕',
      cpp: '⚙️',
      c: '⚙️',
      html: '🌐',
      css: '🎨',
      json: '📋',
      yaml: '📝',
      markdown: '📝',
    };
    return icons[lang?.toLowerCase() || ''] || '📄';
  };

  options.files.forEach((file) => {
    const fileItem = document.createElement('button');
    fileItem.className = `file-item ${file.selected ? 'selected' : ''}`;

    fileItem.style.cssText = `
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px;
      border: 1px solid ${file.selected ? 'var(--accent)' : 'var(--border)'};
      border-radius: 4px;
      background-color: ${file.selected ? 'var(--accent)' : 'transparent'};
      color: ${file.selected ? 'var(--bg)' : 'var(--text)'};
      cursor: pointer;
      font-family: inherit;
      transition: all 0.2s;
      text-align: left;
    `;

    // Icon
    const icon = document.createElement('span');
    icon.textContent = getLanguageIcon(file.language);
    icon.style.fontSize = '16px';

    // Info
    const info = document.createElement('div');
    info.style.cssText = `
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    `;

    const name = document.createElement('div');
    name.textContent = file.name;
    name.style.cssText = `
      font-weight: 500;
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    `;

    const path = document.createElement('div');
    path.textContent = file.path;
    path.style.cssText = `
      font-size: 10px;
      opacity: 0.8;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    `;

    info.appendChild(name);
    info.appendChild(path);

    // Meta
    const meta = document.createElement('div');
    meta.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 10px;
      opacity: 0.8;
    `;

    if (file.lines) {
      const lines = document.createElement('span');
      lines.textContent = `${file.lines} lines`;
      meta.appendChild(lines);
    }

    if (file.language) {
      const lang = document.createElement('span');
      lang.textContent = file.language;
      meta.appendChild(lang);
    }

    fileItem.addEventListener('mouseover', () => {
      if (!file.selected) {
        fileItem.style.backgroundColor = 'var(--border)';
      }
    });

    fileItem.addEventListener('mouseout', () => {
      if (!file.selected) {
        fileItem.style.backgroundColor = 'transparent';
      }
    });

    fileItem.addEventListener('click', () => {
      options.onSelect?.(file);
    });

    fileItem.appendChild(icon);
    fileItem.appendChild(info);
    if (meta.children.length > 0) {
      fileItem.appendChild(meta);
    }

    filesContainer.appendChild(fileItem);
  });

  if (options.files.length === 0) {
    const empty = document.createElement('div');
    empty.style.cssText = `
      padding: 20px;
      text-align: center;
      color: var(--text-secondary);
      font-size: 12px;
    `;
    empty.textContent = 'No files selected';
    filesContainer.appendChild(empty);
  }

  container.appendChild(header);
  container.appendChild(filesContainer);

  return container;
}

export const FileList = {
  create: createFileList,
};
