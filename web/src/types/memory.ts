// Memory Types
export type MemoryStatus = 'active' | 'archived' | 'frozen' | 'deleted'

export type MemoryPriority = 'low' | 'medium' | 'high' | 'urgent'

export type MemoryImportance = 1 | 2 | 3 | 4 | 5

export interface MemoryTag {
  id: string
  name: string
  color?: string
  count?: number
}

export interface MemoryAccess {
  lastAccessedAt: string
  accessCount: number
  lastModifiedAt: string
}

export interface MemoryReference {
  id: string
  title: string
  snippet?: string
  similarity?: number
}

export interface Memory {
  id: string
  content: string
  title: string
  status: MemoryStatus
  priority: MemoryPriority
  importance: MemoryImportance
  tags: MemoryTag[]
  layer?: 'semantic' | 'episodic' | 'procedural' | 'working'
  access: MemoryAccess
  references?: MemoryReference[]
  createdAt: string
  updatedAt: string
}

export interface MemoryFilter {
  status?: MemoryStatus | MemoryStatus[]
  priority?: MemoryPriority | MemoryPriority[]
  importance?: MemoryImportance[]
  tags?: string[]
  layer?: ('semantic' | 'episodic' | 'procedural' | 'working')[]
  search?: string
  dateRange?: {
    start: string
    end: string
  }
}

export interface MemorySort {
  field: 'createdAt' | 'updatedAt' | 'importance' | 'accessCount'
  order: 'asc' | 'desc'
}

export interface MemoryStats {
  total: number
  byStatus: Record<MemoryStatus, number>
  byPriority: Record<MemoryPriority, number>
  byLayer: Record<string, number>
  averageImportance: number
}

export interface MemoryBatchAction {
  type: 'archive' | 'freeze' | 'delete' | 'tag' | 'changePriority'
  ids: string[]
  payload?: Partial<Memory>
}

export interface MemoryLayerMapping {
  layer: 'semantic' | 'episodic' | 'procedural' | 'working'
  count: number
  percentage: number
  color: string
}
