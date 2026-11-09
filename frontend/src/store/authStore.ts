import { create } from 'zustand';
import type { Usuario } from '../types';

interface AuthState {
  user: Usuario | null;
  token: string | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  login: (user: Usuario, token: string) => void;
  switchSession: (user: Usuario, token: string) => void;
  setUser: (user: Usuario) => void;
  finishBootstrap: () => void;
  logout: () => void;
}

const storedToken = typeof window !== 'undefined' ? localStorage.getItem('rentio_token') : null;

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: storedToken,
  isAuthenticated: Boolean(storedToken),
  isBootstrapping: Boolean(storedToken),
  login: (user, token) => {
    localStorage.setItem('rentio_token', token);
    set({ user, token, isAuthenticated: true, isBootstrapping: false });
  },
  switchSession: (user, token) => {
    localStorage.setItem('rentio_token', token);
    set({ user, token, isAuthenticated: true, isBootstrapping: false });
  },
  setUser: (user) => set({ user }),
  finishBootstrap: () => set({ isBootstrapping: false }),
  logout: () => {
    localStorage.removeItem('rentio_token');
    set({ user: null, token: null, isAuthenticated: false, isBootstrapping: false });
  },
}));
