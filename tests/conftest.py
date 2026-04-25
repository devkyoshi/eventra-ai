"""Shared pytest fixtures for the AI Event Planner test suite."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

import pytest

from event_planner.state.event_state import (
    BudgetBreakdown,
    BudgetLineItem,
    Communications,
    EventRequirements,
    EventState,
    ScheduleEntry,
    Venue,
    VenueRecommendation,
    WeatherInfo,
)


@pytest.fixture
def sample_requirements() -> EventRequirements:
    return EventRequirements(
        event_type="tech_meetup",
        attendee_count=50,
        location="Colombo",
        budget_lkr=200_000,
        event_date=datetime(2026, 5, 15, 9, 0, tzinfo=timezone.utc),
        duration_hours=6,
        special_requirements=["projector", "wifi"],
    )


@pytest.fixture
def sample_venue() -> Venue:
    return Venue(
        id=10,
        name="TRACE Expert City Hall",
        capacity_min=30,
        capacity_max=250,
        price_per_day_lkr=150_000,
        amenities=["projector", "screen", "wifi", "ac", "catering", "parking"],
        location="Maligawatte, Colombo 10",
        description="Modern tech-park event space.",
        fit_score=0.92,
        source="venue_db",
    )


@pytest.fixture
def sample_weather() -> WeatherInfo:
    return WeatherInfo(
        date="2026-05-15",
        temperature_c=28.0,
        precipitation_probability=10,
        conditions="Partly cloudy",
        is_outdoor_friendly=True,
    )


@pytest.fixture
def sample_venue_recommendation(
    sample_venue: Venue, sample_weather: WeatherInfo
) -> VenueRecommendation:
    return VenueRecommendation(
        venue=sample_venue,
        rank=1,
        pros=["Great AV setup", "Central location", "Tech-community atmosphere"],
        cons=["Limited parking", "No outdoor space"],
        weather_advisory="Conditions look fine for an indoor event.",
    )


@pytest.fixture
def sample_budget() -> BudgetBreakdown:
    return BudgetBreakdown(
        total_budget_lkr=200_000,
        line_items=[
            BudgetLineItem(
                category="venue",
                amount_lkr=150_000,
                percentage=75.0,
                notes="TRACE Expert City Hall day rate",
            ),
            BudgetLineItem(
                category="food_and_beverage",
                amount_lkr=20_000,
                percentage=10.0,
                notes="LKR 400/head × 50 attendees",
            ),
            BudgetLineItem(
                category="av_equipment",
                amount_lkr=10_000,
                percentage=5.0,
                notes="Projector and mics",
            ),
            BudgetLineItem(
                category="decor",
                amount_lkr=0,
                percentage=0.0,
                notes="No decor budget for tech meetup",
            ),
            BudgetLineItem(
                category="contingency",
                amount_lkr=20_000,
                percentage=10.0,
                notes="10% contingency reserve",
            ),
        ],
        is_balanced=True,
    )


@pytest.fixture
def sample_schedule() -> list[ScheduleEntry]:
    return [
        ScheduleEntry(start_time="09:00", end_time="09:30", activity="Registration & Welcome"),
        ScheduleEntry(start_time="09:30", end_time="10:00", activity="Opening Remarks"),
        ScheduleEntry(start_time="10:00", end_time="11:00", activity="Keynote Talk"),
        ScheduleEntry(start_time="11:00", end_time="12:00", activity="Talk Session 1"),
        ScheduleEntry(start_time="12:00", end_time="13:00", activity="Lunch Break"),
        ScheduleEntry(start_time="13:00", end_time="14:00", activity="Talk Session 2"),
        ScheduleEntry(start_time="14:00", end_time="15:00", activity="Networking"),
    ]


@pytest.fixture
def sample_communications() -> Communications:
    return Communications(
        invitation_email="# Tech Meetup Invitation\n\nYou are invited...",
        vendor_brief="# Vendor Brief\n\nBudget: LKR 200,000...",
        final_plan="# Full Event Plan\n\n## Requirements\n...",
    )


@pytest.fixture
def sample_state(
    sample_requirements: EventRequirements,
    sample_venue: Venue,
    sample_weather: WeatherInfo,
    sample_venue_recommendation: VenueRecommendation,
    sample_budget: BudgetBreakdown,
    sample_schedule: list[ScheduleEntry],
    sample_communications: Communications,
) -> EventState:
    return EventState(
        user_request="Plan a 50-person tech meetup in Colombo with LKR 200,000 on May 15, 2026",
        trace_id="test-trace-001",
        requirements=sample_requirements,
        clarification_needed=None,
        venue_options=[sample_venue_recommendation],
        chosen_venue=sample_venue,
        weather=sample_weather,
        budget=sample_budget,
        schedule=sample_schedule,
        communications=sample_communications,
        output_files=[],
    )


@pytest.fixture
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> Callable:
    """Replace get_llm_response with a configurable mock.

    Usage in tests:
        def test_something(mock_llm):
            mock_llm.return_value = {"event_type": "tech_meetup", ...}
    """
    mock = MagicMock(return_value={})
    monkeypatch.setattr("event_planner.llm.client.get_llm_response", mock)
    return mock


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for file output tests."""
    out = tmp_path / "output"
    out.mkdir()
    return out
