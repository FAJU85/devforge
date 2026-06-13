import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: number;
  login: string;
  name: string;
  email: string;
  avatar_url: string;
}

export interface AuthState {
  user: User | null;
  sessionToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setUser: (user: User | null) => void;
  setSessionToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  login: (user: User, token: string) => void;
  logout: () => void;
  checkAuthStatus: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      sessionToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setUser: (user) => set({ user }),

      setSessionToken: (token) => set({ sessionToken: token }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      login: (user, token) => {
        set({
          user,
          sessionToken: token,
          isAuthenticated: true,
          error: null,
        });
        // Store token in sessionStorage (cleared on browser close)
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('session_token', token);
        }
      },

      logout: () => {
        set({
          user: null,
          sessionToken: null,
          isAuthenticated: false,
          error: null,
        });
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('session_token');
        }
      },

      checkAuthStatus: async () => {
        set({ isLoading: true });
        try {
          const response = await fetch('/api/auth/user', {
            credentials: 'include',
          });

          if (response.ok) {
            const user = await response.json();
            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            set({
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          }
        } catch (error) {
          set({
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Authentication check failed',
          });
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
