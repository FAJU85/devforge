/**
 * TokenMeter component - displays token usage and limits
 */

export interface TokenMeterOptions {
  currentTokens: number;
  maxTokens?: number;
  contextTokens?: number;
  onThresholdReached?: (percentage: number) => void;
}

export function createTokenMeter(options: TokenMeterOptions): HTMLDivElement {
  const container = document.createElement('div');
  container.className = 'token-meter';

  const maxTokens = options.maxTokens || 4096;
  const percentage = Math.min((options.currentTokens / maxTokens) * 100, 100);

  container.style.cssText = `
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background-color: var(--panel);
    border-radius: 6px;
    border: 1px solid var(--border);
  `;

  // Header
  const header = document.createElement('div');
  header.style.cssText = `
    display: flex;
    justify-content: space-between;
    align-items: center;
  `;

  const label = document.createElement('span');
  label.textContent = 'Token Usage';
  label.style.cssText = `
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  `;

  const stats = document.createElement('span');
  stats.textContent = `${options.currentTokens}/${maxTokens}`;
  stats.style.cssText = `
    font-size: 12px;
    color: var(--text-secondary);
    font-family: monospace;
  `;

  header.appendChild(label);
  header.appendChild(stats);

  // Progress bar
  const progressContainer = document.createElement('div');
  progressContainer.style.cssText = `
    width: 100%;
    height: 6px;
    background-color: var(--border);
    border-radius: 3px;
    overflow: hidden;
  `;

  const progressBar = document.createElement('div');
  progressBar.style.cssText = `
    height: 100%;
    background-color: ${percentage < 70 ? 'var(--green)' : percentage < 90 ? 'var(--yellow)' : 'var(--red)'};
    width: ${percentage}%;
    transition: all 0.3s ease;
  `;

  progressContainer.appendChild(progressBar);

  // Details
  const details = document.createElement('div');
  details.style.cssText = `
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--text-secondary);
  `;

  const detailLeft = document.createElement('span');
  detailLeft.textContent = `Usage: ${percentage.toFixed(1)}%`;

  const detailRight = document.createElement('span');
  detailRight.textContent = `Remaining: ${Math.max(0, maxTokens - options.currentTokens)}`;

  details.appendChild(detailLeft);
  details.appendChild(detailRight);

  // Warning message
  const warning = document.createElement('div');
  warning.style.cssText = `
    display: ${percentage > 80 ? 'flex' : 'none'};
    align-items: center;
    gap: 8px;
    padding: 8px;
    background-color: ${percentage > 90 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)'};
    border-radius: 4px;
    font-size: 12px;
    color: ${percentage > 90 ? 'var(--red)' : 'var(--yellow)'};
  `;

  const warningIcon = document.createElement('span');
  warningIcon.textContent = percentage > 90 ? '🚫' : '⚠️';

  const warningText = document.createElement('span');
  warningText.textContent = percentage > 90
    ? 'Token limit nearly reached!'
    : 'Approaching token limit';

  warning.appendChild(warningIcon);
  warning.appendChild(warningText);

  // Context tokens info
  if (options.contextTokens) {
    const contextInfo = document.createElement('div');
    contextInfo.style.cssText = `
      font-size: 11px;
      color: var(--text-secondary);
      padding-top: 4px;
      border-top: 1px solid var(--border);
    `;
    contextInfo.textContent = `Context: ${options.contextTokens} tokens`;
    container.appendChild(contextInfo);
  }

  // Expose methods
  (container as any).update = (currentTokens: number) => {
    const newPercentage = Math.min((currentTokens / maxTokens) * 100, 100);
    progressBar.style.backgroundColor =
      newPercentage < 70 ? 'var(--green)' :
      newPercentage < 90 ? 'var(--yellow)' :
      'var(--red)';
    progressBar.style.width = `${newPercentage}%`;
    stats.textContent = `${currentTokens}/${maxTokens}`;
    detailLeft.textContent = `Usage: ${newPercentage.toFixed(1)}%`;
    detailRight.textContent = `Remaining: ${Math.max(0, maxTokens - currentTokens)}`;
    warning.style.display = newPercentage > 80 ? 'flex' : 'none';
    if (newPercentage > 80) {
      warning.style.backgroundColor =
        newPercentage > 90 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)';
      warning.style.color = newPercentage > 90 ? 'var(--red)' : 'var(--yellow)';
      warningIcon.textContent = newPercentage > 90 ? '🚫' : '⚠️';
      warningText.textContent = newPercentage > 90
        ? 'Token limit nearly reached!'
        : 'Approaching token limit';
    }

    if (newPercentage > 80) {
      options.onThresholdReached?.(newPercentage);
    }
  };

  container.appendChild(header);
  container.appendChild(progressContainer);
  container.appendChild(details);
  container.appendChild(warning);

  return container;
}

export const TokenMeter = {
  create: createTokenMeter,
};
