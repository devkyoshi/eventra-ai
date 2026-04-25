"""Tests for the Coordinator / Requirements Agent — Member 1.

Implement these tests as part of your agent implementation.
Reference: PROJECT-BOOTSTRAP.md § 7.1 step 6
"""

# TODO: Member 1 — implement tests
# Suggested coverage:
#   - Property-based (Hypothesis): generate random valid EventRequirements dicts
#     → assert validate_requirements round-trips them without errors.
#   - Property-based: generate invalid dicts → assert validator always rejects,
#     never silently passes.
#   - Unit: coordinator_node with mocked LLM returns state.requirements on
#     a well-formed prompt.
#   - Unit: coordinator_node sets clarification_needed when budget/date is absent.
#   - Integration: validate_requirements rejects a past event_date.
#   - Integration: validate_requirements rejects budget_per_head below sanity floor.

import pytest


@pytest.mark.skip(reason="Member 1: implement coordinator tests")
def test_coordinator_placeholder() -> None:
    pass
