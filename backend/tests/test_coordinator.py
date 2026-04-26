"""Tests for the Coordinator / Requirements Agent — Member 1."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from event_planner.agents.coordinator import coordinator_node
from event_planner.llm.client import LLMError
from event_planner.state.event_state import EventRequirements
from event_planner.tools.requirements_validator import validate_requirements


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reqs_as_json_dict(reqs: EventRequirements) -> dict:
    """Serialise an EventRequirements to the dict the LLM would return."""
    return reqs.model_dump(mode="json")


# ---------------------------------------------------------------------------
# coordinator_node tests (LLM mocked via conftest mock_llm fixture)
# ---------------------------------------------------------------------------

def test_coordinator_happy_path(mock_llm, sample_requirements):
    """Coordinator returns requirements when LLM produces a valid extraction."""
    mock_llm.return_value = _reqs_as_json_dict(sample_requirements)

    result = coordinator_node({"user_request": "Plan a tech meetup", "trace_id": "t1"})

    assert "requirements" in result
    assert "clarification_needed" not in result
    assert isinstance(result["requirements"], EventRequirements)
    assert result["requirements"].attendee_count == sample_requirements.attendee_count
    assert result["requirements"].location == sample_requirements.location


def test_coordinator_clarification_from_llm(mock_llm):
    """Coordinator propagates clarification questions returned directly by the LLM."""
    questions = ["What is the budget?", "What date?"]
    mock_llm.return_value = {"clarification_needed": questions}

    result = coordinator_node({"user_request": "I want an event", "trace_id": "t2"})

    assert "clarification_needed" in result
    assert result["clarification_needed"] == questions
    assert "requirements" not in result


def test_coordinator_clarification_from_validation(mock_llm):
    """Coordinator converts validation errors into clarification_needed."""
    bad_dict = {
        "event_type": "tech_meetup",
        "attendee_count": 50,
        "location": "Colombo",
        "budget_lkr": 200_000,
        "event_date": "2020-01-01T09:00:00",  # past date
        "duration_hours": 6,
        "special_requirements": [],
    }
    mock_llm.return_value = bad_dict

    result = coordinator_node({"user_request": "some request", "trace_id": "t3"})

    assert "clarification_needed" in result
    assert any("future" in msg.lower() for msg in result["clarification_needed"])


def test_coordinator_llm_error(mock_llm):
    """Coordinator handles LLMError gracefully and returns clarification_needed."""
    mock_llm.side_effect = LLMError("Ollama unreachable")

    result = coordinator_node({"user_request": "Plan an event", "trace_id": "t4"})

    assert "clarification_needed" in result
    assert any("LLM error" in msg for msg in result["clarification_needed"])


# ---------------------------------------------------------------------------
# validate_requirements unit tests
# ---------------------------------------------------------------------------

def test_validate_requirements_valid(sample_requirements):
    result = validate_requirements(_reqs_as_json_dict(sample_requirements))
    assert result.ok is True
    assert result.data is not None
    assert result.data.attendee_count == sample_requirements.attendee_count


def test_validate_requirements_past_date():
    data = {
        "event_type": "tech_meetup",
        "attendee_count": 50,
        "location": "Colombo",
        "budget_lkr": 100_000,
        "event_date": "2025-01-01T09:00:00",
        "duration_hours": 6,
        "special_requirements": [],
    }
    result = validate_requirements(data)
    assert result.ok is False
    assert any("future" in err.lower() for err in result.errors)


def test_validate_requirements_negative_attendees():
    data = {
        "event_type": "workshop",
        "attendee_count": -5,
        "location": "Kandy",
        "budget_lkr": 50_000,
        "event_date": "2026-09-01T09:00:00",
        "duration_hours": 4,
        "special_requirements": [],
    }
    result = validate_requirements(data)
    assert result.ok is False
    assert any("attendee_count" in err for err in result.errors)


def test_validate_requirements_budget_too_low():
    """LKR 1 000 for 100 people = LKR 10/head, below the LKR 500/head floor."""
    data = {
        "event_type": "conference",
        "attendee_count": 100,
        "location": "Colombo",
        "budget_lkr": 1_000,
        "event_date": "2026-09-15T09:00:00",
        "duration_hours": 8,
        "special_requirements": [],
    }
    result = validate_requirements(data)
    assert result.ok is False
    assert any("too low" in err.lower() or "500" in err for err in result.errors)


def test_validate_requirements_empty_location():
    data = {
        "event_type": "wedding",
        "attendee_count": 80,
        "location": "   ",
        "budget_lkr": 500_000,
        "event_date": "2026-12-20T10:00:00",
        "duration_hours": 10,
        "special_requirements": ["catering"],
    }
    result = validate_requirements(data)
    assert result.ok is False
    assert any("location" in err for err in result.errors)


def test_validate_requirements_zero_duration():
    data = {
        "event_type": "workshop",
        "attendee_count": 20,
        "location": "Galle",
        "budget_lkr": 30_000,
        "event_date": "2026-08-10T09:00:00",
        "duration_hours": 0,
        "special_requirements": [],
    }
    result = validate_requirements(data)
    assert result.ok is False
    assert any("duration_hours" in err for err in result.errors)


def test_validate_requirements_missing_required_field():
    """Pydantic should reject a dict missing attendee_count."""
    data = {
        "event_type": "tech_meetup",
        "location": "Colombo",
        "budget_lkr": 100_000,
        "event_date": "2026-07-01T09:00:00",
        "duration_hours": 6,
        "special_requirements": [],
        # attendee_count intentionally omitted
    }
    result = validate_requirements(data)
    assert result.ok is False


# ---------------------------------------------------------------------------
# Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------

_FUTURE_MIN = datetime(2026, 4, 27, tzinfo=timezone.utc)
_FUTURE_MAX = datetime(2030, 12, 31, tzinfo=timezone.utc)

_VALID_EVENT_TYPES = ["tech_meetup", "wedding", "workshop", "conference"]


@settings(max_examples=50)
@given(
    event_type=st.sampled_from(_VALID_EVENT_TYPES),
    attendee_count=st.integers(min_value=1, max_value=2000),
    location=st.text(min_size=1, max_size=60).filter(lambda s: s.strip() != ""),
    event_date=st.datetimes(
        min_value=_FUTURE_MIN.replace(tzinfo=None),
        max_value=_FUTURE_MAX.replace(tzinfo=None),
    ),
    duration_hours=st.integers(min_value=1, max_value=24),
    special_requirements=st.lists(st.text(max_size=30), max_size=5),
)
def test_property_valid_requirements_always_pass(
    event_type,
    attendee_count,
    location,
    event_date,
    duration_hours,
    special_requirements,
):
    """Any structurally valid EventRequirements (with sensible budget) must pass."""
    budget_lkr = attendee_count * 1_000  # always above the 500/head floor
    assume(budget_lkr > 0)

    data = {
        "event_type": event_type,
        "attendee_count": attendee_count,
        "location": location,
        "budget_lkr": budget_lkr,
        "event_date": event_date.isoformat(),
        "duration_hours": duration_hours,
        "special_requirements": special_requirements,
    }
    result = validate_requirements(data)
    assert result.ok is True, f"Unexpected failure for valid data: {result.errors}"
    assert result.data is not None
