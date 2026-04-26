import { DollarSign, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { SectionLabel } from './RequirementsCard'
import type { BudgetBreakdown, ScheduleEntry } from '../types/api'

interface Props {
  budget: BudgetBreakdown
  schedule: ScheduleEntry[]
}

const CATEGORY_COLORS: Record<string, string> = {
  venue: '#0071E3',
  food_and_beverage: '#34C759',
  av_equipment: '#FF9500',
  decor: '#FF2D55',
  contingency: '#86868B',
}

function formatLKR(amount: number): string {
  return `LKR ${amount.toLocaleString('en-LK')}`
}

export function BudgetSection({ budget, schedule }: Props) {
  return (
    <section>
      <SectionLabel icon={DollarSign} label="Budget & Schedule" step={3} />
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Budget table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-[15px]">Budget Breakdown</CardTitle>
            <p className="text-[13px] text-[#6E6E73]">
              Total: {formatLKR(budget.total_budget_lkr)}
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {budget.line_items.map((item) => {
                const color = CATEGORY_COLORS[item.category] ?? '#6E6E73'
                const label = item.category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                return (
                  <div key={item.category}>
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div
                          className="h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: color }}
                        />
                        <span className="text-[13px] font-medium text-[#1D1D1F] truncate">
                          {label}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-[12px] text-[#6E6E73]">{item.percentage}%</span>
                        <span className="text-[13px] font-semibold text-[#1D1D1F]">
                          {formatLKR(item.amount_lkr)}
                        </span>
                      </div>
                    </div>
                    <div className="h-1 overflow-hidden rounded-full bg-[#E8E8ED]">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${item.percentage}%`, backgroundColor: color }}
                      />
                    </div>
                    {item.notes && (
                      <p className="mt-1 text-[11px] text-[#86868B]">{item.notes}</p>
                    )}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Schedule timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="text-[15px]">Run of Show</CardTitle>
            <p className="text-[13px] text-[#6E6E73]">
              {schedule.length} time slots
            </p>
          </CardHeader>
          <CardContent>
            <div className="relative space-y-0">
              {schedule.map((entry, i) => (
                <div key={i} className="flex gap-3">
                  {/* Timeline line */}
                  <div className="flex flex-col items-center">
                    <div className="h-2 w-2 shrink-0 rounded-full bg-[#0071E3] mt-1.5" />
                    {i < schedule.length - 1 && (
                      <div className="w-px flex-1 bg-[#E8E8ED] my-1" />
                    )}
                  </div>

                  <div className="pb-3 min-w-0 flex-1">
                    <div className="flex items-start gap-2">
                      <div className="flex items-center gap-1 shrink-0">
                        <Clock className="h-3 w-3 text-[#86868B]" />
                        <span className="text-[11px] font-mono text-[#86868B]">
                          {entry.start_time}
                        </span>
                      </div>
                      <span className="text-[13px] font-medium text-[#1D1D1F] leading-snug">
                        {entry.activity}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
