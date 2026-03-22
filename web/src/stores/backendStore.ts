import { create } from 'zustand'
import type { BackendProvider, BackendConfig } from '@/types'

interface BackendState {
  // Selected provider
  selectedProvider: BackendProvider | null

  // Connection modal
  isConnectModalOpen: boolean
  isConfigModalOpen: boolean
  editingConfig: BackendConfig | null

  // Test connection
  testResult: { success: boolean; latency?: number; error?: string } | null
  isTesting: boolean

  // Actions
  setSelectedProvider: (provider: BackendProvider | null) => void
  setIsConnectModalOpen: (open: boolean) => void
  setIsConfigModalOpen: (open: boolean) => void
  setEditingConfig: (config: BackendConfig | null) => void
  setTestResult: (result: { success: boolean; latency?: number; error?: string } | null) => void
  setIsTesting: (testing: boolean) => void
}

export const useBackendStore = create<BackendState>((set) => ({
  selectedProvider: null,
  isConnectModalOpen: false,
  isConfigModalOpen: false,
  editingConfig: null,
  testResult: null,
  isTesting: false,

  setSelectedProvider: (provider) => set({ selectedProvider: provider }),

  setIsConnectModalOpen: (open) => set({ isConnectModalOpen: open }),

  setIsConfigModalOpen: (open) => set({ isConfigModalOpen: open }),

  setEditingConfig: (config) => set({ editingConfig: config }),

  setTestResult: (result) => set({ testResult: result }),

  setIsTesting: (testing) => set({ isTesting: testing }),
}))
