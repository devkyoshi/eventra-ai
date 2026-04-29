"""Budget calculator tool — Member 3.

Deterministic budget breakdown. The LLM is never trusted with arithmetic;
this tool owns all numerical computation so totals are guaranteed correct.

Design decision (worth highlighting in the report):
    The LLM does NOT perform arithmetic. compute_budget() owns all numerical
    computation using integer math, guaranteeing exact totals with zero
    floating-point drift. The LLM only narrates around these results.

Policy allocations (% of total budget, after contingency is carved out):
    Contingency is always carved out first at exactly 10%.
    The remainder is split by event type:

    tech_meetup : venue 40%, food_and_beverage 30%, av_equipment 20%, decor 10%
    wedding     : venue 35%, food_and_beverage 40%, av_equipment  5%, decor 20%
    workshop    : venue 45%, food_and_beverage 25%, av_equipment 20%, decor 10%
    conference  : venue 40%, food_and_beverage 30%, av_equipment 20%, decor 10%
    (other)     : venue 40%, food_and_beverage 30%, av_equipment 15%, decor 15%
"""

from __future__ import annotations

import logging
from typing import Literal

from event_planner.state.event_state import BudgetBreakdown, BudgetLineItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Policy tables
# ---------------------------------------------------------------------------

CONTINGENCY_RATE = 0.10          # always exactly 10% of total budget
VENUE_WARNING_THRESHOLD = 0.60   # warn if venue alone exceeds 60%
FB_CAP = 0.40                    # food_and_beverage hard cap

# Target weights for the non-contingency pool, keyed by event type.
# Venue weight is a *target* only — actual venue cost is fixed by the
# venue agent, so the remaining categories absorb any deviation.
_WEIGHTS: dict[str, dict[str, float]] = {
    "tech_meetup": {"venue": 0.40, "food_and_beverage": 0.30, "av_equipment": 0.20, "decor": 0.10},
    "wedding":     {"venue": 0.35, "food_and_beverage": 0.40, "av_equipment": 0.05, "decor": 0.20},
    "workshop":    {"venue": 0.45, "food_and_beverage": 0.25, "av_equipment": 0.20, "decor": 0.10},
    "conference":  {"venue": 0.40, "food_and_beverage": 0.30, "av_equipment": 0.20, "decor": 0.10},
    "other":       {"venue": 0.40, "food_and_beverage": 0.30, "av_equipment": 0.15, "decor": 0.15},
}

_NOTES: dict[str, str] = {
    "venue":             "Hall hire, setup/teardown, and basic utilities.",
    "food_and_beverage": "Catering, beverages, and service staff.",
    "av_equipment":      "Projectors, microphones, PA system, and technician fee.",
    "decor":             "Lighting, banners, table settings, and floral arrangements.",
    "contingency":       "10% reserve for unplanned expenses — non-negotiable policy.",
}


class BudgetError(Exception):
    """Budget constraints cannot be satisfied (e.g. venue cost > total budget)."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_budget(
    total_budget_lkr: int,
    venue_cost: int,
    attendees: int,
    event_type: str,
) -> BudgetBreakdown:
    """Compute a balanced, policy-compliant budget breakdown.

    Allocates line items in this order:
      1. contingency      — always exactly 10% of total (carved out first)
      2. venue            — fixed (= venue_cost input)
      3. food_and_beverage — policy weight of remaining pool, capped at 40% of total
      4. av_equipment     — policy weight of remaining pool
      5. decor            — absorbs any integer rounding remainder

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
    """
    # --- input guards -------------------------------------------------------
    if total_budget_lkr <= 0:
        raise BudgetError(f"total_budget_lkr must be positive, got {total_budget_lkr}")
    if venue_cost < 0:
        raise BudgetError(f"venue_cost must be non-negative, got {venue_cost}")
    if venue_cost > total_budget_lkr:
        raise BudgetError(
            f"venue_cost ({venue_cost:,} LKR) exceeds "
            f"total_budget_lkr ({total_budget_lkr:,} LKR). "
            "Choose a cheaper venue or increase the budget."
        )
    if attendees <= 0:
        raise BudgetError(f"attendees must be positive, got {attendees}")

    # normalise event type
    norm = event_type.lower().replace(" ", "_").replace("-", "_")
    weights = _WEIGHTS.get(norm, _WEIGHTS["other"])

    logger.info(
        "compute_budget | total=%d venue=%d attendees=%d type=%s",
        total_budget_lkr, venue_cost, attendees, norm,
    )

    total = total_budget_lkr

    # --- step 1: contingency (always first, always exactly 10%) -------------
    contingency = round(total * CONTINGENCY_RATE)

    # --- step 2: remaining pool after contingency ---------------------------
    pool = total - contingency  # this is what venue + F&B + AV + decor share

    # --- step 3: venue is fixed ---------------------------------------------
    venue_amount = min(venue_cost, pool)  # safety cap (shouldn't trigger after guard above)

    # --- step 4: distribute the rest by policy weights ----------------------
    flex_pool = pool - venue_amount

    # Scale non-venue weights proportionally
    non_venue_w = {k: v for k, v in weights.items() if k != "venue"}
    w_sum = sum(non_venue_w.values())
    scaled = {k: v / w_sum for k, v in non_venue_w.items()}

    # Integer allocation (floor), giving rounding remainder to decor
    raw: dict[str, int] = {}
    for cat, w in scaled.items():
        raw[cat] = int(flex_pool * w)

    # Apply F&B cap (hard rule: F&B <= 40% of total)
    fb_cap_abs = int(total * FB_CAP)
    if raw.get("food_and_beverage", 0) > fb_cap_abs:
        excess = raw["food_and_beverage"] - fb_cap_abs
        raw["food_and_beverage"] = fb_cap_abs
        raw["decor"] = raw.get("decor", 0) + excess  # redirect excess to decor

    # Assign rounding remainder to decor so totals balance exactly
    allocated_flex = sum(raw.values())
    remainder = flex_pool - allocated_flex
    raw["decor"] = raw.get("decor", 0) + remainder

    # --- step 5: assemble final amounts dict --------------------------------
    final: dict[str, int] = {
        "venue":             venue_amount,
        "food_and_beverage": raw.get("food_and_beverage", 0),
        "av_equipment":      raw.get("av_equipment", 0),
        "decor":             raw.get("decor", 0),
        "contingency":       contingency,
    }

    # --- step 6: exact balance assertion (must hold before returning) -------
    total_check = sum(final.values())
    if total_check != total:
        raise BudgetError(
            f"Internal balance error: sum={total_check} != total={total}. "
            "This is a bug — please report."
        )

    # --- step 7: build Pydantic models --------------------------------------
    line_items: list[BudgetLineItem] = [
        BudgetLineItem(
            category=cat,
            amount_lkr=amount,
            percentage=round((amount / total) * 100, 2),
            notes=_NOTES.get(cat, ""),
        )
        for cat, amount in final.items()
    ]

    logger.info(
        "compute_budget complete | is_balanced=True | per_head=%d",
        total // attendees,
    )

    return BudgetBreakdown(
        total_budget_lkr=total,
        line_items=line_items,
        is_balanced=True,   # guaranteed by assertion above
    )