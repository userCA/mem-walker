// Backend Types
export type BackendProvider = 'milvus' | 'sqlite' | 'chroma' | 'qdrant' | 'weaviate'

export type BackendStatus = 'connected' | 'disconnected' | 'error' | 'connecting'

export interface CollectionStats {
  name: string
  memoryCount: number
  vectorDimension: number
  indexType: string
  createdAt: string
}

export interface StorageMetrics {
  totalMemory: number
  usedMemory: number
  vectorCount: number
  indexSize: number
  diskUsage: number
  connectionPoolSize: number
  activeConnections: number
}

export interface BackendHealth {
  status: BackendStatus
  latency: number
  lastChecked: string
  error?: string
}

export interface BackendConnection {
  provider: BackendProvider
  status: BackendStatus
  host: string
  port: number
  database: string
  health: BackendHealth
  metrics?: StorageMetrics
  collections?: CollectionStats[]
}

export interface BackendConfig {
  provider: BackendProvider
  host: string
  port: number
  database: string
  username?: string
  password?: string
  ssl?: boolean
  timeout?: number
  vectorDimension?: number
  batchSize?: number
}

export interface BackendTestResult {
  success: boolean
  latency?: number
  error?: string
  collections?: string[]
}
