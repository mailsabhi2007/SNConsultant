import { create } from "zustand";

interface CreditState {
  balance: number | null;
  setBalance: (balance: number) => void;
}

export const useCreditStore = create<CreditState>((set) => ({
  balance: null,
  setBalance: (balance) => set({ balance }),
}));
