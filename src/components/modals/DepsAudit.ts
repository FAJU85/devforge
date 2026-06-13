/**
 * DepsAudit component - dependency vulnerability audit display
 */

export interface Vulnerability {
  id: string;
  package: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  fixedVersion?: string;
  affectedVersions: string;
}

export interface DepsAuditOptions {
  vulnerabilities: Vulnerability[];
  onFix?: (id: string) => void;
  onClose?: () => void;
  scanTime?: Date;
}

export function createDepsAudit(options: DepsAuditOptions): HTMLDivElement {
  const modal = document.createElement('div');
  modal.className = 'deps-audit-modal';

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

  const audit = document.createElement('div');
  audit.style.cssText = `
    background-color: var(--panel);
    border-radius: 8px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    width: 100%;
    max-width: 800px;
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
  title.textContent = '🔍 Dependency Audit';
  title.style.cssText = `
    margin: 0 0 12px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text);
  `;

  const stats = document.createElement('div');
  stats.style.cssText = `
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  `;

  const severities = {
    critical: options.vulnerabilities.filter((v) => v.severity === 'critical').length,
    high: options.vulnerabilities.filter((v) => v.severity === 'high').length,
    medium: options.vulnerabilities.filter((v) => v.severity === 'medium').length,
    low: options.vulnerabilities.filter((v) => v.severity === 'low').length,
  };

  const severityColors: { [key: string]: string } = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#f59e0b',
    low: '#eab308',
  };

  Object.entries(severities).forEach(([level, count]) => {
    if (count > 0) {
      const stat = document.createElement('div');
      stat.style.cssText = `
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
      `;

      const badge = document.createElement('span');
      badge.textContent = count.toString();
      badge.style.cssText = `
        padding: 2px 6px;
        background-color: ${severityColors[level]};
        color: white;
        border-radius: 3px;
        font-weight: 600;
      `;

      const label = document.createElement('span');
      label.textContent = level.charAt(0).toUpperCase() + level.slice(1);
      label.style.cssText = `
        color: var(--text-secondary);
        text-transform: capitalize;
      `;

      stat.appendChild(badge);
      stat.appendChild(label);
      stats.appendChild(stat);
    }
  });

  if (options.scanTime) {
    const time = document.createElement('div');
    time.style.cssText = `
      margin-left: auto;
      font-size: 11px;
      color: var(--text-secondary);
    `;
    time.textContent = `Scanned: ${options.scanTime.toLocaleString()}`;
    stats.appendChild(time);
  }

  header.appendChild(title);
  header.appendChild(stats);

  // Vulnerabilities list
  const list = document.createElement('div');
  list.className = 'audit-vulnerabilities-list';
  list.style.cssText = `
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  `;

  options.vulnerabilities.forEach((vuln) => {
    const item = document.createElement('div');
    item.style.cssText = `
      padding: 12px;
      background-color: var(--bg);
      border: 1px solid var(--border);
      border-left: 3px solid ${severityColors[vuln.severity]};
      border-radius: 4px;
    `;

    // Vulnerability header
    const vulnHeader = document.createElement('div');
    vulnHeader.style.cssText = `
      display: flex;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 8px;
    `;

    const severity = document.createElement('span');
    severity.textContent = vuln.severity.toUpperCase();
    severity.style.cssText = `
      padding: 2px 6px;
      background-color: ${severityColors[vuln.severity]};
      color: white;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 600;
      flex-shrink: 0;
    `;

    const package_info = document.createElement('div');
    package_info.style.cssText = `
      flex: 1;
    `;

    const package_name = document.createElement('div');
    package_name.textContent = vuln.package;
    package_name.style.cssText = `
      font-weight: 600;
      font-size: 13px;
      color: var(--text);
    `;

    const package_versions = document.createElement('div');
    package_versions.textContent = `Affected: ${vuln.affectedVersions}`;
    package_versions.style.cssText = `
      font-size: 11px;
      color: var(--text-secondary);
      margin-top: 2px;
    `;

    package_info.appendChild(package_name);
    package_info.appendChild(package_versions);

    vulnHeader.appendChild(severity);
    vulnHeader.appendChild(package_info);

    // Title
    const vulnTitle = document.createElement('div');
    vulnTitle.textContent = vuln.title;
    vulnTitle.style.cssText = `
      font-size: 12px;
      font-weight: 500;
      color: var(--text);
      margin-bottom: 6px;
    `;

    // Description
    const description = document.createElement('div');
    description.textContent = vuln.description;
    description.style.cssText = `
      font-size: 11px;
      color: var(--text-secondary);
      line-height: 1.4;
      margin-bottom: 8px;
    `;

    // Footer with fix button
    const footer = document.createElement('div');
    footer.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
    `;

    if (vuln.fixedVersion) {
      const fixed = document.createElement('span');
      fixed.textContent = `✓ Available: ${vuln.fixedVersion}`;
      fixed.style.cssText = `
        font-size: 10px;
        color: var(--green);
        font-weight: 500;
      `;
      footer.appendChild(fixed);
    }

    if (options.onFix) {
      const fixBtn = document.createElement('button');
      fixBtn.textContent = '🔧 Fix';
      fixBtn.style.cssText = `
        padding: 4px 10px;
        border: 1px solid var(--accent);
        border-radius: 3px;
        background-color: transparent;
        color: var(--accent);
        cursor: pointer;
        font-size: 10px;
        font-weight: 500;
        transition: all 0.2s;
        font-family: inherit;
      `;

      fixBtn.addEventListener('mouseover', () => {
        fixBtn.style.backgroundColor = 'var(--accent)';
        fixBtn.style.color = 'var(--bg)';
      });

      fixBtn.addEventListener('mouseout', () => {
        fixBtn.style.backgroundColor = 'transparent';
        fixBtn.style.color = 'var(--accent)';
      });

      fixBtn.addEventListener('click', () => {
        options.onFix?.(vuln.id);
      });

      footer.appendChild(fixBtn);
    }

    item.appendChild(vulnHeader);
    item.appendChild(vulnTitle);
    item.appendChild(description);
    item.appendChild(footer);

    list.appendChild(item);
  });

  if (options.vulnerabilities.length === 0) {
    const empty = document.createElement('div');
    empty.style.cssText = `
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      flex-direction: column;
      gap: 8px;
      color: var(--text-secondary);
    `;

    const icon = document.createElement('div');
    icon.textContent = '✓';
    icon.style.cssText = `
      font-size: 32px;
      color: var(--green);
    `;

    const text = document.createElement('div');
    text.textContent = 'No vulnerabilities found';

    empty.appendChild(icon);
    empty.appendChild(text);
    list.appendChild(empty);
  }

  // Footer
  const footer = document.createElement('div');
  footer.style.cssText = `
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    background-color: var(--panel);
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
    audit.style.animation = 'fadeOut 0.2s ease-in';
    setTimeout(() => {
      modal.remove();
      options.onClose?.();
    }, 200);
  });

  footer.appendChild(closeBtn);

  audit.appendChild(header);
  audit.appendChild(list);
  audit.appendChild(footer);
  modal.appendChild(audit);

  return modal;
}

export const DepsAudit = {
  create: createDepsAudit,
};
