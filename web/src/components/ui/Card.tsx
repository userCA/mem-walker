import React from 'react'
import { cn } from '@/lib/cn'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  selected?: boolean
  hoverable?: boolean
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, selected, hoverable = true, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-lg bg-card border border-border-light p-4',
          'transition-all duration-200',
          selected && 'border-amber shadow-amber',
          hoverable && 'cursor-pointer',
          className
        )}
        style={selected ? {
          borderColor: '#f59e0b',
          boxShadow: '0 2px 8px rgba(245, 158, 11, 0.15)',
          background: 'linear-gradient(135deg, #fffbf0 0%, #ffffff 100%)',
        } : undefined}
        {...props}
      >
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'
