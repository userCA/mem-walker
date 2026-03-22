import React from 'react'
import { Card, Badge, Button } from '@/components/ui'
import { useBackend, useBackendMetrics, useBackendStore } from '@/hooks'
import type { BackendProvider, BackendStatus } from '@/types'

interface BackendDetailProps {
  provider: BackendProvider
}

export const BackendDetail: React.FC<BackendDetailProps> = ({ provider }) => {
  const { data: backend, isLoading } = useBackend(provider)
  const { data: metrics } = useBackendMetrics(provider)
  const { setIsConfigModalOpen, setEditingConfig } = useBackendStore()

  const providerLabels: Record<BackendProvider, string> = {
    milvus: 'Milvus',
    sqlite: 'SQLite',
    chroma: 'Chroma',
    qdrant: 'Qdrant',
    weaviate: 'Weaviate',
  }

  const statusLabels: Record<BackendStatus, string> = {
    connected: '已连接',
    disconnected: '未连接',
    error: '错误',
    connecting: '连接中',
  }

  const statusColors: Record<BackendStatus, string> = {
    connected: 'bg-green-100 text-green-700',
    disconnected: 'bg-gray-100 text-gray-600',
    error: 'bg-red-100 text-red-700',
    connecting: 'bg-amber-100 text-amber-700',
  }

  if (isLoading) {
    return (
      <div className="flex-1 p-4">
        <div className="space-y-4">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="h-32 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  if (!backend) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-text-muted">选择后端查看详情</p>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-text-primary">
              {providerLabels[backend.provider]}
            </h1>
            <Badge className={statusColors[backend.status]}>
              {statusLabels[backend.status]}
            </Badge>
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setEditingConfig({
                  provider: backend.provider,
                  host: backend.host,
                  port: backend.port,
                  database: backend.database,
                })
                setIsConfigModalOpen(true)
              }}
            >
              配置
            </Button>
            <Button variant="danger" size="sm">
              断开
            </Button>
          </div>
        </div>

        {/* Connection Info */}
        <Card className="p-4">
          <h3 className="text-sm font-medium text-text-primary mb-3">连接信息</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-text-muted">主机</p>
              <p className="text-text-primary font-medium">{backend.host}</p>
            </div>
            <div>
              <p className="text-text-muted">端口</p>
              <p className="text-text-primary font-medium">{backend.port}</p>
            </div>
            <div>
              <p className="text-text-muted">数据库</p>
              <p className="text-text-primary font-medium">{backend.database}</p>
            </div>
            <div>
              <p className="text-text-muted">延迟</p>
              <p className="text-text-primary font-medium">
                {backend.health.latency ? `${backend.health.latency}ms` : '-'}
              </p>
            </div>
          </div>
        </Card>

        {/* Metrics */}
        {metrics && (
          <Card className="p-4">
            <h3 className="text-sm font-medium text-text-primary mb-3">存储指标</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-text-muted mb-1">总内存</p>
                <p className="text-lg font-semibold text-text-primary">
                  {formatBytes(metrics.totalMemory)}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-text-muted mb-1">已用内存</p>
                <p className="text-lg font-semibold text-text-primary">
                  {formatBytes(metrics.usedMemory)}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-text-muted mb-1">向量数量</p>
                <p className="text-lg font-semibold text-text-primary">
                  {metrics.vectorCount.toLocaleString()}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-text-muted mb-1">磁盘使用</p>
                <p className="text-lg font-semibold text-text-primary">
                  {formatBytes(metrics.diskUsage)}
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Collections */}
        {backend.collections && backend.collections.length > 0 && (
          <Card className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-text-primary">集合</h3>
              <Button variant="ghost" size="sm">
                新建集合
              </Button>
            </div>
            <div className="space-y-2">
              {backend.collections.map((collection) => (
                <div
                  key={collection.name}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium text-text-primary">{collection.name}</p>
                    <p className="text-xs text-text-muted">
                      {collection.memoryCount.toLocaleString()} 向量 · {collection.vectorDimension} 维
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{collection.indexType}</Badge>
                    <Button variant="ghost" size="sm">
                      删除
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Quick Actions */}
        <Card className="p-4">
          <h3 className="text-sm font-medium text-text-primary mb-3">快速操作</h3>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm">
              测试连接
            </Button>
            <Button variant="secondary" size="sm">
              刷新指标
            </Button>
            <Button variant="secondary" size="sm">
              优化索引
            </Button>
            <Button variant="secondary" size="sm">
              导出配置
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}
