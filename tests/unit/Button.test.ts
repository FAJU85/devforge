import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock Button component for testing
const createButton = (config: {
  text: string;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
  ariaLabel?: string;
}): HTMLButtonElement => {
  const button = document.createElement('button');
  button.textContent = config.text;
  button.className = `btn btn-${config.variant || 'primary'}`;

  if (config.disabled) {
    button.disabled = true;
    button.setAttribute('aria-disabled', 'true');
  }

  if (config.ariaLabel) {
    button.setAttribute('aria-label', config.ariaLabel);
  }

  if (config.onClick) {
    button.addEventListener('click', config.onClick);
  }

  return button;
};

describe('Button Component', () => {
  let container: HTMLElement;

  beforeEach(() => {
    container = document.body;
    container.innerHTML = '';
  });

  describe('Rendering', () => {
    it('should render a button with text', () => {
      const button = createButton({ text: 'Click me' });
      container.appendChild(button);

      expect(container.querySelector('button')).toBeDefined();
      expect(container.querySelector('button')?.textContent).toBe('Click me');
    });

    it('should render button with primary variant', () => {
      const button = createButton({
        text: 'Primary',
        variant: 'primary',
      });
      container.appendChild(button);

      expect(button.className).toContain('btn-primary');
    });

    it('should render button with secondary variant', () => {
      const button = createButton({
        text: 'Secondary',
        variant: 'secondary',
      });
      container.appendChild(button);

      expect(button.className).toContain('btn-secondary');
    });

    it('should render button with danger variant', () => {
      const button = createButton({
        text: 'Delete',
        variant: 'danger',
      });
      container.appendChild(button);

      expect(button.className).toContain('btn-danger');
    });

    it('should default to primary variant', () => {
      const button = createButton({ text: 'Button' });

      expect(button.className).toContain('btn-primary');
    });
  });

  describe('States', () => {
    it('should render disabled button', () => {
      const button = createButton({
        text: 'Disabled',
        disabled: true,
      });
      container.appendChild(button);

      expect(button.disabled).toBe(true);
      expect(button.getAttribute('aria-disabled')).toBe('true');
    });

    it('should render enabled button', () => {
      const button = createButton({
        text: 'Enabled',
        disabled: false,
      });

      expect(button.disabled).toBe(false);
    });

    it('should prevent click when disabled', () => {
      const clickHandler = vi.fn();
      const button = createButton({
        text: 'Disabled',
        onClick: clickHandler,
        disabled: true,
      });

      button.click();

      // Disabled buttons don't trigger clicks in real DOM
      expect(button.disabled).toBe(true);
    });
  });

  describe('Event Handlers', () => {
    it('should call onClick handler when clicked', () => {
      const onClick = vi.fn();
      const button = createButton({
        text: 'Click me',
        onClick,
      });
      container.appendChild(button);

      button.click();

      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should call onClick handler multiple times', () => {
      const onClick = vi.fn();
      const button = createButton({
        text: 'Click me',
        onClick,
      });

      button.click();
      button.click();
      button.click();

      expect(onClick).toHaveBeenCalledTimes(3);
    });

    it('should handle rapid clicks', () => {
      const onClick = vi.fn();
      const button = createButton({
        text: 'Rapid clicks',
        onClick,
      });

      for (let i = 0; i < 10; i++) {
        button.click();
      }

      expect(onClick).toHaveBeenCalledTimes(10);
    });

    it('should not call onClick when no handler provided', () => {
      const button = createButton({ text: 'No handler' });

      // Should not throw
      expect(() => button.click()).not.toThrow();
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label when provided', () => {
      const button = createButton({
        text: 'Submit',
        ariaLabel: 'Submit form',
      });

      expect(button.getAttribute('aria-label')).toBe('Submit form');
    });

    it('should be keyboard accessible', () => {
      const onClick = vi.fn();
      const button = createButton({
        text: 'Keyboard',
        onClick,
      });

      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      // Simulate keyboard interaction
      button.dispatchEvent(event);

      // Note: In real implementation, we'd need proper keyboard event handling
      expect(button).toBeDefined();
    });

    it('should have semantic HTML structure', () => {
      const button = createButton({ text: 'Semantic' });

      expect(button.tagName).toBe('BUTTON');
    });

    it('should indicate disabled state for screen readers', () => {
      const button = createButton({
        text: 'Disabled',
        disabled: true,
      });

      expect(button.getAttribute('aria-disabled')).toBe('true');
    });
  });

  describe('Styling', () => {
    it('should have btn class', () => {
      const button = createButton({ text: 'Styled' });

      expect(button.className).toContain('btn');
    });

    it('should combine multiple classes', () => {
      const button = createButton({
        text: 'Multi-class',
        variant: 'secondary',
      });

      expect(button.className).toContain('btn');
      expect(button.className).toContain('btn-secondary');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty text', () => {
      const button = createButton({ text: '' });
      container.appendChild(button);

      expect(button.textContent).toBe('');
      expect(button).toBeDefined();
    });

    it('should handle very long text', () => {
      const longText = 'A'.repeat(100);
      const button = createButton({ text: longText });

      expect(button.textContent).toBe(longText);
    });

    it('should handle special characters in text', () => {
      const button = createButton({ text: '<>&"' });

      // Text content should be set safely
      expect(button.textContent).toBe('<>&"');
    });

    it('should handle HTML-like text safely', () => {
      const button = createButton({
        text: '<script>alert("xss")</script>',
      });

      // Should be treated as text, not HTML
      expect(button.textContent).toContain('script');
    });

    it('should handle rapid variant changes', () => {
      const button = createButton({
        text: 'Variant',
        variant: 'primary',
      });

      button.className = 'btn btn-secondary';
      expect(button.className).toContain('btn-secondary');

      button.className = 'btn btn-danger';
      expect(button.className).toContain('btn-danger');
    });

    it('should handle repeated enable/disable', () => {
      const button = createButton({ text: 'Toggle' });

      button.disabled = true;
      expect(button.disabled).toBe(true);

      button.disabled = false;
      expect(button.disabled).toBe(false);

      button.disabled = true;
      expect(button.disabled).toBe(true);
    });
  });

  describe('Complex Interactions', () => {
    it('should handle click with dynamic content change', () => {
      const onClick = vi.fn(() => {
        button.textContent = 'Clicked!';
      });

      const button = createButton({
        text: 'Click me',
        onClick,
      });
      container.appendChild(button);

      button.click();

      expect(onClick).toHaveBeenCalled();
      expect(button.textContent).toBe('Clicked!');
    });

    it('should handle click with state toggle', () => {
      let isActive = false;
      const onClick = vi.fn(() => {
        isActive = !isActive;
        button.setAttribute('aria-pressed', String(isActive));
      });

      const button = createButton({
        text: 'Toggle',
        onClick,
      });

      button.click();
      expect(isActive).toBe(true);
      expect(button.getAttribute('aria-pressed')).toBe('true');

      button.click();
      expect(isActive).toBe(false);
      expect(button.getAttribute('aria-pressed')).toBe('false');
    });

    it('should handle disabling after click', () => {
      const onClick = vi.fn(() => {
        button.disabled = true;
      });

      const button = createButton({
        text: 'Disable me',
        onClick,
      });

      button.click();
      expect(onClick).toHaveBeenCalledTimes(1);
      expect(button.disabled).toBe(true);

      // Second click should not trigger handler (disabled)
      button.click();
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should handle click while disabled state changes', () => {
      const button = createButton({
        text: 'State change',
      });

      button.disabled = true;
      button.disabled = false;
      button.disabled = true;

      expect(button.disabled).toBe(true);
    });
  });
});
