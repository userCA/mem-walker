import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { backendApi } from '@/api'
import type { BackendConfig, BackendProvider } from '@/types'
import toast from 'react-hot-toast'

// Query Keys
export const backendKeys = {
  all: ['backends'] as const,
  lists: () => [...backendKeys.all, 'list'] as const,
  list: () => [...backendKeys.lists()] as const,
  details: () => [...backendKeys.all, 'detail'] as const,
  detail: (provider: BackendProvider) => [...backendKeys.details(), provider] as const,
  metrics: (provider: BackendProvider) => [...backendKeys.detail(provider), 'metrics'] as const,
  collections: (provider: BackendProvider) => [...backendKeys.detail(provider), 'collections'] as const,
}

// Hooks
export function useBackends() {
  return useQuery({
    queryKey: backendKeys.list(),
    queryFn: () => backendApi.list().then((res) => res.data!),
  })
}

export function useBackend(provider: BackendProvider) {
  return useQuery({
    queryKey: backendKeys.detail(provider),
    queryFn: () => backendApi.get(provider).then((res) => res.data!),
    enabled: !!provider,
  })
}

export function useBackendMetrics(provider: BackendProvider) {
  return useQuery({
    queryKey: backendKeys.metrics(provider),
    queryFn: () => backendApi.getMetrics(provider).then((res) => res.data!),
    enabled: !!provider,
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

export function useBackendCollections(provider: BackendProvider) {
  return useQuery({
    queryKey: backendKeys.collections(provider),
    queryFn: () => backendApi.getCollections(provider).then((res) => res.data!),
    enabled: !!provider,
  })
}

export function useConnectBackend() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (config: BackendConfig) => backendApi.connect(config),
    onSuccess: (_, config) => {
      queryClient.invalidateQueries({ queryKey: backendKeys.lists() })
      queryClient.invalidateQueries({ queryKey: backendKeys.detail(config.provider) })
      toast.success(`Connected to ${config.provider}`)
    },
    onError: (error: { message?: string }) => {
      toast.error(error.message || 'Failed to connect')
    },
  })
}

export function useDisconnectBackend() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (provider: BackendProvider) => backendApi.disconnect(provider),
    onSuccess: (_, provider) => {
      queryClient.invalidateQueries({ queryKey: backendKeys.lists() })
      queryClient.invalidateQueries({ queryKey: backendKeys.detail(provider) })
      toast.success(`Disconnected from ${provider}`)
    },
    onError: (error: { message?: string }) => {
      toast.error(error.message || 'Failed to disconnect')
    },
  })
}

export function useTestBackend() {
  return useMutation({
    mutationFn: (config: BackendConfig) => backendApi.test(config),
  })
}

export function useUpdateBackendConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ provider, config }: { provider: BackendProvider; config: Partial<BackendConfig> }) =>
      backendApi.updateConfig(provider, config),
    onSuccess: (_, { provider }) => {
      queryClient.invalidateQueries({ queryKey: backendKeys.detail(provider) })
      toast.success('Configuration updated')
    },
    onError: (error: { message?: string }) => {
      toast.error(error.message || 'Failed to update configuration')
    },
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ provider, name, dimension }: { provider: BackendProvider; name: string; dimension: number }) =>
      backendApi.createCollection(provider, name, dimension),
    onSuccess: (_, { provider }) => {
      queryClient.invalidateQueries({ queryKey: backendKeys.collections(provider) })
      toast.success('Collection created')
    },
    onError: (error: { message?: string }) => {
      toast.error(error.message || 'Failed to create collection')
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ provider, name }: { provider: BackendProvider; name: string }) =>
      backendApi.deleteCollection(provider, name),
    onSuccess: (_, { provider }) => {
      queryClient.invalidateQueries({ queryKey: backendKeys.collections(provider) })
      toast.success('Collection deleted')
    },
    onError: (error: { message?: string }) => {
      toast.error(error.message || 'Failed to delete collection')
    },
  })
}
