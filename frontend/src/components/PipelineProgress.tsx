import { ClipboardList, MapPin, DollarSign, Mail, Check } from 'lucide-react'
import { cn } from '../lib/utils'

const STEPS = [
  { label: 'Requirements', icon: ClipboardList },
  { label: 'Venues', icon: MapPin },
  { label: 'Budget', icon: DollarSign },
  { label: 'Communications', icon: Mail },
]

interface Props {
  currentStep: number
  isLoading: boolean
}

export function PipelineProgress({ currentStep, isLoading }: Props) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => {
          const stepNum = index + 1
          const isComplete = currentStep > stepNum
          const isActive = currentStep === stepNum && isLoading
          const isDone = currentStep >= stepNum && !isLoading

          const Icon = step.icon

          return (
            <div key={step.label} className="flex flex-1 items-center">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={cn(
                    'flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all duration-300',
                    isComplete || isDone
                      ? 'border-[#0071E3] bg-[#0071E3] text-white'
                      : isActive
                        ? 'border-[#0071E3] bg-[#0071E3]/10 text-[#0071E3]'
                        : 'border-[#D2D2D7] bg-white text-[#86868B]'
                  )}
                >
                  {isComplete || (isDone && stepNum <= currentStep) ? (
                    <Check className="h-4 w-4" />
                  ) : isActive ? (
                    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-[#0071E3]/30 border-t-[#0071E3]" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </div>
                <span
                  className={cn(
                    'text-[11px] font-medium transition-colors',
                    isComplete || isDone
                      ? 'text-[#0071E3]'
                      : isActive
                        ? 'text-[#1D1D1F]'
                        : 'text-[#86868B]'
                  )}
                >
                  {step.label}
                </span>
              </div>

              {index < STEPS.length - 1 && (
                <div
                  className={cn(
                    'mx-2 mb-5 h-px flex-1 transition-all duration-500',
                    isComplete || (isDone && stepNum < currentStep)
                      ? 'bg-[#0071E3]'
                      : 'bg-[#E8E8ED]'
                  )}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
