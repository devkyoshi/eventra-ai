"""Shared state contract for the AI Event Planner multi-agent system.

This file is the single source of truth that all four agents depend on.
Changes here require team review — treat it as a public API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, TypedDict

from pydantic import BaseModel


class EventRequirements(BaseModel):
    event_type: str                  # "tech_meetup", "wedding", "workshop", "conference"
    attendee_count: int
    location: str                    # city/area, e.g. "Colombo"
    budget_lkr: int
    event_date: datetime             # required, future date
    duration_hours: int
    special_requirements: list[str]  # ["projector", "outdoor", "vegetarian"]


class Venue(BaseModel):
    id: int
    name: str
    capacity_min: int
    capacity_max: int
    price_per_day_lkr: int
    amenities: list[str]
    location: str
    description: str
    fit_score: float                 # 0.0 – 1.0, set by venue_lookup
    source: str                      # "venue_db" — proves no hallucination
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WeatherInfo(BaseModel):
    date: str
    temperature_c: float
    precipitation_probability: int   # 0–100
    conditions: str
    is_outdoor_friendly: bool


class VenueRecommendation(BaseModel):
    venue: Venue
    rank: int                        # 1, 2, 3
    pros: list[str]
    cons: list[str]
    weather_advisory: str


class BudgetLineItem(BaseModel):
    category: str                    # "venue", "food_and_beverage", "av_equipment", "decor", "contingency"
    amount_lkr: int
    percentage: float
    notes: str


class BudgetBreakdown(BaseModel):
    total_budget_lkr: int
    line_items: list[BudgetLineItem]
    is_balanced: bool                # True iff sum(line_items) == total_budget_lkr


class ScheduleEntry(BaseModel):
    start_time: str                  # "HH:MM"
    end_time: str                    # "HH:MM"
    activity: str
    notes: Optional[str] = None


class Communications(BaseModel):
    invitation_email: str            # markdown
    vendor_brief: str                # markdown
    final_plan: str                  # markdown — the full consolidated document


class EventState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────────
    user_request: str
    trace_id: str

    # ── Agent 1 (Coordinator) writes ───────────────────────────────────────
    requirements: EventRequirements
    clarification_needed: Optional[list[str]]  # if set, pipeline stops here

    # ── Agent 2 (Venue) writes ─────────────────────────────────────────────
    venue_options: list[VenueRecommendation]
    chosen_venue: Venue                        # always venue_options[0].venue
    weather: WeatherInfo

    # ── Agent 3 (Budget) writes ────────────────────────────────────────────
    budget: BudgetBreakdown
    schedule: list[ScheduleEntry]

    # ── Agent 4 (Communications) writes ───────────────────────────────────
    communications: Communications
    output_files: list[str]                    # absolute paths written to disk
