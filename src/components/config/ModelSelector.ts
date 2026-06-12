/**
 * ModelSelector component - AI model selection with capabilities
 */

export interface Model {
  id: string;
  name: string;
  provider: string;
  contextWindow: number;
  costPer1kTokens?: {
    input: number;
    output: number;
  };
  capabilities?: string[];
  recommended?: boolean;
}

export interface ModelSelectorOptions {
  models: Model[];
  selectedId?: string;
  onSelect?: (model: Model) => void;
}

export function createModelSelector(options: ModelSelectorOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'model-selector';

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 12px;
  `;

  // Label
  const label = document.createElement('label');
  label.textContent = 'Model';
  label.style.cssText = `
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  `;

  // List of models
  const list = document.createElement('div');
  list.className = 'model-list';
  list.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 400px;
    overflow-y: auto;
  `;

  const selected = options.selectedId
    ? options.models.find((m) => m.id === options.selectedId)
    : options.models[0];

  options.models.forEach((model) => {
    const item = document.createElement('button');
    item.className = 'model-item';
    item.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      border: 1px solid ${model.id === selected?.id ? 'var(--accent)' : 'var(--border)'};
      border-radius: 6px;
      background-color: ${model.id === selected?.id ? 'var(--accent)' : 'var(--panel)'};
      color: ${model.id === selected?.id ? 'var(--bg)' : 'var(--text)'};
      cursor: pointer;
      font-family: inherit;
      transition: all 0.2s;
      text-align: left;
    `;

    item.addEventListener('mouseover', () => {
      if (model.id !== selected?.id) {
        item.style.backgroundColor = 'var(--border)';
      }
    });

    item.addEventListener('mouseout', () => {
      if (model.id !== selected?.id) {
        item.style.backgroundColor = 'var(--panel)';
      }
    });

    item.addEventListener('click', () => {
      document.querySelectorAll('.model-item').forEach((el) => {
        if (el instanceof HTMLElement) {
          el.style.borderColor = 'var(--border)';
          el.style.backgroundColor = 'var(--panel)';
          el.style.color = 'var(--text)';
        }
      });
      item.style.borderColor = 'var(--accent)';
      item.style.backgroundColor = 'var(--accent)';
      item.style.color = 'var(--bg)';
      options.onSelect?.(model);
    });

    // Left side - model info
    const info = document.createElement('div');
    info.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
    `;

    const modelName = document.createElement('div');
    modelName.style.cssText = `
      font-weight: 600;
      font-size: 13px;
    `;
    modelName.textContent = model.name;
    if (model.recommended) {
      modelName.textContent += ' ⭐';
    }

    const provider = document.createElement('div');
    provider.style.cssText = `
      font-size: 11px;
      opacity: 0.8;
    `;
    provider.textContent = `${model.provider} • ${model.contextWindow.toLocaleString()} tokens`;

    if (model.capabilities && model.capabilities.length > 0) {
      const caps = document.createElement('div');
      caps.style.cssText = `
        font-size: 10px;
        opacity: 0.7;
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-top: 4px;
      `;
      model.capabilities.slice(0, 3).forEach((cap) => {
        const capTag = document.createElement('span');
        capTag.textContent = cap;
        capTag.style.cssText = `
          background-color: rgba(255, 255, 255, 0.1);
          padding: 2px 6px;
          border-radius: 3px;
        `;
        caps.appendChild(capTag);
      });
      info.appendChild(modelName);
      info.appendChild(provider);
      info.appendChild(caps);
    } else {
      info.appendChild(modelName);
      info.appendChild(provider);
    }

    // Right side - cost
    const cost = document.createElement('div');
    cost.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 2px;
      text-align: right;
      font-size: 11px;
      opacity: 0.8;
    `;

    if (model.costPer1kTokens) {
      const costInput = document.createElement('div');
      costInput.textContent = `$${model.costPer1kTokens.input.toFixed(4)}/1k in`;
      cost.appendChild(costInput);

      const costOutput = document.createElement('div');
      costOutput.textContent = `$${model.costPer1kTokens.output.toFixed(4)}/1k out`;
      cost.appendChild(costOutput);
    }

    item.appendChild(info);
    if (cost.children.length > 0) {
      item.appendChild(cost);
    }

    list.appendChild(item);
  });

  container.appendChild(label);
  container.appendChild(list);

  // Expose methods
  (container as any).setModels = (models: Model[]) => {
    list.innerHTML = '';
    options.models = models;
    models.forEach((model) => {
      const item = document.createElement('button');
      item.className = 'model-item';
      item.textContent = model.name;
      item.addEventListener('click', () => options.onSelect?.(model));
      list.appendChild(item);
    });
  };

  return container;
}

export const ModelSelector = {
  create: createModelSelector,
};
