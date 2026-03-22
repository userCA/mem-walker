import React, { useState } from 'react'
import { Modal, Input, Select, Button, Toggle } from '@/components/ui'
import { useConnectBackend, useTestBackend, useBackendStore } from '@/hooks'
import type { BackendConfig, BackendProvider } from '@/types'

export const ConnectModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const [provider, setProvider] = useState<BackendProvider>('milvus')
  const [host, setHost] = useState('localhost')
  const [port, setPort] = useState('19530')
  const [database, setDatabase] = useState('default')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [ssl, setSsl] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; latency?: number; error?: string } | null>(null)

  const { setIsConnectModalOpen, setSelectedProvider } = useBackendStore()
  const connectBackend = useConnectBackend()
  const testBackend = useTestBackend()

  const providerOptions = [
    { value: 'milvus', label: 'Milvus' },
    { value: 'sqlite', label: 'SQLite' },
    { value: 'chroma', label: 'Chroma' },
    { value: 'qdrant', label: 'Qdrant' },
    { value: 'weaviate', label: 'Weaviate' },
  ]

  const defaultPorts: Record<BackendProvider, string> = {
    milvus: '19530',
    sqlite: '',
    chroma: '8000',
    qdrant: '6333',
    weaviate: '8080',
  }

  const handleProviderChange = (value: string) => {
    setProvider(value as BackendProvider)
    setPort(defaultPorts[value as BackendProvider])
  }

  const handleTest = async () => {
    const config: BackendConfig = {
      provider,
      host,
      port: parseInt(port),
      database,
      username: username || undefined,
      password: password || undefined,
      ssl,
    }
    const result = await testBackend.mutateAsync(config)
    setTestResult({
      success: result.success,
      latency: result.data?.latency,
      error: result.data?.error,
    })
  }

  const handleConnect = async () => {
    const config: BackendConfig = {
      provider,
      host,
      port: parseInt(port),
      database,
      username: username || undefined,
      password: password || undefined,
      ssl,
    }
    await connectBackend.mutateAsync(config)
    setSelectedProvider(provider)
    setIsConnectModalOpen(false)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="连接后端" className="max-w-md">
      <div className="space-y-4">
        {/* Provider */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">后端类型</label>
          <Select
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value)}
            options={providerOptions}
          />
        </div>

        {/* Host */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">主机</label>
          <Input
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="localhost"
          />
        </div>

        {/* Port */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">端口</label>
          <Input
            type="number"
            value={port}
            onChange={(e) => setPort(e.target.value)}
            placeholder={defaultPorts[provider]}
          />
        </div>

        {/* Database */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">数据库/集合</label>
          <Input
            value={database}
            onChange={(e) => setDatabase(e.target.value)}
            placeholder="default"
          />
        </div>

        {/* Credentials */}
        {(provider === 'milvus' || provider === 'qdrant' || provider === 'weaviate') && (
          <>
            <div className="space-y-1">
              <label className="text-sm font-medium text-text-primary">用户名</label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="可选"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-text-primary">密码</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="可选"
              />
            </div>
          </>
        )}

        {/* SSL */}
        <Toggle
          enabled={ssl}
          onChange={setSsl}
          label="使用 SSL"
          description="通过 TLS/SSL 加密连接"
        />

        {/* Test Result */}
        {testResult && (
          <div
            className={`p-3 rounded-lg text-sm ${
              testResult.success
                ? 'bg-green-50 text-green-700'
                : 'bg-red-50 text-red-700'
            }`}
          >
            {testResult.success ? (
              <span>连接成功 {testResult.latency && `(${testResult.latency}ms)`}</span>
            ) : (
              <span>连接失败: {testResult.error}</span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            variant="secondary"
            className="flex-1"
            onClick={handleTest}
            disabled={testBackend.isPending}
          >
            {testBackend.isPending ? '测试中...' : '测试连接'}
          </Button>
          <Button
            className="flex-1"
            onClick={handleConnect}
            disabled={connectBackend.isPending}
          >
            {connectBackend.isPending ? '连接中...' : '连接'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
