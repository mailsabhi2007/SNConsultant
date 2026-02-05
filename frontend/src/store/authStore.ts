import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  user_id: string;
  username: string;
  email?: string | null;
  is_admin: boolean;
  is_superadmin?: boolean;
}

interface AuthState {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
    }),
    {
      name: "auth-storage",
    }
  )
);
