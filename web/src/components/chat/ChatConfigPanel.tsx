import React from 'react'
import { Modal, RangeSlider, Input, Toggle, Textarea, Select, Button } from '@/components/ui'
import { useChatConfig, useChatPresets, useChatStore, useUpdateChatConfig } from '@/hooks'
import { cn } from '@/lib/cn'

export const ChatConfigPanel: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const { data: config } = useChatConfig()
  const { data: presets = [] } = useChatPresets()
  const { activePresetId, setActivePresetId, config: localConfig, setConfig } = useChatStore()
  const updateConfig = useUpdateChatConfig()

  const displayConfig = { ...config, ...localConfig }

  const handleSave = async () => {
    await updateConfig.mutateAsync(localConfig)
    onClose()
  }

  const modelOptions = [
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  ]

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="对话设置" className="max-w-lg">
      <div className="space-y-6">
        {/* Presets */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">预设</label>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => {
                  setActivePresetId(preset.id)
                  setConfig(preset.config)
                }}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm transition-colors',
                  activePresetId === preset.id
                    ? 'bg-amber-100 text-amber-700 font-medium'
                    : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
                )}
              >
                {preset.icon} {preset.name}
              </button>
            ))}
          </div>
        </div>

        {/* Model */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">模型</label>
          <Select
            value={displayConfig.model}
            onChange={(e) => setConfig({ model: e.target.value })}
            options={modelOptions}
          />
        </div>

        {/* Temperature */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-text-primary">Temperature</label>
            <span className="text-sm text-text-muted">{displayConfig.temperature.toFixed(1)}</span>
          </div>
          <RangeSlider
            value={displayConfig.temperature}
            onChange={(val) => setConfig({ temperature: val })}
            min={0}
            max={2}
            step={0.1}
          />
          <p className="text-xs text-text-muted">较低的值更确定性，较高的值更有创造性</p>
        </div>

        {/* Max Tokens */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">最大回复长度</label>
          <Input
            type="number"
            value={displayConfig.maxTokens}
            onChange={(e) => setConfig({ maxTokens: parseInt(e.target.value) })}
            min={100}
            max={4000}
            step={100}
          />
        </div>

        {/* Top P */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-text-primary">Top P</label>
            <span className="text-sm text-text-muted">{displayConfig.topP.toFixed(1)}</span>
          </div>
          <RangeSlider
            value={displayConfig.topP}
            onChange={(val) => setConfig({ topP: val })}
            min={0}
            max={1}
            step={0.1}
          />
        </div>

        {/* Include Memories */}
        <Toggle
          enabled={displayConfig.includeMemories}
          onChange={(val) => setConfig({ includeMemories: val })}
          label="引用记忆"
          description="在回复中引用相关记忆内容"
        />

        {/* Memory Threshold */}
        {displayConfig.includeMemories && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-text-primary">记忆引用阈值</label>
              <span className="text-sm text-text-muted">{Math.round(displayConfig.memoryThreshold * 100)}%</span>
            </div>
            <RangeSlider
              value={displayConfig.memoryThreshold}
              onChange={(val) => setConfig({ memoryThreshold: val })}
              min={0}
              max={1}
              step={0.1}
            />
          </div>
        )}

        {/* System Prompt */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">系统提示词</label>
          <Textarea
            value={displayConfig.systemPrompt || ''}
            onChange={(e) => setConfig({ systemPrompt: e.target.value })}
            placeholder="可选的自定义系统提示词..."
            rows={3}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button variant="secondary" className="flex-1" onClick={onClose}>
            取消
          </Button>
          <Button className="flex-1" onClick={handleSave}>
            保存
          </Button>
        </div>
      </div>
    </Modal>
  )
}
