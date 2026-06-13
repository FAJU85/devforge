import { describe, it, expect, beforeEach, vi } from 'vitest';

class InputBox {
  private value: string = '';
  private placeholder: string = '';
  private disabled: boolean = false;
  private onSubmit: ((value: string) => void) | null = null;
  private onChange: ((value: string) => void) | null = null;

  constructor(placeholder?: string) {
    this.placeholder = placeholder || '';
  }

  setValue(value: string): void {
    this.value = value;
    this.onChange?.(value);
  }

  getValue(): string {
    return this.value;
  }

  clear(): void {
    this.setValue('');
  }

  setPlaceholder(placeholder: string): void {
    this.placeholder = placeholder;
  }

  getPlaceholder(): string {
    return this.placeholder;
  }

  setDisabled(disabled: boolean): void {
    this.disabled = disabled;
  }

  isDisabled(): boolean {
    return this.disabled;
  }

  submit(): void {
    if (this.value.trim()) {
      this.onSubmit?.(this.value);
      this.clear();
    }
  }

  onValueChange(callback: (value: string) => void): void {
    this.onChange = callback;
  }

  onSubmitted(callback: (value: string) => void): void {
    this.onSubmit = callback;
  }

  focus(): void {
    // Focus implementation
  }

  blur(): void {
    // Blur implementation
  }
}

describe('InputBox', () => {
  let inputBox: InputBox;

  beforeEach(() => {
    inputBox = new InputBox('Enter message...');
  });

  it('should create with placeholder', () => {
    expect(inputBox.getPlaceholder()).toBe('Enter message...');
  });

  it('should set and get value', () => {
    inputBox.setValue('Test message');
    expect(inputBox.getValue()).toBe('Test message');
  });

  it('should clear value', () => {
    inputBox.setValue('Test message');
    inputBox.clear();
    expect(inputBox.getValue()).toBe('');
  });

  it('should update placeholder', () => {
    inputBox.setPlaceholder('New placeholder');
    expect(inputBox.getPlaceholder()).toBe('New placeholder');
  });

  it('should handle disabled state', () => {
    expect(inputBox.isDisabled()).toBe(false);
    inputBox.setDisabled(true);
    expect(inputBox.isDisabled()).toBe(true);
  });

  it('should call onChange callback', () => {
    const onChange = vi.fn();
    inputBox.onValueChange(onChange);
    inputBox.setValue('New value');
    expect(onChange).toHaveBeenCalledWith('New value');
  });

  it('should submit value', () => {
    const onSubmit = vi.fn();
    inputBox.onSubmitted(onSubmit);
    inputBox.setValue('Submit this');
    inputBox.submit();
    expect(onSubmit).toHaveBeenCalledWith('Submit this');
  });

  it('should clear after submit', () => {
    const onSubmit = vi.fn();
    inputBox.onSubmitted(onSubmit);
    inputBox.setValue('Message');
    inputBox.submit();
    expect(inputBox.getValue()).toBe('');
  });

  it('should not submit empty value', () => {
    const onSubmit = vi.fn();
    inputBox.onSubmitted(onSubmit);
    inputBox.setValue('   ');
    inputBox.submit();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('should handle multiple value changes', () => {
    const onChange = vi.fn();
    inputBox.onValueChange(onChange);
    inputBox.setValue('First');
    inputBox.setValue('Second');
    inputBox.setValue('Third');
    expect(onChange).toHaveBeenCalledTimes(3);
  });

  it('should maintain value when disabled', () => {
    inputBox.setValue('Test');
    inputBox.setDisabled(true);
    expect(inputBox.getValue()).toBe('Test');
  });

  it('should focus input', () => {
    expect(() => inputBox.focus()).not.toThrow();
  });

  it('should blur input', () => {
    expect(() => inputBox.blur()).not.toThrow();
  });
});
