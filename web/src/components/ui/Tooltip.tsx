import React, { useState } from 'react'
import { cn } from '@/lib/cn'

interface TooltipProps {
  content: string
  children: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  className,
}) => {
  const [isVisible, setIsVisible] = useState(false)

  const positionStyles = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  return (
    <div
      className={cn('relative inline-block', className)}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          className={cn(
            'absolute z-50 px-2 py-1 text-xs text-white bg-text-primary rounded whitespace-nowrap',
            'opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200',
            positionStyles[position]
          )}
        >
          {content}
        </div>
      )}
    </div>
  )
}

// Simpler version without group dependency
export const SimpleTooltip: React.FC<TooltipProps> = ({
  content,
  children,
  className,
}) => {
  const [visible, setVisible] = React.useState(false)

  return (
    <div
      className={cn('relative inline-block', className)}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-text-primary rounded whitespace-nowrap z-50">
          {content}
        </div>
      )}
    </div>
  )
}
