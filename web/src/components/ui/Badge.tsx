import React from 'react'
import { cn } from '@/lib/cn'

type BadgeVariant = 'default' | 'secondary' | 'work' | 'personal' | 'project' | 'study'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-700',
  secondary: 'bg-gray-100 text-gray-700',
  work: 'bg-category-work text-green-800',
  personal: 'bg-category-personal text-pink-800',
  project: 'bg-category-project text-blue-800',
  study: 'bg-category-study text-green-800',
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  ...props
}) => {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
}
