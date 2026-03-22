import React from 'react'
import { Card, Badge, Button } from '@/components/ui'
import { cn } from '@/lib/cn'
import type { ChatMessage as ChatMessageType } from '@/types'

interface ChatMessageProps {
  message: ChatMessageType
  onRegenerate?: () => void
  onCopy?: () => void
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onRegenerate,
  onCopy,
}) => {
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'

  // Debug logging
  console.log('=== ChatMessage render ===')
  console.log('message.id:', message.id)
  console.log('message.role:', message.role)
  console.log('message.content:', JSON.stringify(message.content))
  console.log('message.status:', message.status)
  console.log('message:', message)

  return (
    <div
      className={cn(
        'flex gap-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm font-medium',
          isUser
            ? 'bg-amber-100 text-amber-700'
            : isAssistant
            ? 'bg-green-100 text-green-700'
            : 'bg-gray-100 text-gray-600'
        )}
      >
        {isUser ? '👤' : isAssistant ? '🤖' : '⚙️'}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          'flex-1 max-w-[80%]',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'p-3 rounded-lg',
            isUser
              ? 'bg-gray-100 text-gray-800 rounded-tr-none'
              : 'bg-gray-100 text-gray-800 rounded-tl-none'
          )}
        >
          {/* Status indicator for streaming */}
          {message.status === 'streaming' && (
            <div className="flex items-center gap-1 mb-2">
              <span className="text-xs opacity-70">生成中</span>
              <span className="flex gap-0.5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1 h-1 bg-current rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  />
                ))}
              </span>
            </div>
          )}

          {/* Message text */}
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>

          {/* Error indicator */}
          {message.status === 'error' && (
            <div className="mt-2 text-xs text-red-200">发送失败</div>
          )}
        </div>

        {/* Memory References */}
        {message.memoryReferences && message.memoryReferences.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-xs text-text-muted">引用记忆:</p>
            <div className="flex flex-wrap gap-1">
              {message.memoryReferences.map((ref) => (
                <Badge key={ref.id} variant="secondary" className="text-xs cursor-pointer hover:bg-gray-200">
                  {ref.title}
                  {ref.similarity && (
                    <span className="ml-1 opacity-70">{Math.round(ref.similarity * 100)}%</span>
                  )}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        {isAssistant && (
          <div className="flex items-center gap-1 mt-1">
            <Button
              size="sm"
              variant="ghost"
              className="text-xs h-6 px-2"
              onClick={onCopy}
            >
              复制
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="text-xs h-6 px-2"
              onClick={onRegenerate}
            >
              重新生成
            </Button>
          </div>
        )}

        {/* Timestamp */}
        <p
          className={cn(
            'text-xs text-text-muted mt-1',
            isUser && 'text-right'
          )}
        >
          {new Date(message.createdAt).toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}
