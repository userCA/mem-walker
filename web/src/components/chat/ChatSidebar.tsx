import React from 'react'
import { Button, Badge } from '@/components/ui'
import { useChatSessions, useCreateChatSession, useChatStore } from '@/hooks'
import { cn } from '@/lib/cn'

export const ChatSidebar: React.FC = () => {
  const { data, isLoading } = useChatSessions()
  const { currentSessionId, setCurrentSessionId } = useChatStore()
  const createSession = useCreateChatSession()

  const handleCreateSession = async () => {
    try {
      const result = await createSession.mutateAsync({})
      if (result.data) {
        setCurrentSessionId(result.data.id)
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const sessions = data?.items || []

  return (
    <aside className="w-64 border-r border-border bg-card/50 h-full overflow-y-auto">
      <div className="p-4 space-y-4">
        {/* New Chat Button */}
        <Button className="w-full" size="sm" onClick={handleCreateSession} isLoading={createSession.isPending}>
          新对话
        </Button>

        {/* Session List */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">
            对话历史
          </h3>

          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-text-muted text-center py-4">暂无对话</p>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => setCurrentSessionId(session.id)}
                className={cn(
                  'w-full p-3 rounded-lg text-left transition-all group',
                  currentSessionId === session.id
                    ? 'bg-amber-50 border border-amber-200'
                    : 'hover:bg-gray-50 border border-transparent'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">
                      {session.title}
                    </p>
                    <p className="text-xs text-text-muted mt-0.5">
                      {session.memoryCount} 条记忆 · {session.messages.length} 条消息
                    </p>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {session.isPinned && (
                      <Badge variant="secondary" className="text-xs">
                        置顶
                      </Badge>
                    )}
                  </div>
                </div>
                <p className="text-xs text-text-muted mt-1">
                  {new Date(session.updatedAt).toLocaleDateString()}
                </p>
              </button>
            ))
          )}
        </div>
      </div>
    </aside>
  )
}
