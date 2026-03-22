import React from 'react'
import { Card, Badge } from '@/components/ui'
import { cn } from '@/lib/cn'
import type { Memory } from '@/types'

interface MemoryCardProps {
  memory: Memory
  isSelected?: boolean
  isSelectable?: boolean
  onSelect?: (id: string) => void
  onClick?: (id: string) => void
}

export const MemoryCard: React.FC<MemoryCardProps> = ({
  memory,
  isSelected,
  isSelectable,
  onSelect,
  onClick,
}) => {
  const priorityColors = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-50 text-blue-600',
    high: 'bg-amber-50 text-amber-600',
    urgent: 'bg-red-50 text-red-600',
  }

  const layerColors = {
    semantic: 'bg-purple-50 text-purple-600',
    episodic: 'bg-blue-50 text-blue-600',
    procedural: 'bg-green-50 text-green-600',
    working: 'bg-orange-50 text-orange-600',
  }

  return (
    <Card
      className={cn(
        'p-4 cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-0.5',
        isSelected && 'ring-2 ring-amber-500 bg-amber-50/50'
      )}
      onClick={() => onClick?.(memory.id)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-text-primary truncate">{memory.title}</h4>
        </div>
        {isSelectable && (
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => {
              e.stopPropagation()
              onSelect?.(memory.id)
            }}
            className="w-4 h-4 text-amber-500 rounded border-gray-300 focus:ring-amber-500 mt-1"
          />
        )}
      </div>

      {/* Content preview */}
      <p className="text-sm text-text-secondary line-clamp-2 mb-3">{memory.content}</p>

      {/* Tags */}
      {memory.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {memory.tags.slice(0, 3).map((tag) => (
            <Badge key={tag.id} variant="secondary" className="text-xs">
              {tag.name}
            </Badge>
          ))}
          {memory.tags.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{memory.tags.length - 3}
            </Badge>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge className={priorityColors[memory.priority]} variant="secondary">
            {memory.priority === 'urgent' ? '紧急' : memory.priority}
          </Badge>
          {memory.layer && (
            <Badge className={layerColors[memory.layer]} variant="secondary">
              {memory.layer === 'semantic' ? '语义' :
               memory.layer === 'episodic' ? '情景' :
               memory.layer === 'procedural' ? '程序' : '工作'}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span>{memory.access.accessCount} 次访问</span>
        </div>
      </div>

      {/* Importance indicator */}
      <div className="flex items-center gap-1 mt-2">
        {[1, 2, 3, 4, 5].map((level) => (
          <div
            key={level}
            className={cn(
              'w-2 h-2 rounded-full transition-colors',
              level <= memory.importance ? 'bg-amber-400' : 'bg-gray-200'
            )}
          />
        ))}
        <span className="ml-1 text-xs text-text-muted">重要性</span>
      </div>
    </Card>
  )
}
