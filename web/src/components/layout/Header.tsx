import React from 'react'
import { Button, Badge } from '@/components/ui'
import { useAppStore, type AppMode } from '@/stores'
import { useBackends } from '@/hooks'
import { cn } from '@/lib/cn'

export const Header: React.FC = () => {
  const { mode, setMode } = useAppStore()
  const { data: backends = [] } = useBackends()

  const connectedCount = backends.filter((b) => b.status === 'connected').length

  const modes: { key: AppMode; label: string; icon: string }[] = [
    { key: 'memory', label: '记忆管理', icon: '🧠' },
    { key: 'chat', label: '记忆对话', icon: '💬' },
    { key: 'backend', label: '存储后端', icon: '🗄️' },
  ]

  return (
    <header className="h-14 border-b border-border bg-card px-4 flex items-center justify-between">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🧠</span>
          <h1 className="text-lg font-semibold text-text-primary">Mnemosyne</h1>
        </div>
        <Badge variant="secondary" className="text-xs">
          v0.1.0
        </Badge>
      </div>

      {/* Mode Tabs */}
      <nav className="flex items-center gap-1">
        {modes.map((m) => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              mode === m.key
                ? 'bg-amber-100 text-amber-700'
                : 'text-text-secondary hover:bg-gray-100'
            )}
          >
            <span>{m.icon}</span>
            <span>{m.label}</span>
          </button>
        ))}
      </nav>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {/* Status */}
        <div className="flex items-center gap-2 text-sm">
          <div className="flex items-center gap-1">
            <div
              className={cn(
                'w-2 h-2 rounded-full',
                connectedCount > 0 ? 'bg-green-500' : 'bg-gray-400'
              )}
            />
            <span className="text-text-muted">
              {connectedCount} 后端
            </span>
          </div>
        </div>

        {/* Import/Export */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm">
            导入
          </Button>
          <Button variant="ghost" size="sm">
            导出
          </Button>
        </div>

        {/* Settings */}
        <Button variant="ghost" size="sm">
          ⚙️
        </Button>
      </div>
    </header>
  )
}
