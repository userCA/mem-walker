import React, { useState } from 'react'
import { Button, Badge, Card, Input, Textarea } from '@/components/ui'
import { useMemory, useUpdateMemory, useDeleteMemory, useMemoryStore } from '@/hooks'
import { cn } from '@/lib/cn'
import type { MemoryStatus, MemoryPriority, MemoryImportance } from '@/types'

interface MemoryDetailProps {
  memoryId: string
  onClose: () => void
}

export const MemoryDetail: React.FC<MemoryDetailProps> = ({ memoryId, onClose }) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [editedTitle, setEditedTitle] = useState('')
  const [editedPriority, setEditedPriority] = useState<MemoryPriority>('medium')
  const [editedImportance, setEditedImportance] = useState<MemoryImportance>(3)

  const { data: memory, isLoading } = useMemory(memoryId)
  const updateMemory = useUpdateMemory()
  const deleteMemory = useDeleteMemory()
  const { setSelectedMemoryId } = useMemoryStore()

  React.useEffect(() => {
    if (memory) {
      setEditedTitle(memory.title)
      setEditedContent(memory.content)
      setEditedPriority(memory.priority)
      setEditedImportance(memory.importance)
    }
  }, [memory])

  const handleSave = async () => {
    await updateMemory.mutateAsync({
      id: memoryId,
      data: {
        title: editedTitle,
        content: editedContent,
        priority: editedPriority,
        importance: editedImportance,
      },
    })
    setIsEditing(false)
  }

  const handleDelete = async () => {
    if (window.confirm('确定要删除这条记忆吗？')) {
      await deleteMemory.mutateAsync(memoryId)
      setSelectedMemoryId(null)
      onClose()
    }
  }

  const statusLabels: Record<MemoryStatus, string> = {
    active: '活跃',
    archived: '已归档',
    frozen: '已冻结',
    deleted: '已删除',
  }

  const priorityLabels: Record<MemoryPriority, string> = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急',
  }

  if (isLoading) {
    return (
      <div className="w-96 border-l border-border h-full overflow-y-auto p-4">
        <div className="space-y-4">
          <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-full bg-gray-100 rounded animate-pulse" />
          <div className="h-4 w-3/4 bg-gray-100 rounded animate-pulse" />
          <div className="h-32 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  if (!memory) {
    return (
      <div className="w-96 border-l border-border h-full flex items-center justify-center">
        <p className="text-text-muted">选择一条记忆查看详情</p>
      </div>
    )
  }

  return (
    <div className="w-96 border-l border-border h-full overflow-y-auto bg-card">
      {/* Header */}
      <div className="sticky top-0 bg-card border-b border-border p-4 z-10">
        <div className="flex items-center justify-between mb-2">
          <Badge
            className={cn(
              memory.status === 'active' && 'bg-green-100 text-green-700',
              memory.status === 'archived' && 'bg-amber-100 text-amber-700',
              memory.status === 'frozen' && 'bg-blue-100 text-blue-700'
            )}
          >
            {statusLabels[memory.status]}
          </Badge>
          <div className="flex gap-1">
            {!isEditing && (
              <>
                <Button size="sm" variant="ghost" onClick={() => setIsEditing(true)}>
                  编辑
                </Button>
                <Button size="sm" variant="ghost" onClick={handleDelete}>
                  删除
                </Button>
              </>
            )}
            <Button size="sm" variant="ghost" onClick={onClose}>
              关闭
            </Button>
          </div>
        </div>

        {isEditing ? (
          <Input
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            className="text-lg font-semibold"
          />
        ) : (
          <h2 className="text-lg font-semibold text-text-primary">{memory.title}</h2>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Metadata */}
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{priorityLabels[memory.priority]}优先级</Badge>
          {memory.layer && (
            <Badge variant="secondary" className="capitalize">
              {memory.layer === 'semantic' ? '语义层' :
               memory.layer === 'episodic' ? '情景层' :
               memory.layer === 'procedural' ? '程序层' : '工作层'}
            </Badge>
          )}
        </div>

        {/* Importance */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-text-muted">重要性</label>
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4, 5].map((level) => (
              <button
                key={level}
                onClick={() => isEditing && setEditedImportance(level as MemoryImportance)}
                className={cn(
                  'w-6 h-6 rounded-full transition-all',
                  level <= (isEditing ? editedImportance : memory.importance)
                    ? 'bg-amber-400 text-white'
                    : 'bg-gray-200',
                  isEditing && 'hover:scale-110 cursor-pointer'
                )}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-text-muted">内容</label>
          {isEditing ? (
            <Textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              rows={8}
            />
          ) : (
            <Card className="p-3 text-sm text-text-secondary whitespace-pre-wrap">
              {memory.content}
            </Card>
          )}
        </div>

        {/* Tags */}
        {memory.tags.length > 0 && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted">标签</label>
            <div className="flex flex-wrap gap-1">
              {memory.tags.map((tag) => (
                <Badge key={tag.id} variant="secondary">
                  {tag.name}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* References */}
        {memory.references && memory.references.length > 0 && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted">相关记忆</label>
            <div className="space-y-2">
              {memory.references.map((ref) => (
                <Card
                  key={ref.id}
                  className="p-2 cursor-pointer hover:bg-gray-50"
                  onClick={() => setSelectedMemoryId(ref.id)}
                >
                  <p className="text-sm font-medium">{ref.title}</p>
                  {ref.similarity && (
                    <p className="text-xs text-text-muted">相似度: {Math.round(ref.similarity * 100)}%</p>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        <Card className="p-3 space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">访问次数</span>
            <span className="text-text-primary">{memory.access.accessCount}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">创建时间</span>
            <span className="text-text-primary">{new Date(memory.createdAt).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-text-muted">最后访问</span>
            <span className="text-text-primary">{new Date(memory.access.lastAccessedAt).toLocaleDateString()}</span>
          </div>
        </Card>

        {/* Edit Actions */}
        {isEditing && (
          <div className="flex gap-2">
            <Button className="flex-1" onClick={handleSave}>
              保存
            </Button>
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => setIsEditing(false)}
            >
              取消
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
