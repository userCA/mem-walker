// Chat Types
export type ChatRole = 'user' | 'assistant' | 'system'

export type ChatMessageStatus = 'sending' | 'sent' | 'error' | 'streaming'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  status: ChatMessageStatus
  memoryReferences?: Array<{
    id: string
    title: string
    similarity?: number
    snippet?: string
  }>
  createdAt: string
  updatedAt?: string
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  memoryCount: number
  createdAt: string
  updatedAt: string
  isPinned?: boolean
  isExpanded?: boolean
}

export interface ChatConfig {
  model: string
  temperature: number
  maxTokens: number
  topP: number
  topK: number
  repeatPenalty: number
  includeMemories: boolean
  memoryThreshold: number
  systemPrompt?: string
}

export interface ChatPreset {
  id: string
  name: string
  description: string
  icon: string
  config: Partial<ChatConfig>
}

export interface ChatStats {
  totalSessions: number
  totalMessages: number
  averageMessagesPerSession: number
  totalMemoryReferences: number
}
