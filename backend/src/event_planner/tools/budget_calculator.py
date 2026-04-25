"""Budget calculator tool — Member 3.

Deterministic budget breakdown. The LLM is never trusted with arithmetic;
this tool owns all numerical computation so totals are guaranteed correct.
"""

# TODO: Member 3 — implement this tool
# Reference: PROJECT-BOOTSTRAP.md § 7.3 step 2

from __future__ import annotations

from event_planner.state.event_state import BudgetBreakdown


class BudgetError(Exception):
    """Budget constraints cannot be satisfied (e.g. venue cost > total budget)."""


def compute_budget(
    total_budget_lkr: int,
    venue_cost: int,
    attendees: int,
    event_type: str,
) -> BudgetBreakdown:
    """Compute a balanced, policy-compliant budget breakdown.

    Allocates line items in this order:
      1. venue        — fixed (= venue_cost input)
      2. food_and_beverage — per-head × attendees, capped at 40% of total
      3. av_equipment — fixed percentage based on event_type
      4. decor        — fixed percentage based on event_type
      5. contingency  — always >= 10% of total; absorbs rounding remainders

    Guarantees:
      sum(line_item.amount_lkr) == total_budget_lkr  (exactly, no floating-point drift)
      contingency >= 0.10 * total_budget_lkr
      BudgetBreakdown.is_balanced == True

    Args:
        total_budget_lkr: Total event budget in LKR.
        venue_cost: Venue price_per_day_lkr (fixed, must be <= total_budget_lkr).
        attendees: Number of expected attendees.
        event_type: One of "tech_meetup", "wedding", "workshop", "conference".

    Returns:
        BudgetBreakdown with balanced line items.

    Raises:
        BudgetError: If venue_cost > total_budget_lkr or constraints cannot be met.
        NotImplementedError: Until Member 3 implements this tool.
    """
    raise NotImplementedError(
        "compute_budget is not yet implemented. "
        "Member 3: see PROJECT-BOOTSTRAP.md § 7.3 step 2."
    )
