import { describe, it, expect, beforeEach } from 'vitest';
import { create } from 'zustand';

describe('State Management Integration', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('should create a zustand store', () => {
    interface TestStore {
      count: number;
      increment: () => void;
      decrement: () => void;
    }

    const useTestStore = create<TestStore>((set) => ({
      count: 0,
      increment: () => set((state) => ({ count: state.count + 1 })),
      decrement: () => set((state) => ({ count: state.count - 1 })),
    }));

    const { count, increment, decrement } = useTestStore.getState();

    expect(count).toBe(0);
    increment();
    expect(useTestStore.getState().count).toBe(1);
    decrement();
    expect(useTestStore.getState().count).toBe(0);
  });

  it('should handle multiple concurrent state updates', () => {
    interface CounterStore {
      count: number;
      increment: () => void;
      decrement: () => void;
    }

    const useCounterStore = create<CounterStore>((set) => ({
      count: 0,
      increment: () => set((state) => ({ count: state.count + 1 })),
      decrement: () => set((state) => ({ count: state.count - 1 })),
    }));

    const { increment, decrement } = useCounterStore.getState();

    increment();
    increment();
    decrement();

    expect(useCounterStore.getState().count).toBe(1);

    increment();
    increment();

    expect(useCounterStore.getState().count).toBe(3);
  });

  it('should persist state changes across store updates', () => {
    interface AppStore {
      user: string | null;
      setUser: (name: string) => void;
      clearUser: () => void;
    }

    const useAppStore = create<AppStore>((set) => ({
      user: null,
      setUser: (name) => set({ user: name }),
      clearUser: () => set({ user: null }),
    }));

    expect(useAppStore.getState().user).toBeNull();

    useAppStore.getState().setUser('Alice');
    expect(useAppStore.getState().user).toBe('Alice');

    useAppStore.getState().setUser('Bob');
    expect(useAppStore.getState().user).toBe('Bob');

    useAppStore.getState().clearUser();
    expect(useAppStore.getState().user).toBeNull();
  });

  it('should handle complex state updates', () => {
    interface ComplexStore {
      items: string[];
      filters: { active: boolean; category: string };
      addItem: (item: string) => void;
      setFilter: (key: string, value: unknown) => void;
    }

    const useComplexStore = create<ComplexStore>((set) => ({
      items: [],
      filters: { active: true, category: 'all' },
      addItem: (item) =>
        set((state) => ({ items: [...state.items, item] })),
      setFilter: (key, value) =>
        set((state) => ({
          filters: { ...state.filters, [key]: value },
        })),
    }));

    useComplexStore.getState().addItem('Item 1');
    useComplexStore.getState().addItem('Item 2');
    expect(useComplexStore.getState().items).toHaveLength(2);

    useComplexStore.getState().setFilter('category', 'completed');
    expect(useComplexStore.getState().filters.category).toBe('completed');
    expect(useComplexStore.getState().filters.active).toBe(true);
  });

  it('should handle concurrent state updates', () => {
    interface ConcurrentStore {
      value: number;
      increment: () => void;
    }

    const useConcurrentStore = create<ConcurrentStore>((set) => ({
      value: 0,
      increment: () => set((state) => ({ value: state.value + 1 })),
    }));

    const { increment } = useConcurrentStore.getState();

    increment();
    increment();
    increment();

    expect(useConcurrentStore.getState().value).toBe(3);
  });
});
