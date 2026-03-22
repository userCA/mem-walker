import React from 'react'
import { cn } from '@/lib/cn'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'amber'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', disabled, isLoading, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-150',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
          {
            // Variants
            'bg-text-primary text-white hover:bg-gray-800 active:bg-gray-900': variant === 'primary',
            'bg-white border border-border text-text-primary hover:bg-gray-50 active:bg-gray-100': variant === 'secondary',
            'bg-red-500 text-white hover:bg-red-600 active:bg-red-700': variant === 'danger',
            'bg-transparent hover:bg-gray-100 text-text-secondary hover:text-text-primary': variant === 'ghost',
            'bg-amber text-white hover:bg-amber/90 active:bg-amber/80': variant === 'amber',
          },
          {
            // Sizes
            'px-2.5 py-1.5 text-xs': size === 'sm',
            'px-4 py-2 text-sm': size === 'md',
            'px-6 py-3 text-base': size === 'lg',
          },
          'hover:-translate-y-0.5 hover:shadow-md',
          className
        )}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
