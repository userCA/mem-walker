import { create } from 'zustand'
import type { MemoryFilter, MemorySort, MemoryTag } from '@/types'

interface MemoryState {
  // View state
  selectedMemoryId: string | null
  filter: MemoryFilter
  sort: MemorySort
  viewMode: 'list' | 'grid' | 'graph'

  // Selection state
  selectedIds: string[]
  selectAll: boolean

  // Tag management
  tags: MemoryTag[]
  selectedTags: string[]

  // Actions
  setSelectedMemoryId: (id: string | null) => void
  setFilter: (filter: Partial<MemoryFilter>) => void
  clearFilter: () => void
  setSort: (sort: MemorySort) => void
  setViewMode: (mode: 'list' | 'grid' | 'graph') => void
  toggleSelectId: (id: string) => void
  selectAllMemories: (ids: string[]) => void
  clearSelection: () => void
  setTags: (tags: MemoryTag[]) => void
  toggleTag: (tagId: string) => void
  clearTags: () => void
}

const defaultFilter: MemoryFilter = {}
const defaultSort: MemorySort = { field: 'updatedAt', order: 'desc' }

export const useMemoryStore = create<MemoryState>((set) => ({
  selectedMemoryId: null,
  filter: defaultFilter,
  sort: defaultSort,
  viewMode: 'list',
  selectedIds: [],
  selectAll: false,
  tags: [],
  selectedTags: [],

  setSelectedMemoryId: (id) => set({ selectedMemoryId: id }),

  setFilter: (filter) => set((state) => ({ filter: { ...state.filter, ...filter } })),

  clearFilter: () => set({ filter: defaultFilter, selectedTags: [] }),

  setSort: (sort) => set({ sort }),

  setViewMode: (mode) => set({ viewMode: mode }),

  toggleSelectId: (id) =>
    set((state) => ({
      selectedIds: state.selectedIds.includes(id)
        ? state.selectedIds.filter((i) => i !== id)
        : [...state.selectedIds, id],
    })),

  selectAllMemories: (ids) => set({ selectedIds: ids, selectAll: true }),

  clearSelection: () => set({ selectedIds: [], selectAll: false }),

  setTags: (tags) => set({ tags }),

  toggleTag: (tagId) =>
    set((state) => ({
      selectedTags: state.selectedTags.includes(tagId)
        ? state.selectedTags.filter((t) => t !== tagId)
        : [...state.selectedTags, tagId],
    })),

  clearTags: () => set({ selectedTags: [] }),
}))
