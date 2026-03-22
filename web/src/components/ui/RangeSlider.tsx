import React from 'react'
import { cn } from '@/lib/cn'

interface RangeSliderProps {
  min: number
  max: number
  value: number
  onChange: (value: number) => void
  step?: number
  label?: string
  showValue?: boolean
  formatValue?: (value: number) => string
  formatLabel?: (value: number) => string
  className?: string
}

export const RangeSlider: React.FC<RangeSliderProps> = ({
  min,
  max,
  value,
  onChange,
  step = 1,
  label,
  showValue = true,
  formatValue,
  formatLabel = (v) => String(v),
  className,
}) => {
  const displayValue = formatValue ? formatValue(value) : formatLabel(value);
  const percentage = ((value - min) / (max - min)) * 100

  return (
    <div className={cn('w-full', className)}>
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <span className="text-sm text-text-secondary">{label}</span>
          )}
          {showValue && (
            <span className="text-sm font-medium text-text-primary">
              {displayValue}
            </span>
          )}
        </div>
      )}
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-1 bg-border-light rounded-full appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${percentage}%, #e2ddd8 ${percentage}%, #e2ddd8 100%)`,
          }}
        />
      </div>
    </div>
  )
}
