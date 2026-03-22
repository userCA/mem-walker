import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { memoryApi } from '@/api'
import type { Memory, MemoryBatchAction, ApiQueryParams } from '@/types'
import toast from 'react-hot-toast'

// Query Keys
export const memoryKeys = {
  all: ['memories'] as const,
  lists: () => [...memoryKeys.all, 'list'] as const,
  list: (params?: ApiQueryParams) => [...memoryKeys.lists(), params] as const,
  stats: () => [...memoryKeys.all, 'stats'] as const,
  tags: () => [...memoryKeys.all, 'tags'] as const,
  layers: () => [...memoryKeys.all, 'layers'] as const,
  details: () => [...memoryKeys.all, 'detail'] as const,
  detail: (id: string) => [...memoryKeys.details(), id] as const,
  search: (query: string) => [...memoryKeys.all, 'search', query] as const,
}

// Hooks
export function useMemories(params?: ApiQueryParams) {
  return useQuery({
    queryKey: memoryKeys.list(params),
    queryFn: () => memoryApi.list(params).then((res) => res.data!),
  })
}

export function useMemory(id: string) {
  return useQuery({
    queryKey: memoryKeys.detail(id),
    queryFn: () => memoryApi.get(id).then((res) => res.data!),
    enabled: !!id,
  })
}

export function useMemoryStats() {
  return useQuery({
    queryKey: memoryKeys.stats(),
    queryFn: () => memoryApi.stats().then((res) => res.data!),
  })
}

export function useMemoryTags() {
  return useQuery({
    queryKey: memoryKeys.tags(),
    queryFn: () => memoryApi.getTags().then((res) => res.data!),
  })
}

export function useMemoryLayers() {
  return useQuery({
    queryKey: memoryKeys.layers(),
    queryFn: () => memoryApi.getLayers().then((res) => res.data!),
  })
}

export function useMemorySearch(query: string, limit = 10) {
  return useQuery({
    queryKey: memoryKeys.search(query),
    queryFn: () => memoryApi.search(query, limit).then((res) => res.data!),
    enabled: query.length > 0,
  })
}

export function useCreateMemory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<Memory>) => memoryApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: memoryKeys.stats() })
      toast.success('Memory created')
    },
    onError: () => {
      toast.error('Failed to create memory')
    },
  })
}

export function useUpdateMemory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Memory> }) => memoryApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: memoryKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: memoryKeys.stats() })
      toast.success('Memory updated')
    },
    onError: () => {
      toast.error('Failed to update memory')
    },
  })
}

export function useDeleteMemory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => memoryApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: memoryKeys.stats() })
      toast.success('Memory deleted')
    },
    onError: () => {
      toast.error('Failed to delete memory')
    },
  })
}

export function useBatchMemoryAction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (action: MemoryBatchAction) => memoryApi.batch(action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: memoryKeys.lists() })
      queryClient.invalidateQueries({ queryKey: memoryKeys.stats() })
      toast.success('Batch action completed')
    },
    onError: () => {
      toast.error('Failed to execute batch action')
    },
  })
}
