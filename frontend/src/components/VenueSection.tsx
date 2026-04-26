import { MapPin, Users, Star, CheckCircle2, XCircle, CloudSun } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { SectionLabel } from './RequirementsCard'
import type { VenueRecommendation } from '../types/api'

interface Props {
  venues: VenueRecommendation[]
}

function formatLKR(amount: number): string {
  return `LKR ${amount.toLocaleString('en-LK')}`
}

export function VenueSection({ venues }: Props) {
  return (
    <section>
      <SectionLabel icon={MapPin} label="Venue Recommendations" step={2} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {venues.map((rec) => (
          <VenueCard key={rec.venue.id} rec={rec} />
        ))}
      </div>
    </section>
  )
}

function VenueCard({ rec }: { rec: VenueRecommendation }) {
  const { venue, rank, pros, cons, weather_advisory } = rec
  const isTop = rank === 1

  return (
    <Card className={isTop ? 'ring-2 ring-[#0071E3] ring-offset-1' : ''}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <CardTitle className="text-[14px] leading-snug">{venue.name}</CardTitle>
            <CardDescription className="mt-0.5 flex items-center gap-1 text-[12px]">
              <MapPin className="h-3 w-3 shrink-0" />
              {venue.location}
            </CardDescription>
          </div>
          {isTop && (
            <Badge variant="default" className="shrink-0 text-[10px]">
              <Star className="mr-1 h-2.5 w-2.5" />
              Top Pick
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Fit score */}
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-[11px] font-medium uppercase tracking-wide text-[#86868B]">
              Fit Score
            </span>
            <span className="text-[13px] font-semibold text-[#1D1D1F]">
              {Math.round(venue.fit_score * 100)}%
            </span>
          </div>
          <Progress value={venue.fit_score * 100} />
        </div>

        {/* Capacity & price */}
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-[8px] bg-[#F5F5F7] px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-[#86868B]">Capacity</p>
            <div className="mt-0.5 flex items-center gap-1 text-[12px] font-medium text-[#1D1D1F]">
              <Users className="h-3 w-3 text-[#6E6E73]" />
              {venue.capacity_min}–{venue.capacity_max}
            </div>
          </div>
          <div className="rounded-[8px] bg-[#F5F5F7] px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-[#86868B]">Day Rate</p>
            <p className="mt-0.5 text-[12px] font-medium text-[#1D1D1F]">
              {formatLKR(venue.price_per_day_lkr)}
            </p>
          </div>
        </div>

        {/* Pros */}
        {pros.length > 0 && (
          <div className="space-y-1.5">
            {pros.slice(0, 3).map((pro) => (
              <div key={pro} className="flex items-start gap-2 text-[12px] text-[#1D1D1F]">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#34C759]" />
                {pro}
              </div>
            ))}
          </div>
        )}

        {/* Cons */}
        {cons.length > 0 && (
          <div className="space-y-1.5">
            {cons.slice(0, 2).map((con) => (
              <div key={con} className="flex items-start gap-2 text-[12px] text-[#6E6E73]">
                <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#86868B]" />
                {con}
              </div>
            ))}
          </div>
        )}

        {/* Weather */}
        <div className="flex items-start gap-2 rounded-[8px] bg-[#F5F5F7] px-3 py-2">
          <CloudSun className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#FF9500]" />
          <p className="text-[11px] text-[#6E6E73] leading-snug">{weather_advisory}</p>
        </div>

        {/* Amenities */}
        <div className="flex flex-wrap gap-1.5">
          {venue.amenities.slice(0, 5).map((a) => (
            <Badge key={a} variant="secondary" className="text-[10px]">
              {a.replace(/_/g, ' ')}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
