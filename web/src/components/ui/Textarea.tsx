import React from 'react'
import { cn } from '@/lib/cn'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          'w-full rounded-lg border bg-card px-3 py-2 text-sm',
          'placeholder:text-text-muted',
          'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'resize-y min-h-[80px]',
          'transition-all duration-150',
          error ? 'border-red-500' : 'border-border hover:border-gray-400',
          className
        )}
        {...props}
      />
    )
  }
)

Textarea.displayName = 'Textarea'
