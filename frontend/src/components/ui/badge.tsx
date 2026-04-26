import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-[#0071E3]/10 text-[#0071E3]',
        secondary: 'bg-[#F5F5F7] text-[#6E6E73]',
        success: 'bg-[#34C759]/10 text-[#248A3D]',
        warning: 'bg-[#FF9500]/10 text-[#C93400]',
        outline: 'border border-[#D2D2D7] text-[#6E6E73] bg-transparent',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}
