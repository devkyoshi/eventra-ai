import { HelpCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'

interface Props {
  questions: string[]
}

export function ClarificationView({ questions }: Props) {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#FF9500]/10">
              <HelpCircle className="h-5 w-5 text-[#C93400]" />
            </div>
            <div>
              <CardTitle className="text-[15px]">A few things to clarify</CardTitle>
              <p className="mt-0.5 text-[13px] text-[#6E6E73]">
                Please provide the following details so we can build your plan.
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3">
            {questions.map((q, i) => (
              <li key={i} className="flex gap-3 text-[14px] text-[#1D1D1F]">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#F5F5F7] text-[11px] font-semibold text-[#6E6E73]">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{q}</span>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    </div>
  )
}
