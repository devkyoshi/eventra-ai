import type React from 'react'
import { ClipboardList, Users, MapPin, Wallet, Calendar, Clock, Tag } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import type { EventRequirements } from '../types/api'

interface Props {
  requirements: EventRequirements
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  tech_meetup: 'Tech Meetup',
  wedding: 'Wedding',
  workshop: 'Workshop',
  conference: 'Conference',
}

function formatLKR(amount: number): string {
  return `LKR ${amount.toLocaleString('en-LK')}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-LK', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function RequirementsCard({ requirements: r }: Props) {
  const fields = [
    { icon: Tag, label: 'Event Type', value: EVENT_TYPE_LABELS[r.event_type] ?? r.event_type },
    { icon: Users, label: 'Attendees', value: `${r.attendee_count.toLocaleString()} guests` },
    { icon: MapPin, label: 'Location', value: r.location },
    { icon: Wallet, label: 'Budget', value: formatLKR(r.budget_lkr) },
    { icon: Calendar, label: 'Date', value: formatDate(r.event_date) },
    { icon: Clock, label: 'Duration', value: `${r.duration_hours} hours` },
  ]

  return (
    <section>
      <SectionLabel icon={ClipboardList} label="Requirements" step={1} />
      <Card>
        <CardHeader>
          <CardTitle className="text-[15px]">Parsed Event Requirements</CardTitle>
          <p className="text-[13px] text-[#6E6E73]">
            Extracted and validated from your request
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {fields.map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex items-start gap-3 rounded-[10px] bg-[#F5F5F7] px-4 py-3">
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#0071E3]/10">
                  <Icon className="h-3.5 w-3.5 text-[#0071E3]" />
                </div>
                <div className="min-w-0">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-[#86868B]">{label}</p>
                  <p className="mt-0.5 text-[14px] font-medium text-[#1D1D1F] truncate">{value}</p>
                </div>
              </div>
            ))}
          </div>

          {r.special_requirements.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-[#86868B]">
                Special Requirements
              </p>
              <div className="flex flex-wrap gap-2">
                {r.special_requirements.map(req => (
                  <Badge key={req} variant="default">
                    {req}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}

export function SectionLabel({
  icon: Icon,
  label,
  step,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  step: number
}) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#0071E3] text-[11px] font-semibold text-white">
        {step}
      </div>
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-[#6E6E73]" />
        <span className="text-[17px] font-semibold text-[#1D1D1F]">{label}</span>
      </div>
    </div>
  )
}
