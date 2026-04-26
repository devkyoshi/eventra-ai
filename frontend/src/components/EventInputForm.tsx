import { useState, type KeyboardEvent } from 'react'
import { Button } from './ui/button'
import { Sparkles } from 'lucide-react'

interface Props {
  onSubmit: (text: string) => void
  isLoading: boolean
}

const EXAMPLE_PROMPTS = [
  'Plan a 50-person tech meetup in Colombo on 2026-08-15 with a LKR 250,000 budget',
  'Organise a 120-person conference in Kandy on 2026-10-05 with LKR 600,000 budget',
  'Plan a wedding reception for 80 guests in Colombo on 2027-02-14 with LKR 1,200,000',
]

export function EventInputForm({ onSubmit, isLoading }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (trimmed) onSubmit(trimmed)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl space-y-4">
      <div className="relative">
        <textarea
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your event — type, location, date, number of guests, budget…"
          disabled={isLoading}
          rows={4}
          className="w-full resize-none rounded-[14px] border border-[#D2D2D7] bg-white px-5 py-4 text-[15px] text-[#1D1D1F] placeholder:text-[#86868B] transition-all duration-200 focus:border-[#0071E3] focus:outline-none focus:ring-4 focus:ring-[#0071E3]/12 disabled:opacity-60"
        />
        <div className="absolute bottom-3 right-3 text-[11px] text-[#86868B]">
          ⌘↵ to submit
        </div>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={isLoading || !value.trim()}
        size="lg"
        className="w-full"
      >
        {isLoading ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            Planning your event…
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            Plan My Event
          </>
        )}
      </Button>

      {!isLoading && !value && (
        <div className="space-y-2">
          <p className="text-center text-[12px] text-[#86868B] font-medium uppercase tracking-wide">
            Try an example
          </p>
          <div className="space-y-1.5">
            {EXAMPLE_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                onClick={() => setValue(prompt)}
                className="block w-full rounded-[10px] bg-[#F5F5F7] px-4 py-2.5 text-left text-[13px] text-[#6E6E73] transition-colors hover:bg-[#EAEAEC] hover:text-[#1D1D1F]"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
