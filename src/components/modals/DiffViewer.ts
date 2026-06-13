/**
 * DiffViewer component - side-by-side file diff visualization
 */

export interface DiffLine {
  type: 'add' | 'remove' | 'context';
  lineNumber?: number;
  content: string;
}

export interface DiffViewerOptions {
  oldFile: string;
  newFile: string;
  oldContent: string;
  newContent: string;
  onClose?: () => void;
  onApply?: () => void;
}

export function createDiffViewer(options: DiffViewerOptions): HTMLDivElement {
  const modal = document.createElement('div');
  modal.className = 'diff-viewer-modal';

  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9996;
    padding: 20px;
  `;

  const viewer = document.createElement('div');
  viewer.style.cssText = `
    background-color: var(--panel);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    width: 100%;
    max-width: 1000px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg);
  `;

  const title = document.createElement('h2');
  title.textContent = '📋 File Diff';
  title.style.cssText = `
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `;

  const files = document.createElement('div');
  files.style.cssText = `
    display: flex;
    gap: 20px;
    font-size: 12px;
    color: var(--text-secondary);
  `;

  const oldFileDiv = document.createElement('div');
  oldFileDiv.textContent = `Old: ${options.oldFile}`;
  oldFileDiv.style.cssText = `color: var(--red);`;

  const newFileDiv = document.createElement('div');
  newFileDiv.textContent = `New: ${options.newFile}`;
  newFileDiv.style.cssText = `color: var(--green);`;

  files.appendChild(oldFileDiv);
  files.appendChild(newFileDiv);

  header.appendChild(title);
  header.appendChild(files);

  // Content area with two columns
  const content = document.createElement('div');
  content.style.cssText = `
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    overflow: hidden;
    border-bottom: 1px solid var(--border);
  `;

  // Old content
  const oldColumn = document.createElement('div');
  oldColumn.style.cssText = `
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border);
    overflow: auto;
  `;

  const oldHeader = document.createElement('div');
  oldHeader.style.cssText = `
    padding: 8px 12px;
    background-color: rgba(239, 68, 68, 0.1);
    border-bottom: 1px solid var(--border);
    font-size: 11px;
    font-weight: 600;
    color: var(--red);
    position: sticky;
    top: 0;
  `;
  oldHeader.textContent = '- Removed';

  const oldPre = document.createElement('pre');
  oldPre.textContent = options.oldContent;
  oldPre.style.cssText = `
    margin: 0;
    padding: 12px;
    font-size: 12px;
    font-family: monospace;
    color: var(--text);
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  `;

  oldColumn.appendChild(oldHeader);
  oldColumn.appendChild(oldPre);

  // New content
  const newColumn = document.createElement('div');
  newColumn.style.cssText = `
    display: flex;
    flex-direction: column;
    overflow: auto;
  `;

  const newHeader = document.createElement('div');
  newHeader.style.cssText = `
    padding: 8px 12px;
    background-color: rgba(16, 185, 129, 0.1);
    border-bottom: 1px solid var(--border);
    font-size: 11px;
    font-weight: 600;
    color: var(--green);
    position: sticky;
    top: 0;
  `;
  newHeader.textContent = '+ Added';

  const newPre = document.createElement('pre');
  newPre.textContent = options.newContent;
  newPre.style.cssText = `
    margin: 0;
    padding: 12px;
    font-size: 12px;
    font-family: monospace;
    color: var(--text);
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  `;

  newColumn.appendChild(newHeader);
  newColumn.appendChild(newPre);

  content.appendChild(oldColumn);
  content.appendChild(newColumn);

  // Footer
  const footer = document.createElement('div');
  footer.style.cssText = `
    padding: 12px 16px;
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  `;

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.style.cssText = `
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background-color: transparent;
    color: var(--text);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  closeBtn.addEventListener('click', () => {
    modal.style.animation = 'fadeOut 0.2s ease-in';
    setTimeout(() => {
      modal.remove();
      options.onClose?.();
    }, 200);
  });

  const applyBtn = document.createElement('button');
  applyBtn.textContent = '✓ Apply';
  applyBtn.style.cssText = `
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    background-color: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  applyBtn.addEventListener('mouseover', () => {
    applyBtn.style.opacity = '0.8';
  });

  applyBtn.addEventListener('mouseout', () => {
    applyBtn.style.opacity = '1';
  });

  applyBtn.addEventListener('click', () => {
    options.onApply?.();
    closeBtn.click();
  });

  footer.appendChild(closeBtn);
  footer.appendChild(applyBtn);

  viewer.appendChild(header);
  viewer.appendChild(content);
  viewer.appendChild(footer);
  modal.appendChild(viewer);

  // Animations
  const style = document.createElement('style');
  if (!document.head.querySelector('style[data-diff-animations]')) {
    style.setAttribute('data-diff-animations', 'true');
    style.textContent = `
      @keyframes fadeOut {
        to { opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

  return modal;
}

export const DiffViewer = {
  create: createDiffViewer,
};
