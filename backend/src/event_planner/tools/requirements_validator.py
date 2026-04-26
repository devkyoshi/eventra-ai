"""Requirements validator tool — Member 1.

Validates raw LLM extractions against the EventRequirements Pydantic model
and applies logical business-rule checks beyond mere type validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ValidationError

from event_planner.state.event_state import EventRequirements

# Cutoff date — event_date must be strictly after this.
_CUTOFF = datetime(2026, 4, 26, tzinfo=timezone.utc)

# Minimum LKR per attendee; below this the budget is logically impossible.
_MIN_LKR_PER_HEAD = 500


class MissingFieldError(Exception):
    """A required field was absent from the LLM extraction."""


class LogicalInconsistencyError(Exception):
    """Extracted values are type-valid but logically impossible."""


class ValidationResult(BaseModel):
    ok: bool
    data: Optional[EventRequirements] = None
    errors: list[str] = []


def validate_requirements(raw_extraction: dict) -> ValidationResult:
    """Validate a raw LLM-extracted dict against EventRequirements.

    Runs two passes:
      1. Pydantic structural validation (types, required fields).
      2. Logical checks: budget sanity floor, future date, positive attendees,
         non-empty location.

    Args:
        raw_extraction: The dict produced by the coordinator LLM call.

    Returns:
        ValidationResult with ok=True and populated data on success, or
        ok=False and a list of human-readable error strings on failure.
    """
    # Pass 1 — structural / type validation via Pydantic
    try:
        parsed = EventRequirements.model_validate(raw_extraction)
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        ]
        return ValidationResult(ok=False, errors=errors)

    # Pass 2 — logical business-rule checks
    errors: list[str] = []

    # Future-date check (handle timezone-naive datetimes from the LLM)
    event_dt = (
        parsed.event_date
        if parsed.event_date.tzinfo is not None
        else parsed.event_date.replace(tzinfo=timezone.utc)
    )
    if event_dt <= _CUTOFF:
        errors.append(
            f"event_date must be in the future (after 2026-04-26); got {parsed.event_date.date()}"
        )

    if parsed.attendee_count <= 0:
        errors.append(f"attendee_count must be greater than 0; got {parsed.attendee_count}")

    if parsed.budget_lkr <= 0:
        errors.append(f"budget_lkr must be greater than 0; got {parsed.budget_lkr}")

    if not parsed.location.strip():
        errors.append("location must be a non-empty string")

    if parsed.duration_hours <= 0:
        errors.append(f"duration_hours must be greater than 0; got {parsed.duration_hours}")

    # Budget sanity floor: at least LKR 500 per head
    if parsed.attendee_count > 0 and parsed.budget_lkr > 0:
        per_head = parsed.budget_lkr / parsed.attendee_count
        if per_head < _MIN_LKR_PER_HEAD:
            errors.append(
                f"budget_lkr ({parsed.budget_lkr:,}) is too low for "
                f"{parsed.attendee_count} attendees "
                f"(minimum LKR {_MIN_LKR_PER_HEAD}/head; got LKR {per_head:.0f}/head)"
            )

    if errors:
        return ValidationResult(ok=False, errors=errors)

    return ValidationResult(ok=True, data=parsed)
