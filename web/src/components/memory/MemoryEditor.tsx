import React, { useState } from 'react'
import { Modal, Input, Textarea, Button, Select, RangeSlider } from '@/components/ui'
import { useCreateMemory, useMemoryTags } from '@/hooks'
import type { MemoryPriority, MemoryImportance } from '@/types'

interface MemoryEditorProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

export const MemoryEditor: React.FC<MemoryEditorProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [priority, setPriority] = useState<MemoryPriority>('medium')
  const [importance, setImportance] = useState<MemoryImportance>(3)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [newTag, setNewTag] = useState('')

  const { data: tags = [] } = useMemoryTags()
  const createMemory = useCreateMemory()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !content.trim()) return

    await createMemory.mutateAsync({
      title: title.trim(),
      content: content.trim(),
      priority,
      importance,
      tags: selectedTags.map((id) => ({ id, name: '' })),
    })

    // Reset form
    setTitle('')
    setContent('')
    setPriority('medium')
    setImportance(3)
    setSelectedTags([])
    onSuccess?.()
    onClose()
  }

  const toggleTag = (tagId: string) => {
    setSelectedTags((prev) =>
      prev.includes(tagId) ? prev.filter((t) => t !== tagId) : [...prev, tagId]
    )
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="创建新记忆"
      className="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">标题</label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="记忆的标题..."
            required
          />
        </div>

        {/* Content */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">内容</label>
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="记忆的内容..."
            rows={6}
            required
          />
        </div>

        {/* Priority */}
        <div className="space-y-1">
          <label className="text-sm font-medium text-text-primary">优先级</label>
          <Select
            value={priority}
            onChange={(e) => setPriority(e.target.value as MemoryPriority)}
            options={[
              { value: 'low', label: '低' },
              { value: 'medium', label: '中' },
              { value: 'high', label: '高' },
              { value: 'urgent', label: '紧急' },
            ]}
          />
        </div>

        {/* Importance */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">重要性</label>
          <RangeSlider
            value={importance}
            onChange={(val) => setImportance(val as MemoryImportance)}
            min={1}
            max={5}
            step={1}
            formatLabel={(val) => `${val}星`}
          />
        </div>

        {/* Tags */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-text-primary">标签</label>
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => toggleTag(tag.id)}
                className={`px-2 py-1 rounded-full text-xs transition-all ${
                  selectedTags.includes(tag.id)
                    ? 'bg-amber-500 text-white'
                    : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
                }`}
              >
                {tag.name}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="添加新标签..."
              className="flex-1"
            />
            <Button type="button" variant="secondary" size="sm">
              添加
            </Button>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>
            取消
          </Button>
          <Button type="submit" className="flex-1" disabled={createMemory.isPending}>
            {createMemory.isPending ? '创建中...' : '创建'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
