import { create } from "zustand"

interface AuthModalState {
  isOpen: boolean
  mode: "login" | "register"
  openAuth: (mode?: "login" | "register") => void
  closeAuth: () => void
}

export const useAuthModalStore = create<AuthModalState>((set) => ({
  isOpen: false,
  mode: "login",
  openAuth: (mode = "login") => set({ isOpen: true, mode }),
  closeAuth: () => set({ isOpen: false }),
}))
