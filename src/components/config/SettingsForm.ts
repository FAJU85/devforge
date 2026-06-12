/**
 * SettingsForm component - complete configuration form
 */

export interface SettingValue {
  id: string;
  label: string;
  type: 'text' | 'number' | 'toggle' | 'select';
  value: any;
  options?: { label: string; value: any }[];
  onChange?: (value: any) => void;
  help?: string;
}

export interface SettingsFormOptions {
  title: string;
  description?: string;
  sections: {
    title: string;
    settings: SettingValue[];
  }[];
  onSave?: (settings: { [key: string]: any }) => void;
  onCancel?: () => void;
}

export function createSettingsForm(options: SettingsFormOptions): HTMLDivElement {
  const form = document.createElement('form');
  form.className = 'settings-form';

  form.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 24px;
    max-width: 600px;
  `;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
  });

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
  `;

  const title = document.createElement('h2');
  title.textContent = options.title;
  title.style.cssText = `
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--text);
  `;

  header.appendChild(title);

  if (options.description) {
    const desc = document.createElement('p');
    desc.textContent = options.description;
    desc.style.cssText = `
      margin: 0;
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.5;
    `;
    header.appendChild(desc);
  }

  form.appendChild(header);

  // Sections
  const formData: { [key: string]: any } = {};

  options.sections.forEach((section) => {
    const sectionDiv = document.createElement('div');
    sectionDiv.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 16px;
      background-color: var(--panel);
      border-radius: 6px;
      border: 1px solid var(--border);
    `;

    const sectionTitle = document.createElement('h3');
    sectionTitle.textContent = section.title;
    sectionTitle.style.cssText = `
      margin: 0 0 8px 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--text);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    `;

    sectionDiv.appendChild(sectionTitle);

    // Settings items
    const itemsContainer = document.createElement('div');
    itemsContainer.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 12px;
    `;

    section.settings.forEach((setting) => {
      const item = document.createElement('div');
      item.style.cssText = `
        display: flex;
        flex-direction: column;
        gap: 4px;
      `;

      const label = document.createElement('label');
      label.textContent = setting.label;
      label.style.cssText = `
        font-size: 13px;
        font-weight: 500;
        color: var(--text);
      `;

      let control: HTMLElement;
      let valueGetter: () => any;

      if (setting.type === 'text') {
        const input = document.createElement('input');
        input.type = 'text';
        input.value = setting.value || '';
        input.style.cssText = `
          padding: 8px 12px;
          border: 1px solid var(--border);
          border-radius: 4px;
          background-color: var(--input-bg);
          color: var(--text);
          font-size: 13px;
          font-family: inherit;
        `;

        input.addEventListener('change', () => {
          formData[setting.id] = input.value;
          setting.onChange?.(input.value);
        });

        control = input;
        valueGetter = () => input.value;
      } else if (setting.type === 'number') {
        const input = document.createElement('input');
        input.type = 'number';
        input.value = String(setting.value || 0);
        input.style.cssText = `
          padding: 8px 12px;
          border: 1px solid var(--border);
          border-radius: 4px;
          background-color: var(--input-bg);
          color: var(--text);
          font-size: 13px;
          font-family: inherit;
        `;

        input.addEventListener('change', () => {
          const value = parseFloat(input.value);
          formData[setting.id] = value;
          setting.onChange?.(value);
        });

        control = input;
        valueGetter = () => parseFloat(input.value);
      } else if (setting.type === 'toggle') {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = setting.value || false;
        checkbox.style.cssText = `
          width: 18px;
          height: 18px;
          cursor: pointer;
        `;

        checkbox.addEventListener('change', () => {
          formData[setting.id] = checkbox.checked;
          setting.onChange?.(checkbox.checked);
        });

        control = checkbox;
        valueGetter = () => checkbox.checked;
      } else {
        const select = document.createElement('select');
        select.value = String(setting.value || '');
        select.style.cssText = `
          padding: 8px 12px;
          border: 1px solid var(--border);
          border-radius: 4px;
          background-color: var(--input-bg);
          color: var(--text);
          font-size: 13px;
          font-family: inherit;
          cursor: pointer;
        `;

        setting.options?.forEach((opt) => {
          const option = document.createElement('option');
          option.value = String(opt.value);
          option.textContent = opt.label;
          select.appendChild(option);
        });

        select.addEventListener('change', () => {
          const value = setting.options?.find((opt) => opt.value === select.value)?.value;
          formData[setting.id] = value;
          setting.onChange?.(value);
        });

        control = select;
        valueGetter = () => setting.options?.find((opt) => String(opt.value) === select.value)?.value;
      }

      item.appendChild(label);
      item.appendChild(control);

      if (setting.help) {
        const help = document.createElement('div');
        help.textContent = setting.help;
        help.style.cssText = `
          font-size: 11px;
          color: var(--text-secondary);
          margin-top: 2px;
        `;
        item.appendChild(help);
      }

      itemsContainer.appendChild(item);
      formData[setting.id] = valueGetter();
    });

    sectionDiv.appendChild(itemsContainer);
    form.appendChild(sectionDiv);
  });

  // Action buttons
  const actions = document.createElement('div');
  actions.style.cssText = `
    display: flex;
    gap: 12px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
  `;

  const saveBtn = document.createElement('button');
  saveBtn.type = 'button';
  saveBtn.textContent = '💾 Save Settings';
  saveBtn.style.cssText = `
    flex: 1;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    background-color: var(--accent);
    color: var(--bg);
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s;
    font-family: inherit;
  `;

  saveBtn.addEventListener('mouseover', () => {
    saveBtn.style.opacity = '0.8';
  });

  saveBtn.addEventListener('mouseout', () => {
    saveBtn.style.opacity = '1';
  });

  saveBtn.addEventListener('click', () => {
    options.onSave?.(formData);
    saveBtn.textContent = '✓ Saved';
    setTimeout(() => {
      saveBtn.textContent = '💾 Save Settings';
    }, 2000);
  });

  actions.appendChild(saveBtn);

  if (options.onCancel) {
    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.style.cssText = `
      padding: 10px 16px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background-color: transparent;
      color: var(--text);
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
      font-family: inherit;
    `;

    cancelBtn.addEventListener('mouseover', () => {
      cancelBtn.style.backgroundColor = 'var(--border)';
    });

    cancelBtn.addEventListener('mouseout', () => {
      cancelBtn.style.backgroundColor = 'transparent';
    });

    cancelBtn.addEventListener('click', () => {
      options.onCancel?.();
    });

    actions.appendChild(cancelBtn);
  }

  form.appendChild(actions);

  return form;
}

export const SettingsForm = {
  create: createSettingsForm,
};
