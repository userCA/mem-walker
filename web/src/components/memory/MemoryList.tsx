import React, { useState, useMemo } from 'react'
import { Input, Button, Card } from '@/components/ui'
import { MemoryCard } from './MemoryCard'
import { useMemories, useMemoryStore } from '@/hooks'
import { cn } from '@/lib/cn'

interface MemoryListProps {
  onMemoryClick: (id: string) => void
}

export const MemoryList: React.FC<MemoryListProps> = ({ onMemoryClick }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const {
    selectedMemoryId,
    setSelectedMemoryId,
    selectedIds,
    toggleSelectId,
    clearSelection,
    viewMode,
    sort,
    setSort,
    filter,
    selectedTags,
  } = useMemoryStore()

  const { data, isLoading, error } = useMemories({
    search: searchQuery,
    sort: `${sort.field}:${sort.order}`,
    ...filter,
  })

  // Client-side tag filtering
  const memories = useMemo(() => {
    if (!data?.items) return []
    if (selectedTags.length === 0) return data.items

    return data.items.filter((memory) =>
      memory.tags.some((tag) => selectedTags.includes(tag.id))
    )
  }, [data?.items, selectedTags])

  const isSelectMode = selectedIds.length > 0

  const handleSortChange = (field: 'updatedAt' | 'createdAt' | 'importance') => {
    setSort({
      field,
      order: sort.field === field && sort.order === 'desc' ? 'asc' : 'desc',
    })
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <p className="text-red-500 mb-2">加载失败</p>
          <p className="text-sm text-text-muted">{error.message}</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Search and Sort Bar */}
      <div className="p-4 border-b border-border space-y-3">
        <div className="flex items-center gap-3">
          <Input
            placeholder="搜索记忆..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1"
          />
          <Button variant="secondary" size="sm">
            排序
          </Button>
        </div>

        {/* Sort Options */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-text-muted">排序:</span>
          {[
            { key: 'updatedAt', label: '更新时间' },
            { key: 'createdAt', label: '创建时间' },
            { key: 'importance', label: '重要性' },
          ].map((option) => (
            <button
              key={option.key}
              onClick={() => handleSortChange(option.key as 'updatedAt' | 'createdAt' | 'importance')}
              className={cn(
                'px-2 py-1 rounded transition-colors',
                sort.field === option.key
                  ? 'bg-amber-100 text-amber-700 font-medium'
                  : 'text-text-muted hover:bg-gray-100'
              )}
            >
              {option.label}
              {sort.field === option.key && (
                <span className="ml-1">{sort.order === 'desc' ? '↓' : '↑'}</span>
              )}
            </button>
          ))}
        </div>

        {/* Selection Bar */}
        {isSelectMode && (
          <div className="flex items-center justify-between p-2 bg-amber-50 rounded-lg">
            <span className="text-sm text-amber-700">
              已选择 {selectedIds.length} 项
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={clearSelection}>
                取消选择
              </Button>
              <Button size="sm" variant="danger">
                批量删除
              </Button>
              <Button size="sm" variant="secondary">
                批量归档
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* List Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-3xl">🧠</span>
            </div>
            <p className="text-text-primary font-medium mb-1">暂无记忆</p>
            <p className="text-sm text-text-muted">点击上方按钮创建第一个记忆</p>
          </div>
        ) : viewMode === 'list' ? (
          <div className="space-y-3">
            {memories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                isSelected={selectedMemoryId === memory.id}
                isSelectable={isSelectMode}
                onSelect={toggleSelectId}
                onClick={(id) => {
                  if (isSelectMode) {
                    toggleSelectId(id)
                  } else {
                    setSelectedMemoryId(id)
                    onMemoryClick(id)
                  }
                }}
              />
            ))}
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 gap-3">
            {memories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                isSelected={selectedMemoryId === memory.id}
                isSelectable={isSelectMode}
                onSelect={toggleSelectId}
                onClick={(id) => {
                  if (isSelectMode) {
                    toggleSelectId(id)
                  } else {
                    setSelectedMemoryId(id)
                    onMemoryClick(id)
                  }
                }}
              />
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <Card className="p-8 text-center">
              <p className="text-text-muted">图谱视图 - 待实现</p>
            </Card>
          </div>
        )}
      </div>

      {/* Pagination */}
      {data && data.total > data.pageSize && (
        <div className="p-4 border-t border-border flex items-center justify-between">
          <span className="text-sm text-text-muted">
            显示 {(data.page - 1) * data.pageSize + 1} - {Math.min(data.page * data.pageSize, data.total)} / {data.total}
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={data.page <= 1}
            >
              上一页
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={!data.hasMore}
            >
              下一页
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
