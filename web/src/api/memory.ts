import { api } from '../lib/api-client'
import type { Memory, MemoryStats, MemoryBatchAction, ApiResponse, PaginatedResponse, ApiQueryParams } from '@/types'

export const memoryApi = {
  list: async (params?: ApiQueryParams): Promise<ApiResponse<PaginatedResponse<Memory>>> => {
    return api.get<PaginatedResponse<Memory>>('/memories', { params })
  },

  get: async (id: string): Promise<ApiResponse<Memory>> => {
    return api.get<Memory>(`/memories/${id}`)
  },

  create: async (data: Partial<Memory>): Promise<ApiResponse<Memory>> => {
    return api.post<Memory>('/memories', data)
  },

  update: async (id: string, data: Partial<Memory>): Promise<ApiResponse<Memory>> => {
    return api.patch<Memory>(`/memories/${id}`, data)
  },

  delete: async (id: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/memories/${id}`)
  },

  batch: async (action: MemoryBatchAction): Promise<ApiResponse<void>> => {
    return api.post<void>('/memories/batch', action)
  },

  stats: async (): Promise<ApiResponse<MemoryStats>> => {
    return api.get<MemoryStats>('/memories/stats')
  },

  search: async (query: string, limit = 10): Promise<ApiResponse<Memory[]>> => {
    return api.get<Memory[]>('/memories/search', { params: { q: query, limit } })
  },

  getTags: async (): Promise<ApiResponse<Array<{ id: string; name: string; color?: string; count: number }>>> => {
    return api.get('/memories/tags')
  },

  getLayers: async (): Promise<ApiResponse<Array<{ layer: string; count: number; percentage: number }>>> => {
    return api.get('/memories/layers')
  },

  export: async (format: 'json' | 'csv' = 'json'): Promise<ApiResponse<{ url: string }>> => {
    return api.post('/memories/export', { format })
  },

  import: async (file: File): Promise<ApiResponse<{ imported: number; failed: number }>> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/memories/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
