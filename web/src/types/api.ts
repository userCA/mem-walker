// API Types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: ApiError
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface ApiQueryParams {
  page?: number
  pageSize?: number
  sort?: string
  order?: 'asc' | 'desc'
  filter?: Record<string, unknown>
  search?: string
}

export interface ApiMutationParams<T = unknown> {
  data: T
}

// Memory API
export interface MemoryApiEndpoints {
  list: (params?: ApiQueryParams) => Promise<ApiResponse<PaginatedResponse<import('./memory').Memory>>>
  get: (id: string) => Promise<ApiResponse<import('./memory').Memory>>
  create: (data: Partial<import('./memory').Memory>) => Promise<ApiResponse<import('./memory').Memory>>
  update: (id: string, data: Partial<import('./memory').Memory>) => Promise<ApiResponse<import('./memory').Memory>>
  delete: (id: string) => Promise<ApiResponse<void>>
  batch: (action: import('./memory').MemoryBatchAction) => Promise<ApiResponse<void>>
  stats: () => Promise<ApiResponse<import('./memory').MemoryStats>>
  search: (query: string, limit?: number) => Promise<ApiResponse<import('./memory').Memory[]>>
}

// Backend API
export interface BackendApiEndpoints {
  list: () => Promise<ApiResponse<import('./backend').BackendConnection[]>>
  get: (provider: import('./backend').BackendProvider) => Promise<ApiResponse<import('./backend').BackendConnection>>
  connect: (config: import('./backend').BackendConfig) => Promise<ApiResponse<import('./backend').BackendConnection>>
  disconnect: (provider: import('./backend').BackendProvider) => Promise<ApiResponse<void>>
  test: (config: import('./backend').BackendConfig) => Promise<ApiResponse<import('./backend').BackendTestResult>>
  updateConfig: (provider: import('./backend').BackendProvider, config: Partial<import('./backend').BackendConfig>) => Promise<ApiResponse<import('./backend').BackendConnection>>
}

// Chat API
export interface ChatApiEndpoints {
  listSessions: (params?: ApiQueryParams) => Promise<ApiResponse<PaginatedResponse<import('./chat').ChatSession>>>
  getSession: (id: string) => Promise<ApiResponse<import('./chat').ChatSession>>
  createSession: (data?: Partial<import('./chat').ChatSession>) => Promise<ApiResponse<import('./chat').ChatSession>>
  updateSession: (id: string, data: Partial<import('./chat').ChatSession>) => Promise<ApiResponse<import('./chat').ChatSession>>
  deleteSession: (id: string) => Promise<ApiResponse<void>>
  sendMessage: (sessionId: string, content: string, config?: Partial<import('./chat').ChatConfig>) => Promise<ApiResponse<import('./chat').ChatMessage>>
  getConfig: () => Promise<ApiResponse<import('./chat').ChatConfig>>
  updateConfig: (config: Partial<import('./chat').ChatConfig>) => Promise<ApiResponse<import('./chat').ChatConfig>>
}
