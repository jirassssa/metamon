import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  address: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, address: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      address: null,
      isAuthenticated: false,
      setAuth: (token: string, address: string) =>
        set({ token, address, isAuthenticated: true }),
      clearAuth: () =>
        set({ token: null, address: null, isAuthenticated: false }),
    }),
    {
      name: "auth-storage",
    }
  )
);
