import { api } from '../lib/api-client'
import type { BackendConnection, BackendConfig, BackendTestResult, BackendProvider, ApiResponse } from '@/types'

export const backendApi = {
  list: async (): Promise<ApiResponse<BackendConnection[]>> => {
    return api.get<BackendConnection[]>('/backends')
  },

  get: async (provider: BackendProvider): Promise<ApiResponse<BackendConnection>> => {
    return api.get<BackendConnection>(`/backends/${provider}`)
  },

  connect: async (config: BackendConfig): Promise<ApiResponse<BackendConnection>> => {
    return api.post<BackendConnection>('/backends/connect', config)
  },

  disconnect: async (provider: BackendProvider): Promise<ApiResponse<void>> => {
    return api.post<void>(`/backends/${provider}/disconnect`)
  },

  test: async (config: BackendConfig): Promise<ApiResponse<BackendTestResult>> => {
    return api.post<BackendTestResult>('/backends/test', config)
  },

  updateConfig: async (provider: BackendProvider, config: Partial<BackendConfig>): Promise<ApiResponse<BackendConnection>> => {
    return api.patch<BackendConnection>(`/backends/${provider}`, config)
  },

  getCollections: async (provider: BackendProvider): Promise<ApiResponse<Array<{ name: string; memoryCount: number; dimension: number }>>> => {
    return api.get(`/backends/${provider}/collections`)
  },

  createCollection: async (provider: BackendProvider, name: string, dimension: number): Promise<ApiResponse<void>> => {
    return api.post(`/backends/${provider}/collections`, { name, dimension })
  },

  deleteCollection: async (provider: BackendProvider, name: string): Promise<ApiResponse<void>> => {
    return api.delete(`/backends/${provider}/collections/${name}`)
  },

  getMetrics: async (provider: BackendProvider): Promise<ApiResponse<{
    totalMemory: number
    usedMemory: number
    vectorCount: number
    diskUsage: number
  }>> => {
    return api.get(`/backends/${provider}/metrics`)
  },
}
