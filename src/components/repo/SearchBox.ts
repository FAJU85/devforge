/**
 * SearchBox component - file and content search
 */

export interface SearchResult {
  id: string;
  title: string;
  path: string;
  type: 'file' | 'folder' | 'match';
  lineNumber?: number;
  preview?: string;
}

export interface SearchBoxOptions {
  onSearch: (query: string) => void;
  onResultSelect?: (result: SearchResult) => void;
  placeholder?: string;
}

export function createSearchBox(options: SearchBoxOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'search-box';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: relative;
  `;

  // Search input wrapper
  const inputWrapper = document.createElement('div');
  inputWrapper.style.cssText = `
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background-color: var(--input-bg);
    transition: all 0.2s;
  `;

  const searchIcon = document.createElement('span');
  searchIcon.textContent = '🔍';
  searchIcon.style.cssText = `
    font-size: 14px;
    color: var(--text-secondary);
  `;

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = options.placeholder || 'Search files...';
  input.className = 'search-input';

  input.style.cssText = `
    flex: 1;
    border: none;
    background: none;
    color: var(--text);
    font-size: 13px;
    font-family: inherit;
    padding: 10px 0;
    outline: none;
  `;

  const clearBtn = document.createElement('button');
  clearBtn.textContent = '✕';
  clearBtn.style.cssText = `
    display: none;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 16px;
    padding: 4px;
    transition: color 0.2s;
  `;

  clearBtn.addEventListener('mouseover', () => {
    clearBtn.style.color = 'var(--text)';
  });

  clearBtn.addEventListener('mouseout', () => {
    clearBtn.style.color = 'var(--text-secondary)';
  });

  clearBtn.addEventListener('click', () => {
    input.value = '';
    clearBtn.style.display = 'none';
    resultsContainer.innerHTML = '';
    input.focus();
  });

  input.addEventListener('focus', () => {
    inputWrapper.style.borderColor = 'var(--accent)';
    inputWrapper.style.boxShadow = '0 0 0 2px var(--accent-dim)';
  });

  input.addEventListener('blur', () => {
    inputWrapper.style.borderColor = 'var(--border)';
    inputWrapper.style.boxShadow = 'none';
  });

  input.addEventListener('input', (e) => {
    const query = (e.target as HTMLInputElement).value;
    clearBtn.style.display = query ? 'block' : 'none';
    if (query) {
      options.onSearch(query);
    } else {
      resultsContainer.innerHTML = '';
    }
  });

  inputWrapper.appendChild(searchIcon);
  inputWrapper.appendChild(input);
  inputWrapper.appendChild(clearBtn);

  // Results container
  const resultsContainer = document.createElement('div');
  resultsContainer.className = 'search-results';
  resultsContainer.style.cssText = `
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: var(--panel);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 6px 6px;
    max-height: 300px;
    overflow-y: auto;
    z-index: 99;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  `;

  // Expose method to show results
  (container as any).showResults = (results: SearchResult[]) => {
    if (results.length === 0) {
      resultsContainer.innerHTML = '';
      resultsContainer.style.display = 'none';
      return;
    }

    resultsContainer.innerHTML = '';
    resultsContainer.style.display = 'block';

    results.slice(0, 10).forEach((result) => {
      const resultItem = document.createElement('button');
      resultItem.className = 'search-result-item';
      resultItem.style.cssText = `
        display: flex;
        flex-direction: column;
        gap: 4px;
        width: 100%;
        padding: 12px;
        border: none;
        background: transparent;
        color: var(--text);
        cursor: pointer;
        text-align: left;
        font-size: 12px;
        transition: all 0.2s;
        font-family: inherit;
        border-bottom: 1px solid var(--border);
      `;

      resultItem.addEventListener('mouseover', () => {
        resultItem.style.backgroundColor = 'var(--border)';
      });

      resultItem.addEventListener('mouseout', () => {
        resultItem.style.backgroundColor = 'transparent';
      });

      const title = document.createElement('div');
      title.style.fontWeight = '500';
      const icon = result.type === 'folder' ? '📁' : '📄';
      title.textContent = `${icon} ${result.title}`;

      const path = document.createElement('div');
      path.style.cssText = `
        font-size: 11px;
        color: var(--text-secondary);
      `;
      path.textContent = result.path;

      if (result.preview) {
        const preview = document.createElement('div');
        preview.style.cssText = `
          font-size: 11px;
          color: var(--text-secondary);
          margin-top: 4px;
          font-family: monospace;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        `;
        preview.textContent = result.preview;
        resultItem.appendChild(title);
        resultItem.appendChild(path);
        resultItem.appendChild(preview);
      } else {
        resultItem.appendChild(title);
        resultItem.appendChild(path);
      }

      resultItem.addEventListener('click', () => {
        options.onResultSelect?.(result);
        input.value = '';
        clearBtn.style.display = 'none';
        resultsContainer.innerHTML = '';
        resultsContainer.style.display = 'none';
      });

      resultsContainer.appendChild(resultItem);
    });

    if (results.length > 10) {
      const more = document.createElement('div');
      more.style.cssText = `
        padding: 8px 12px;
        text-align: center;
        font-size: 11px;
        color: var(--text-secondary);
        border-top: 1px solid var(--border);
      `;
      more.textContent = `+${results.length - 10} more results`;
      resultsContainer.appendChild(more);
    }
  };

  container.appendChild(inputWrapper);
  container.appendChild(resultsContainer);

  return container;
}

export const SearchBox = {
  create: createSearchBox,
};
