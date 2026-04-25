"""Requirements validator tool — Member 1.

Validates raw LLM extractions against the EventRequirements Pydantic model
and applies logical business-rule checks beyond mere type validation.
"""

# TODO: Member 1 — implement this tool
# Reference: PROJECT-BOOTSTRAP.md § 7.1 step 3

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ValidationError

from event_planner.state.event_state import EventRequirements


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

    Raises:
        NotImplementedError: Until Member 1 implements this tool.
    """
    raise NotImplementedError(
        "validate_requirements is not yet implemented. "
        "Member 1: see PROJECT-BOOTSTRAP.md § 7.1 step 3."
    )
