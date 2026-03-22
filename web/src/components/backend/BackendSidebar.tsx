import React from 'react'
import { Button } from '@/components/ui'
import { useBackends, useBackendStore } from '@/hooks'
import { cn } from '@/lib/cn'
import type { BackendProvider, BackendStatus } from '@/types'

export const BackendSidebar: React.FC = () => {
  const { data: backends = [], isLoading } = useBackends()
  const { selectedProvider, setSelectedProvider, setIsConnectModalOpen } = useBackendStore()

  const providerLabels: Record<BackendProvider, string> = {
    milvus: 'Milvus',
    sqlite: 'SQLite',
    chroma: 'Chroma',
    qdrant: 'Qdrant',
    weaviate: 'Weaviate',
  }

  const providerIcons: Record<BackendProvider, string> = {
    milvus: '🔍',
    sqlite: '📄',
    chroma: '💎',
    qdrant: '🎯',
    weaviate: '🌐',
  }

  const statusColors: Record<BackendStatus, string> = {
    connected: 'bg-green-500',
    disconnected: 'bg-gray-400',
    error: 'bg-red-500',
    connecting: 'bg-amber-500 animate-pulse',
  }

  const allProviders: BackendProvider[] = ['milvus', 'sqlite', 'chroma', 'qdrant', 'weaviate']

  return (
    <aside className="w-64 border-r border-border bg-card/50 h-full overflow-y-auto">
      <div className="p-4 space-y-4">
        {/* Add Backend Button */}
        <Button
          className="w-full"
          size="sm"
          onClick={() => setIsConnectModalOpen(true)}
        >
          添加后端
        </Button>

        {/* Backend List */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide">
            已连接的后端
          </h3>

          {isLoading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <>
              {backends.length === 0 ? (
                <p className="text-sm text-text-muted text-center py-4">
                  暂无已连接的后端
                </p>
              ) : (
                backends.map((backend) => (
                  <button
                    key={backend.provider}
                    onClick={() => setSelectedProvider(backend.provider)}
                    className={cn(
                      'w-full p-3 rounded-lg text-left transition-all',
                      selectedProvider === backend.provider
                        ? 'bg-amber-50 border border-amber-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{providerIcons[backend.provider]}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary">
                          {providerLabels[backend.provider]}
                        </p>
                        <p className="text-xs text-text-muted truncate">
                          {backend.host}:{backend.port}
                        </p>
                      </div>
                      <div
                        className={cn(
                          'w-2 h-2 rounded-full',
                          statusColors[backend.status]
                        )}
                        title={backend.status}
                      />
                    </div>
                    {backend.status === 'connected' && backend.metrics && (
                      <div className="mt-2 text-xs text-text-muted">
                        <span>{backend.metrics.vectorCount.toLocaleString()} 向量</span>
                      </div>
                    )}
                  </button>
                ))
              )}

              {/* Available Providers */}
              <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wide pt-4">
                可用后端
              </h3>
              {allProviders
                .filter((p) => !backends.find((b) => b.provider === p))
                .map((provider) => (
                  <button
                    key={provider}
                    onClick={() => {
                      setSelectedProvider(provider)
                      setIsConnectModalOpen(true)
                    }}
                    className="w-full p-3 rounded-lg text-left hover:bg-gray-50 border border-dashed border-gray-300 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{providerIcons[provider]}</span>
                      <span className="text-sm text-text-muted">{providerLabels[provider]}</span>
                    </div>
                  </button>
                ))}
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
