"""Tests for the Budget & Scheduling Agent — Member 3.

Implement these tests as part of your agent implementation.
Reference: PROJECT-BOOTSTRAP.md § 7.3 step 5

This is the strongest property-based test suite in the project — the
deterministic nature of budget_calculator makes Hypothesis very effective here.
"""

# TODO: Member 3 — implement tests
# Required property-based invariants (Hypothesis):
#   1. sum(line_item.amount_lkr) == total_budget_lkr  (exact equality, no drift)
#   2. No category exceeds its policy cap (F&B <= 40%, contingency >= 10%)
#   3. sum(line_item.percentage) == 100.0  (within 0.01 tolerance)
#   4. BudgetBreakdown.is_balanced == True for all valid inputs
#   5. build_schedule returns no overlapping time blocks
#   6. build_schedule total span == duration_hours

import pytest


@pytest.mark.skip(reason="Member 3: implement budget tests")
def test_budget_placeholder() -> None:
    pass
