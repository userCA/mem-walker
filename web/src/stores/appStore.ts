import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type AppMode = 'memory' | 'chat' | 'backend'

interface AppState {
  mode: AppMode
  sidebarCollapsed: boolean
  commandPaletteOpen: boolean
  theme: 'light' | 'dark' | 'system'
  setMode: (mode: AppMode) => void
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setCommandPaletteOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      mode: 'memory',
      sidebarCollapsed: false,
      commandPaletteOpen: false,
      theme: 'light',

      setMode: (mode) => set({ mode }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        theme: state.theme,
      }),
    }
  )
)
