import React from 'react'
import { Card } from '@/components/ui'
import { Badge, SimpleTooltip } from '@/components/ui'
import { useMemoryStore } from '@/stores'
import { useMemoryStats, useMemoryTags, useMemoryLayers } from '@/hooks'
import { cn } from '@/lib/cn'
import type { MemoryStatus } from '@/types'

const layerColors: Record<string, string> = {
  semantic: '#8b5cf6',
  episodic: '#3b82f6',
  procedural: '#10b981',
  working: '#f97316',
}

export const MemorySidebar: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useMemoryStats()
  const { data: tags = [] } = useMemoryTags()
  const { data: layers = [] } = useMemoryLayers()
  const { viewMode, setViewMode, filter, setFilter, selectedTags, toggleTag } = useMemoryStore()

  const quickFilters: { label: string; value: MemoryStatus | undefined; count?: number }[] = [
    { label: '全部', value: undefined, count: stats?.total },
    { label: '活跃', value: 'active', count: stats?.byStatus.active },
    { label: '已归档', value: 'archived', count: stats?.byStatus.archived },
    { label: '已冻结', value: 'frozen', count: stats?.byStatus.frozen },
  ]

  return (
    <aside className="w-64 border-r border-border bg-card/50 h-full overflow-y-auto">
      <div className="p-4 space-y-6">
        {/* Stats Overview */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">概览</h3>
          {statsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <Card className="p-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">总记忆</span>
                <span className="font-semibold text-text-primary">{stats?.total || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">活跃</span>
                <span className="font-medium text-success">{stats?.byStatus.active || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">已归档</span>
                <span className="font-medium text-amber-600">{stats?.byStatus.archived || 0}</span>
              </div>
            </Card>
          )}
        </div>

        {/* Quick Filters */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">快速筛选</h3>
          <div className="space-y-1">
            {quickFilters.map((q) => (
              <button
                key={q.label}
                onClick={() => setFilter({ status: q.value })}
                className={cn(
                  'w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors',
                  filter.status === q.value
                    ? 'bg-amber-50 text-amber-700 font-medium'
                    : 'text-text-secondary hover:bg-gray-100'
                )}
              >
                <span>{q.label}</span>
                <Badge variant="secondary" className="text-xs">
                  {q.count || 0}
                </Badge>
              </button>
            ))}
          </div>
        </div>

        {/* Tags */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">标签</h3>
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <button
                key={tag.id}
                onClick={() => toggleTag(tag.id)}
                className={cn(
                  'px-2 py-1 rounded-full text-xs transition-all',
                  selectedTags.includes(tag.id)
                    ? 'bg-amber-500 text-white'
                    : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
                )}
              >
                {tag.name}
                {tag.count && <span className="ml-1 opacity-70">({tag.count})</span>}
              </button>
            ))}
            {tags.length === 0 && (
              <span className="text-xs text-text-muted">暂无标签</span>
            )}
          </div>
        </div>

        {/* Layer Mapping */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">记忆层级</h3>
          <div className="space-y-2">
            {layers.map((layer) => (
              <div key={layer.layer} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="capitalize text-text-secondary">{layer.layer}</span>
                  <span className="text-text-muted">{layer.count} ({layer.percentage}%)</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${layer.percentage}%`, backgroundColor: layerColors[layer.layer] || '#f59e0b' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">视图</h3>
          <div className="flex gap-1">
            {(['list', 'grid', 'graph'] as const).map((mode) => (
              <SimpleTooltip key={mode} content={mode === 'list' ? '列表视图' : mode === 'grid' ? '网格视图' : '图谱视图'}>
                <button
                  onClick={() => setViewMode(mode)}
                  className={cn(
                    'flex-1 p-2 rounded-lg text-xs font-medium transition-colors',
                    viewMode === mode
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-gray-100 text-text-muted hover:bg-gray-200'
                  )}
                >
                  {mode === 'list' ? '列表' : mode === 'grid' ? '网格' : '图谱'}
                </button>
              </SimpleTooltip>
            ))}
          </div>
        </div>
      </div>
    </aside>
  )
}
