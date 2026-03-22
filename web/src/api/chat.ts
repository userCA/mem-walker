import { api } from '../lib/api-client'
import type { ChatSession, ChatMessage, ChatConfig, ApiResponse, PaginatedResponse, ApiQueryParams } from '@/types'

export const chatApi = {
  listSessions: async (params?: ApiQueryParams): Promise<ApiResponse<PaginatedResponse<ChatSession>>> => {
    return api.get<PaginatedResponse<ChatSession>>('/chat/sessions', { params })
  },

  getSession: async (id: string): Promise<ApiResponse<ChatSession>> => {
    return api.get<ChatSession>(`/chat/sessions/${id}`)
  },

  createSession: async (data?: Partial<ChatSession>): Promise<ApiResponse<ChatSession>> => {
    return api.post<ChatSession>('/chat/sessions', data || {})
  },

  updateSession: async (id: string, data: Partial<ChatSession>): Promise<ApiResponse<ChatSession>> => {
    return api.patch<ChatSession>(`/chat/sessions/${id}`, data)
  },

  deleteSession: async (id: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/chat/sessions/${id}`)
  },

  sendMessage: async (
    sessionId: string,
    content: string,
    config?: Partial<ChatConfig>
  ): Promise<ApiResponse<{ userMessage: ChatMessage; assistantMessage: ChatMessage }>> => {
    return api.post(`/chat/sessions/${sessionId}/messages`, { content, config })
  },

  getConfig: async (): Promise<ApiResponse<ChatConfig>> => {
    return api.get<ChatConfig>('/chat/config')
  },

  updateConfig: async (config: Partial<ChatConfig>): Promise<ApiResponse<ChatConfig>> => {
    return api.patch<ChatConfig>('/chat/config', config)
  },

  getPresets: async (): Promise<ApiResponse<Array<{ id: string; name: string; description: string; icon: string; config: Partial<ChatConfig> }>>> => {
    return api.get('/chat/presets')
  },

  deleteMessage: async (sessionId: string, messageId: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/chat/sessions/${sessionId}/messages/${messageId}`)
  },

  clearSession: async (sessionId: string): Promise<ApiResponse<void>> => {
    return api.delete<void>(`/chat/sessions/${sessionId}/messages`)
  },

  regenerateMessage: async (sessionId: string, messageId: string): Promise<ApiResponse<ChatMessage>> => {
    return api.post<ChatMessage>(`/chat/sessions/${sessionId}/messages/${messageId}/regenerate`)
  },
}
