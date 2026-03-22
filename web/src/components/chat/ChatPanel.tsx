import React, { useState, useRef, useEffect } from 'react'
import { Button, Input } from '@/components/ui'
import { ChatMessage } from './ChatMessage'
import { useChatSession, useSendChatMessage, useCreateChatSession, useChatStore } from '@/hooks'

export const ChatPanel: React.FC = () => {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const { currentSessionId, config, setCurrentSessionId } = useChatStore()
  const { data: session, isLoading } = useChatSession(currentSessionId || '')
  const sendMessage = useSendChatMessage()
  const createSession = useCreateChatSession()

  const handleCreateSession = async () => {
    try {
      const result = await createSession.mutateAsync({})
      console.log('=== handleCreateSession ===')
      console.log('Result:', result)
      console.log('Result.data:', result?.data)
      if (result?.data) {
        console.log('Setting currentSessionId to:', result.data.id)
        setCurrentSessionId(result.data.id)
      } else {
        console.error('result.data is undefined!')
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const messages = session?.messages || []

  // Debug: 打印 session 数据
  console.log('Session data:', session)
  console.log('Messages:', messages)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || !currentSessionId) {
      console.log('Submit blocked: inputValue =', JSON.stringify(inputValue), 'currentSessionId =', currentSessionId)
      return
    }

    const content = inputValue.trim()
    console.log('=== handleSubmit ===')
    console.log('Content:', content)
    console.log('SessionId:', currentSessionId)
    console.log('Config:', config)
    setInputValue('')

    try {
      const result = await sendMessage.mutateAsync({
        sessionId: currentSessionId,
        content,
        config,
      })
      console.log('Send message result:', result)
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  if (!currentSessionId) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-background">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">💬</span>
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">开始新对话</h2>
          <p className="text-text-muted mb-4">
            选择左侧会话历史中的对话，或创建新对话开始聊天
          </p>
          <Button onClick={handleCreateSession} isLoading={createSession.isPending}>创建新对话</Button>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="space-y-4 w-64">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mx-auto" />
          <div className="h-32 w-full bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-text-primary">{session?.title || '新对话'}</h2>
            <p className="text-xs text-text-muted">
              {messages.length} 条消息 · {session?.memoryCount || 0} 条记忆
            </p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost">
              设置
            </Button>
            <Button size="sm" variant="ghost">
              清空
            </Button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !sendMessage.isPending ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <p className="text-text-muted">发送消息开始对话</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onRegenerate={() => {
                  // TODO: Implement regenerate
                }}
                onCopy={() => {
                  navigator.clipboard.writeText(message.content)
                }}
              />
            ))}
            {/* AI typing indicator - 精致的小点动画 */}
            {sendMessage.isPending && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-100 to-amber-50 flex items-center justify-center shadow-sm">
                  <span className="text-sm">✨</span>
                </div>
                <div className="bg-white/80 backdrop-blur-sm rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-border bg-card">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="输入消息..."
            className="flex-1"
            disabled={sendMessage.isPending}
          />
          <Button
            type="submit"
            disabled={!inputValue.trim() || sendMessage.isPending}
            isLoading={sendMessage.isPending}
          >
            发送
          </Button>
        </form>
        <p className="text-xs text-text-muted mt-2 text-center">
          按 Enter 发送，Shift + Enter 换行
        </p>
      </div>
    </div>
  )
}
