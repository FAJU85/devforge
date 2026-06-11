/**
 * RepoSelector component - dropdown for selecting between repositories
 */

export interface Repository {
  id: string;
  name: string;
  owner: string;
  url: string;
  language?: string;
  stars?: number;
}

export interface RepoSelectorOptions {
  repositories: Repository[];
  selectedId?: string;
  onSelect?: (repo: Repository) => void;
}

export function createRepoSelector(options: RepoSelectorOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'repo-selector';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;

  // Label
  const label = document.createElement('label');
  label.textContent = 'Repository';
  label.style.cssText = `
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  `;

  // Dropdown button
  const dropdown = document.createElement('button');
  dropdown.className = 'repo-dropdown';

  const selected = options.selectedId
    ? options.repositories.find((r) => r.id === options.selectedId)
    : options.repositories[0];

  dropdown.style.cssText = `
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background-color: var(--input-bg);
    color: var(--text);
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    transition: all 0.2s;
  `;

  const dropdownText = document.createElement('span');
  dropdownText.textContent = selected ? `${selected.owner}/${selected.name}` : 'Select repository...';

  const dropdownIcon = document.createElement('span');
  dropdownIcon.textContent = '▼';
  dropdownIcon.style.cssText = `
    font-size: 10px;
    transition: transform 0.2s;
  `;

  dropdown.appendChild(dropdownText);
  dropdown.appendChild(dropdownIcon);

  // Dropdown menu
  const menu = document.createElement('div');
  menu.className = 'repo-dropdown-menu';
  menu.style.cssText = `
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: var(--panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    max-height: 300px;
    overflow-y: auto;
    z-index: 100;
    margin-top: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  `;

  let isOpen = false;

  dropdown.addEventListener('click', () => {
    isOpen = !isOpen;
    menu.style.display = isOpen ? 'block' : 'none';
    dropdownIcon.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0)';
  });

  options.repositories.forEach((repo) => {
    const item = document.createElement('button');
    item.className = 'repo-dropdown-item';
    item.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 4px;
      width: 100%;
      padding: 12px;
      border: none;
      background: ${repo.id === selected?.id ? 'var(--border)' : 'transparent'};
      color: var(--text);
      cursor: pointer;
      text-align: left;
      font-size: 13px;
      transition: all 0.2s;
      font-family: inherit;
    `;

    item.addEventListener('mouseover', () => {
      item.style.backgroundColor = 'var(--border)';
    });

    item.addEventListener('mouseout', () => {
      item.style.backgroundColor = repo.id === selected?.id ? 'var(--border)' : 'transparent';
    });

    const itemName = document.createElement('div');
    itemName.textContent = `${repo.owner}/${repo.name}`;
    itemName.style.fontWeight = '500';

    const itemMeta = document.createElement('div');
    itemMeta.style.cssText = `
      font-size: 11px;
      color: var(--text-secondary);
      display: flex;
      gap: 12px;
    `;

    if (repo.language) {
      const lang = document.createElement('span');
      lang.textContent = repo.language;
      itemMeta.appendChild(lang);
    }

    if (repo.stars) {
      const stars = document.createElement('span');
      stars.textContent = `⭐ ${repo.stars}`;
      itemMeta.appendChild(stars);
    }

    item.appendChild(itemName);
    if (repo.language || repo.stars) {
      item.appendChild(itemMeta);
    }

    item.addEventListener('click', () => {
      dropdownText.textContent = `${repo.owner}/${repo.name}`;
      options.onSelect?.(repo);
      isOpen = false;
      menu.style.display = 'none';
      dropdownIcon.style.transform = 'rotate(0)';

      document.querySelectorAll('.repo-dropdown-item').forEach((el) => {
        if (el instanceof HTMLElement) {
          el.style.backgroundColor = 'transparent';
        }
      });
      item.style.backgroundColor = 'var(--border)';
    });

    menu.appendChild(item);
  });

  // Close menu on outside click
  document.addEventListener('click', (e) => {
    if (e.target !== dropdown && e.target !== menu && !menu.contains(e.target as Node)) {
      isOpen = false;
      menu.style.display = 'none';
      dropdownIcon.style.transform = 'rotate(0)';
    }
  });

  // Wrapper for positioning
  const wrapper = document.createElement('div');
  wrapper.style.cssText = `
    position: relative;
  `;

  wrapper.appendChild(dropdown);
  wrapper.appendChild(menu);

  container.appendChild(label);
  container.appendChild(wrapper);

  // Expose methods
  (container as any).setRepositories = (repos: Repository[]) => {
    menu.innerHTML = '';
    repos.forEach((repo) => {
      const item = document.createElement('button');
      item.className = 'repo-dropdown-item';
      item.style.cssText = `
        padding: 12px;
        border: none;
        background: transparent;
        color: var(--text);
        cursor: pointer;
        font-size: 13px;
      `;
      item.textContent = `${repo.owner}/${repo.name}`;
      item.addEventListener('click', () => options.onSelect?.(repo));
      menu.appendChild(item);
    });
  };

  return container;
}

export const RepoSelector = {
  create: createRepoSelector,
};
