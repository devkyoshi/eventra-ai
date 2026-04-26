import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0071E3]/40',
  {
    variants: {
      variant: {
        default:
          'bg-[#0071E3] text-white hover:bg-[#0077ED] active:bg-[#006AD6] rounded-[980px]',
        outline:
          'border border-[#D2D2D7] bg-white text-[#1D1D1F] hover:bg-[#F5F5F7] active:bg-[#E8E8ED] rounded-[10px]',
        ghost:
          'text-[#1D1D1F] hover:bg-[#F5F5F7] active:bg-[#E8E8ED] rounded-[10px]',
        secondary:
          'bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] active:bg-[#D2D2D7] rounded-[10px]',
      },
      size: {
        default: 'h-10 px-6 py-2',
        sm: 'h-8 px-4 text-xs',
        lg: 'h-12 px-8 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
