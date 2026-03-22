import { create } from 'zustand'
import type { ChatConfig } from '@/types'

interface ChatState {
  // Current session
  currentSessionId: string | null

  // UI state
  isConfigPanelOpen: boolean
  isPresetPanelOpen: boolean

  // Config
  config: ChatConfig

  // Presets
  activePresetId: string | null

  // Actions
  setCurrentSessionId: (id: string | null) => void
  setConfig: (config: Partial<ChatConfig>) => void
  resetConfig: () => void
  setIsConfigPanelOpen: (open: boolean) => void
  setIsPresetPanelOpen: (open: boolean) => void
  setActivePresetId: (id: string | null) => void
}

const defaultConfig: ChatConfig = {
  model: 'gpt-4',
  temperature: 0.7,
  maxTokens: 2000,
  topP: 1,
  topK: 40,
  repeatPenalty: 1.1,
  includeMemories: true,
  memoryThreshold: 0.7,
}

export const useChatStore = create<ChatState>((set) => ({
  currentSessionId: null,
  isConfigPanelOpen: false,
  isPresetPanelOpen: false,
  config: defaultConfig,
  activePresetId: null,

  setCurrentSessionId: (id) => set({ currentSessionId: id }),

  setConfig: (config) => set((state) => ({ config: { ...state.config, ...config } })),

  resetConfig: () => set({ config: defaultConfig }),

  setIsConfigPanelOpen: (open) => set({ isConfigPanelOpen: open }),

  setIsPresetPanelOpen: (open) => set({ isPresetPanelOpen: open }),

  setActivePresetId: (id) => set({ activePresetId: id }),
}))
