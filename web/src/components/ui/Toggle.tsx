import React from 'react'
import { cn } from '@/lib/cn'

interface ToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  label?: string
  description?: string
  className?: string
}

export const Toggle: React.FC<ToggleProps> = ({
  enabled,
  onChange,
  label,
  description,
  className,
}) => {
  return (
    <div className={cn('flex items-center justify-between', className)}>
      {(label || description) && (
        <div>
          {label && (
            <div className="text-sm font-medium text-text-primary">{label}</div>
          )}
          {description && (
            <div className="text-xs text-text-muted">{description}</div>
          )}
        </div>
      )}
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        onClick={() => onChange(!enabled)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full',
          'border-2 border-transparent transition-colors duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2',
          enabled ? 'bg-success' : 'bg-gray-300'
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow',
            'transition duration-200',
            enabled ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
    </div>
  )
}
