import React from 'react'
import { cn } from '@/lib/cn'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode
  error?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, icon, error, ...props }, ref) => {
    return (
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
            {icon}
          </span>
        )}
        <input
          ref={ref}
          className={cn(
            'w-full rounded-lg border bg-card px-3 py-2 text-sm',
            'placeholder:text-text-muted',
            'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'transition-all duration-150',
            icon && 'pl-10',
            error ? 'border-red-500 focus:ring-red-500' : 'border-border hover:border-gray-400',
            className
          )}
          {...props}
        />
      </div>
    )
  }
)

Input.displayName = 'Input'
