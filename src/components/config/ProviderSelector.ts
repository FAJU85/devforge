/**
 * ProviderSelector component - AI provider selection (OpenAI, Groq, HuggingFace, etc.)
 */

export interface Provider {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'available' | 'configured' | 'unavailable';
  url?: string;
}

export interface ProviderSelectorOptions {
  providers: Provider[];
  selectedId?: string;
  onSelect?: (provider: Provider) => void;
}

export function createProviderSelector(options: ProviderSelectorOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'provider-selector';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 12px;
  `;

  // Label
  const label = document.createElement('label');
  label.textContent = 'AI Provider';
  label.style.cssText = `
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  `;

  // Grid of provider cards
  const grid = document.createElement('div');
  grid.className = 'provider-grid';
  grid.style.cssText = `
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
  `;

  options.providers.forEach((provider) => {
    const card = document.createElement('button');
    card.className = `provider-card provider-${provider.status}`;

    const isSelected = provider.id === options.selectedId;

    card.style.cssText = `
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 16px;
      border: 2px solid ${isSelected ? 'var(--accent)' : 'var(--border)'};
      border-radius: 8px;
      background-color: var(--panel);
      color: var(--text);
      cursor: ${provider.status === 'unavailable' ? 'not-allowed' : 'pointer'};
      font-family: inherit;
      transition: all 0.2s;
      opacity: ${provider.status === 'unavailable' ? '0.5' : '1'};
    `;

    if (provider.status !== 'unavailable') {
      card.addEventListener('mouseover', () => {
        card.style.backgroundColor = 'var(--border)';
        card.style.transform = 'translateY(-2px)';
      });

      card.addEventListener('mouseout', () => {
        card.style.backgroundColor = 'var(--panel)';
        card.style.transform = 'translateY(0)';
      });

      card.addEventListener('click', () => {
        document.querySelectorAll('.provider-card').forEach((c) => {
          if (c instanceof HTMLElement) {
            c.style.borderColor = 'var(--border)';
          }
        });
        card.style.borderColor = 'var(--accent)';
        options.onSelect?.(provider);
      });
    }

    // Icon
    const icon = document.createElement('div');
    icon.textContent = provider.icon;
    icon.style.cssText = `
      font-size: 32px;
    `;

    // Name
    const name = document.createElement('div');
    name.textContent = provider.name;
    name.style.cssText = `
      font-size: 13px;
      font-weight: 600;
      text-align: center;
    `;

    // Status badge
    const badge = document.createElement('div');
    badge.style.cssText = `
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 4px;
      background-color: ${
        provider.status === 'configured'
          ? 'rgba(16, 185, 129, 0.2)'
          : provider.status === 'available'
            ? 'rgba(59, 130, 246, 0.2)'
            : 'rgba(107, 114, 128, 0.2)'
      };
      color: ${
        provider.status === 'configured'
          ? 'var(--green)'
          : provider.status === 'available'
            ? 'var(--accent)'
            : 'var(--text-secondary)'
      };
    `;

    badge.textContent =
      provider.status === 'configured'
        ? '✓ Configured'
        : provider.status === 'available'
          ? 'Available'
          : 'Unavailable';

    card.appendChild(icon);
    card.appendChild(name);
    card.appendChild(badge);

    grid.appendChild(card);
  });

  container.appendChild(label);
  container.appendChild(grid);

  // Expose methods
  (container as any).setProviders = (providers: Provider[]) => {
    grid.innerHTML = '';
    options.providers = providers;
    providers.forEach((provider) => {
      const card = document.createElement('button');
      card.className = `provider-card provider-${provider.status}`;
      card.textContent = provider.name;
      card.addEventListener('click', () => options.onSelect?.(provider));
      grid.appendChild(card);
    });
  };

  return container;
}

export const ProviderSelector = {
  create: createProviderSelector,
};
