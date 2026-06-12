/**
 * CommandPalette component - quick command search and execution
 */

interface Command {
  id: string;
  label: string;
  description?: string;
  category: string;
  icon?: string;
  onSelect: () => void;
}

export interface CommandPaletteOptions {
  commands: Command[];
  onClose?: () => void;
}

export function createCommandPalette(options: CommandPaletteOptions): HTMLDivElement {
  const overlay = document.createElement('div');
  overlay.className = 'command-palette-overlay';

  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    z-index: 9997;
    padding-top: 100px;
    animation: fadeIn 0.2s ease-out;
  `;

  const palette = document.createElement('div');
  palette.className = 'command-palette';

  palette.style.cssText = `
    background-color: var(--panel);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    width: 90%;
    max-width: 600px;
    max-height: 70vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    animation: slideDown 0.3s ease-out;
  `;

  // Search input
  const inputContainer = document.createElement('div');
  inputContainer.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  `;

  const searchIcon = document.createElement('span');
  searchIcon.textContent = '🔍';
  searchIcon.style.fontSize = '18px';

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'Search commands...';
  input.autofocus = true;
  input.style.cssText = `
    flex: 1;
    border: none;
    background: none;
    color: var(--text);
    font-size: 16px;
    font-family: inherit;
    outline: none;
  `;

  inputContainer.appendChild(searchIcon);
  inputContainer.appendChild(input);

  // Results list
  const resultsList = document.createElement('div');
  resultsList.className = 'command-results';
  resultsList.style.cssText = `
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  `;

  // Helper to render filtered results
  const renderResults = (query: string) => {
    resultsList.innerHTML = '';

    const filtered = query
      ? options.commands.filter(
          (cmd) =>
            cmd.label.toLowerCase().includes(query.toLowerCase()) ||
            cmd.description?.toLowerCase().includes(query.toLowerCase()) ||
            cmd.category.toLowerCase().includes(query.toLowerCase())
        )
      : options.commands;

    if (filtered.length === 0) {
      const empty = document.createElement('div');
      empty.style.cssText = `
        padding: 40px 20px;
        text-align: center;
        color: var(--text-secondary);
      `;
      empty.textContent = 'No commands found';
      resultsList.appendChild(empty);
      return;
    }

    // Group by category
    const grouped: { [key: string]: Command[] } = {};
    filtered.forEach((cmd) => {
      if (!grouped[cmd.category]) {
        grouped[cmd.category] = [];
      }
      grouped[cmd.category].push(cmd);
    });

    Object.entries(grouped).forEach(([category, cmds]) => {
      const categoryHeader = document.createElement('div');
      categoryHeader.style.cssText = `
        padding: 8px 16px;
        padding-top: 12px;
        color: var(--text-secondary);
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      `;
      categoryHeader.textContent = category;
      resultsList.appendChild(categoryHeader);

      cmds.forEach((cmd, index) => {
        const item = document.createElement('button');
        item.className = 'command-item';
        item.style.cssText = `
          padding: 12px 16px;
          border: none;
          background: ${index === 0 ? 'var(--accent)' : 'transparent'};
          color: ${index === 0 ? 'var(--bg)' : 'var(--text)'};
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;
          transition: all 0.1s;
          font-family: inherit;
          text-align: left;
          width: 100%;
        `;

        if (cmd.icon) {
          const icon = document.createElement('span');
          icon.textContent = cmd.icon;
          icon.style.fontSize = '18px';
          item.appendChild(icon);
        }

        const content = document.createElement('div');
        content.style.cssText = `
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        `;

        const label = document.createElement('div');
        label.textContent = cmd.label;
        label.style.fontWeight = '500';

        const desc = document.createElement('div');
        desc.textContent = cmd.description || '';
        desc.style.cssText = `
          font-size: 12px;
          opacity: 0.7;
        `;

        content.appendChild(label);
        if (cmd.description) content.appendChild(desc);
        item.appendChild(content);

        item.addEventListener('mouseover', () => {
          item.style.backgroundColor = 'var(--accent)';
          item.style.color = 'var(--bg)';
        });

        item.addEventListener('mouseout', () => {
          item.style.backgroundColor = 'transparent';
          item.style.color = 'var(--text)';
        });

        item.addEventListener('click', () => {
          cmd.onSelect();
          closeCommandPalette();
        });

        resultsList.appendChild(item);
      });
    });
  };

  // Initial render
  renderResults('');

  // Search handler
  input.addEventListener('input', (e) => {
    renderResults((e.target as HTMLInputElement).value);
  });

  // Close handlers
  const closeCommandPalette = () => {
    overlay.style.animation = 'fadeOut 0.2s ease-in';
    palette.style.animation = 'slideUp 0.2s ease-in';
    setTimeout(() => {
      overlay.remove();
      options.onClose?.();
    }, 200);
  };

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCommandPalette();
    }
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeCommandPalette();
    }
  });

  // Add animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes fadeOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    @keyframes slideDown {
      from {
        transform: translateY(-20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    @keyframes slideUp {
      from {
        transform: translateY(0);
        opacity: 1;
      }
      to {
        transform: translateY(-20px);
        opacity: 0;
      }
    }
  `;

  document.head.appendChild(style);

  palette.appendChild(inputContainer);
  palette.appendChild(resultsList);
  overlay.appendChild(palette);

  return overlay;
}

export const CommandPalette = {
  create: createCommandPalette,
};
