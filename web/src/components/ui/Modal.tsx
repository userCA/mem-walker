import React, { useEffect } from 'react'
import { cn } from '@/lib/cn'

interface ModalProps {
  open?: boolean
  isOpen?: boolean
  onClose: () => void
  children: React.ReactNode
  className?: string
  title?: string
}

export const Modal: React.FC<ModalProps> = ({
  open,
  isOpen,
  onClose,
  children,
  className,
  title,
}) => {
  const isOpenFinal = open ?? isOpen ?? false;
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpenFinal) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpenFinal, onClose])

  if (!isOpenFinal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      {/* Content */}
      <div
        className={cn(
          'relative bg-card rounded-xl shadow-2xl max-w-lg w-full mx-4 max-h-[90vh] overflow-auto',
          className
        )}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-border-light">
            <h2 className="text-lg font-semibold">{title}</h2>
            <button
              onClick={onClose}
              className="text-text-muted hover:text-text-primary transition-colors"
            >
              ✕
            </button>
          </div>
        )}
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}
