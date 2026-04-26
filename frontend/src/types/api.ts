export interface EventRequirements {
  event_type: 'tech_meetup' | 'wedding' | 'workshop' | 'conference'
  attendee_count: number
  location: string
  budget_lkr: number
  event_date: string
  duration_hours: number
  special_requirements: string[]
}

export interface Venue {
  id: number
  name: string
  capacity_min: number
  capacity_max: number
  price_per_day_lkr: number
  amenities: string[]
  location: string
  description: string
  fit_score: number
  source: string
}

export interface VenueRecommendation {
  venue: Venue
  rank: number
  pros: string[]
  cons: string[]
  weather_advisory: string
}

export interface BudgetLineItem {
  category: string
  amount_lkr: number
  percentage: number
  notes: string
}

export interface BudgetBreakdown {
  total_budget_lkr: number
  line_items: BudgetLineItem[]
  is_balanced: boolean
}

export interface ScheduleEntry {
  start_time: string
  end_time: string
  activity: string
  notes?: string
}

export interface Communications {
  invitation_email: string
  vendor_brief: string
  final_plan: string
}

export interface PlanResponse {
  status: 'success' | 'clarification_needed'
  trace_id?: string
  clarification_needed?: string[]
  requirements?: EventRequirements
  venue_options?: VenueRecommendation[]
  budget?: BudgetBreakdown
  schedule?: ScheduleEntry[]
  communications?: Communications
}
