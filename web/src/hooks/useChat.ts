import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from '@/api'
import type { ChatSession, ChatConfig, ApiQueryParams } from '@/types'
import toast from 'react-hot-toast'

// Query Keys
export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  sessionList: (params?: ApiQueryParams) => [...chatKeys.sessions(), 'list', params] as const,
  sessionDetails: () => [...chatKeys.all, 'session'] as const,
  session: (id: string) => [...chatKeys.sessionDetails(), id] as const,
  config: () => [...chatKeys.all, 'config'] as const,
  presets: () => [...chatKeys.all, 'presets'] as const,
}

// Hooks
export function useChatSessions(params?: ApiQueryParams) {
  return useQuery({
    queryKey: chatKeys.sessionList(params),
    queryFn: () => chatApi.listSessions(params).then((res) => res.data!),
  })
}

export function useChatSession(id: string) {
  return useQuery({
    queryKey: chatKeys.session(id),
    queryFn: () => {
      console.log('=== useChatSession fetching ===')
      console.log('Session ID:', id)
      return chatApi.getSession(id).then((res) => {
        console.log('Session API response:', res)
        console.log('Session data:', res.data)
        console.log('Messages in session:', res.data?.messages)
        return res.data!
      })
    },
    enabled: !!id,
  })
}

export function useChatConfig() {
  return useQuery({
    queryKey: chatKeys.config(),
    queryFn: () => chatApi.getConfig().then((res) => res.data!),
  })
}

export function useChatPresets() {
  return useQuery({
    queryKey: chatKeys.presets(),
    queryFn: () => chatApi.getPresets().then((res) => res.data!),
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}

export function useCreateChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data?: Partial<ChatSession>) => chatApi.createSession(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() })
      toast.success('New chat session created')
    },
    onError: () => {
      toast.error('Failed to create session')
    },
  })
}

export function useUpdateChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ChatSession> }) => chatApi.updateSession(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() })
      queryClient.invalidateQueries({ queryKey: chatKeys.session(id) })
    },
    onError: () => {
      toast.error('Failed to update session')
    },
  })
}

export function useDeleteChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => chatApi.deleteSession(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() })
      toast.success('Session deleted')
    },
    onError: () => {
      toast.error('Failed to delete session')
    },
  })
}

export function useSendChatMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, content, config }: { sessionId: string; content: string; config?: Partial<ChatConfig> }) =>
      chatApi.sendMessage(sessionId, content, config),
    onSuccess: (response, { sessionId }) => {
      console.log('=== useSendChatMessage onSuccess ===')
      console.log('Response:', response)
      console.log('sessionId:', sessionId)

      // 直接使对应的 session query 失效，强制重新获取最新数据
      queryClient.invalidateQueries({ queryKey: chatKeys.session(sessionId) })
      // 同时使 sessions list 失效
      queryClient.invalidateQueries({ queryKey: chatKeys.sessions() })

      console.log('Message sent successfully, query invalidated')
    },
    onError: (error) => {
      console.error('Send message error:', error)
      toast.error('Failed to send message')
    },
  })
}

export function useUpdateChatConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (config: Partial<ChatConfig>) => chatApi.updateConfig(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.config() })
      toast.success('Chat configuration updated')
    },
    onError: () => {
      toast.error('Failed to update configuration')
    },
  })
}

export function useDeleteChatMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, messageId }: { sessionId: string; messageId: string }) =>
      chatApi.deleteMessage(sessionId, messageId),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.session(sessionId) })
    },
    onError: () => {
      toast.error('Failed to delete message')
    },
  })
}

export function useClearChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => chatApi.clearSession(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.session(sessionId) })
      toast.success('Chat cleared')
    },
    onError: () => {
      toast.error('Failed to clear chat')
    },
  })
}

export function useRegenerateMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, messageId }: { sessionId: string; messageId: string }) =>
      chatApi.regenerateMessage(sessionId, messageId),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.session(sessionId) })
    },
    onError: () => {
      toast.error('Failed to regenerate message')
    },
  })
}
