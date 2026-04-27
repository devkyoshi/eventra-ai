"""FastAPI server — exposes the coordinator agent as an HTTP API.

Run from the backend/ directory:
    uvicorn api:app --reload

The coordinator agent is fully implemented; the other three agents still raise
NotImplementedError. This server calls coordinator_node directly and appends
realistic mock data for Venue, Budget, and Communications so the frontend can
demonstrate the full four-section pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from event_planner.agents.coordinator import coordinator_node
from event_planner.observability.tracer import get_tracer
from event_planner.state.event_state import (
    BudgetBreakdown,
    BudgetLineItem,
    Communications,
    EventRequirements,
    ScheduleEntry,
    Venue,
    VenueRecommendation,
    WeatherInfo,
)
from event_planner.tools.budget_calculator import compute_budget
from event_planner.tools.schedule_builder import build_schedule

app = FastAPI(title="Eventra AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class PlanRequest(BaseModel):
    user_request: str


# ---------------------------------------------------------------------------
# Mock data builders
# ---------------------------------------------------------------------------

_VENUES = [
    {
        "id": 1,
        "name": "TRACE Expert City Hall",
        "capacity_min": 30,
        "capacity_max": 250,
        "price_per_day_lkr": 120_000,
        "amenities": ["projector", "screen", "wifi", "ac", "catering", "parking"],
        "location": "Maligawatte, Colombo 10",
        "description": "A modern tech-park event space ideal for meetups and conferences.",
    },
    {
        "id": 2,
        "name": "Cinnamon Grand Ballroom",
        "capacity_min": 50,
        "capacity_max": 500,
        "price_per_day_lkr": 180_000,
        "amenities": ["stage", "projector", "wifi", "ac", "catering", "valet_parking", "av_team"],
        "location": "Colombo 3",
        "description": "Elegant five-star ballroom suitable for weddings and large conferences.",
    },
    {
        "id": 3,
        "name": "Hilton Colombo – Lotus Suite",
        "capacity_min": 20,
        "capacity_max": 120,
        "price_per_day_lkr": 85_000,
        "amenities": ["projector", "whiteboard", "wifi", "ac", "catering"],
        "location": "Sir Chittampalam A. Gardiner Mawatha, Colombo 1",
        "description": "Boutique meeting and workshop space in the heart of the CBD.",
    },
]

_SCHEDULE_TEMPLATES: dict[str, list[str]] = {
    "tech_meetup": [
        "Registration & Welcome",
        "Opening Keynote",
        "Talk Session 1",
        "Coffee Break",
        "Talk Session 2",
        "Panel Discussion",
        "Lunch",
        "Workshop / Breakout",
        "Lightning Talks",
        "Networking",
        "Closing Remarks",
    ],
    "wedding": [
        "Guest Arrival",
        "Ceremony",
        "Cocktail Hour",
        "Reception Dinner",
        "First Dance",
        "Speeches & Toasts",
        "Cake Cutting",
        "Entertainment",
        "Dancing",
        "Send-off",
    ],
    "workshop": [
        "Registration",
        "Introduction & Objectives",
        "Module 1",
        "Coffee Break",
        "Module 2",
        "Lunch",
        "Module 3",
        "Hands-on Exercise",
        "Q&A",
        "Wrap-up & Next Steps",
    ],
    "conference": [
        "Registration & Badge Pickup",
        "Opening Address",
        "Keynote Speaker",
        "Session Block A",
        "Coffee Break",
        "Session Block B",
        "Lunch & Networking",
        "Session Block C",
        "Panel Discussion",
        "Sponsor Showcase",
        "Closing Remarks",
        "Networking Reception",
    ],
}


def _fit_score(venue: dict, reqs: EventRequirements) -> float:
    """Heuristic fit score 0–1 based on capacity and budget match."""
    # Capacity score
    cap_ok = venue["capacity_min"] <= reqs.attendee_count <= venue["capacity_max"]
    cap_score = 1.0 if cap_ok else max(0.0, 1.0 - abs(reqs.attendee_count - venue["capacity_max"]) / venue["capacity_max"])

    # Budget score — venue takes ~55% of budget ideally
    ideal_venue_cost = reqs.budget_lkr * 0.55
    price_ratio = min(venue["price_per_day_lkr"], ideal_venue_cost) / max(venue["price_per_day_lkr"], ideal_venue_cost)

    # Amenity bonus
    desired = {"projector", "wifi", "ac", "catering"}
    amenity_score = len(desired & set(venue["amenities"])) / len(desired)

    return round(cap_score * 0.5 + price_ratio * 0.3 + amenity_score * 0.2, 2)


def _build_mock_venues(reqs: EventRequirements) -> list[dict]:
    scored = sorted(
        [(v, _fit_score(v, reqs)) for v in _VENUES],
        key=lambda x: x[1],
        reverse=True,
    )

    weather = WeatherInfo(
        date=reqs.event_date.strftime("%Y-%m-%d"),
        temperature_c=28.5,
        precipitation_probability=15,
        conditions="Partly cloudy",
        is_outdoor_friendly=True,
    )

    results = []
    for rank, (v_dict, score) in enumerate(scored, start=1):
        venue = Venue(
            **v_dict,
            fit_score=score,
            source="venue_db",
        )
        pros = ["Excellent AV setup", "Central location", "Experienced staff"]
        cons = ["Limited parking" if rank > 1 else "Can be busy on weekends"]
        rec = VenueRecommendation(
            venue=venue,
            rank=rank,
            pros=pros[:3],
            cons=cons[:1],
            weather_advisory=(
                "Conditions look ideal for your event date."
                if weather.is_outdoor_friendly
                else "Expect some rain — confirm indoor backup plan."
            ),
        )
        results.append(rec.model_dump(mode="json"))
    return results




def _build_mock_communications(
    reqs: EventRequirements,
    top_venue_name: str = "TBC",
) -> Communications:
    date_str = reqs.event_date.strftime("%B %d, %Y")
    event_label = reqs.event_type.replace("_", " ").title()

    invitation = f"""# {event_label} — You're Invited!

Dear Guest,

We are delighted to invite you to our upcoming **{event_label}** taking place on **{date_str}** at **{top_venue_name}**, {reqs.location}.

**Event Details**
- Date: {date_str}
- Duration: {reqs.duration_hours} hours
- Location: {top_venue_name}, {reqs.location}
- Expected attendees: {reqs.attendee_count}

{"Special arrangements: " + ", ".join(reqs.special_requirements) if reqs.special_requirements else ""}

We look forward to seeing you there. Please RSVP by replying to this email.

Warm regards,
The Eventra Team
"""

    vendor_brief = f"""# Vendor Brief — {event_label}

**Event:** {event_label}
**Date:** {date_str}
**Venue:** {top_venue_name}, {reqs.location}
**Attendees:** {reqs.attendee_count}
**Duration:** {reqs.duration_hours} hours
**Total Budget:** LKR {reqs.budget_lkr:,}

## Scope of Work

Please provide a full-service package covering the following:
1. Venue setup and breakdown
2. Catering for {reqs.attendee_count} guests
3. AV equipment and technical support
{"4. " + ", ".join(reqs.special_requirements) if reqs.special_requirements else ""}

## Budget Allocation

- Venue hire: LKR {int(reqs.budget_lkr * 0.55):,}
- Food & Beverage: LKR {int(reqs.budget_lkr * 0.30):,}
- AV & Equipment: LKR {int(reqs.budget_lkr * 0.08):,}
- Contingency: LKR {reqs.budget_lkr - int(reqs.budget_lkr * 0.55) - int(reqs.budget_lkr * 0.30) - int(reqs.budget_lkr * 0.08):,}

## Deliverables

- Itemised quote within 3 business days
- Confirmation of availability for {date_str}
- Assigned day-of coordinator
"""

    final_plan = f"""# Full Event Plan — {event_label}

## Overview

| Field | Detail |
|-------|--------|
| Event Type | {event_label} |
| Date | {date_str} |
| Duration | {reqs.duration_hours} hours |
| Location | {reqs.location} |
| Venue | {top_venue_name} |
| Attendees | {reqs.attendee_count} |
| Budget | LKR {reqs.budget_lkr:,} |
{"| Special Requirements | " + ", ".join(reqs.special_requirements) + " |" if reqs.special_requirements else ""}

## Recommended Venue

**{top_venue_name}** has been selected as the top venue based on capacity fit and budget alignment.

## Budget Summary

Total: LKR {reqs.budget_lkr:,}
- Venue (55%): LKR {int(reqs.budget_lkr * 0.55):,}
- Food & Beverage (30%): LKR {int(reqs.budget_lkr * 0.30):,}
- AV Equipment (8%): LKR {int(reqs.budget_lkr * 0.08):,}
- Contingency (7%): LKR {reqs.budget_lkr - int(reqs.budget_lkr * 0.55) - int(reqs.budget_lkr * 0.30) - int(reqs.budget_lkr * 0.08):,}

## Next Steps

1. Confirm venue booking at {top_venue_name}
2. Send invitations to {reqs.attendee_count} attendees
3. Finalise catering and AV vendor contracts
4. Confirm day-of run sheet with all vendors
"""

    return Communications(
        invitation_email=invitation,
        vendor_brief=vendor_brief,
        final_plan=final_plan,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/plan")
def plan_event(body: PlanRequest) -> dict:
    trace_id = str(uuid.uuid4())[:8]
    tracer = get_tracer()
    tracer.start_run(trace_id)

    state = {"user_request": body.user_request, "trace_id": trace_id}

    result = coordinator_node(state)  # type: ignore[arg-type]

    if "clarification_needed" in result:
        tracer.end_run()
        return {
            "status": "clarification_needed",
            "clarification_needed": result["clarification_needed"],
        }

    reqs: EventRequirements = result["requirements"]

    venue_options = _build_mock_venues(reqs)
    top_venue_name = venue_options[0]["venue"]["name"] if venue_options else "TBC"

    budget = compute_budget(
        total_budget_lkr=reqs.budget_lkr,
        venue_cost=venue_options[0]["venue"]["price_per_day_lkr"] if venue_options else 0,
        attendees=reqs.attendee_count,
        event_type=reqs.event_type,
    )
    schedule = build_schedule(
        start_time="09:00",
        duration_hours=reqs.duration_hours,
        event_type=reqs.event_type,
    )
    
    communications = _build_mock_communications(reqs, top_venue_name)

    tracer.end_run()

    return {
        "status": "success",
        "trace_id": trace_id,
        "requirements": reqs.model_dump(mode="json"),
        "venue_options": venue_options,
        "budget": budget.model_dump(mode="json"),
        "schedule": [s.model_dump(mode="json") for s in schedule],
        "communications": communications.model_dump(mode="json"),
    }
