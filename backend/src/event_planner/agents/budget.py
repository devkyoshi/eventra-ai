"""Budget & Scheduling Agent — Member 3.

Computes a deterministic, balanced budget breakdown and generates the
event run-of-show schedule. The LLM only narrates; all arithmetic is
done by deterministic tools.
"""

from __future__ import annotations

import logging
import time

from event_planner.llm.llm import LLMError, get_llm_response
from event_planner.prompts.budget_prompt import BUDGET_SYSTEM_PROMPT
from event_planner.state.event_state import EventState
from event_planner.tools.budget_calculator import BudgetError, compute_budget
from event_planner.tools.schedule_builder import ScheduleError, build_schedule

logger = logging.getLogger(__name__)

_DEFAULT_START_TIME = "09:00"

from event_planner.llm.llm import LLMError, get_llm_response



# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------

def budget_node(state: EventState) -> EventState:
    """Compute budget and build the event schedule.

    Reads:
        state["requirements"]   — validated EventRequirements
        state["chosen_venue"]   — Venue with price_per_day_lkr

    Writes:
        state["budget"]    — BudgetBreakdown (line items sum == total)
        state["schedule"]  — list[ScheduleEntry] in chronological order

    Args:
        state: Current EventState from the LangGraph runtime.

    Returns:
        Updated EventState with budget and schedule set.
    """
    t0 = time.time()
    trace_id = state.get("trace_id", "n/a")
    logger.info("BudgetAgent | start | trace_id=%s", trace_id)

    requirements = state["requirements"]
    chosen_venue  = state["chosen_venue"]

    # ------------------------------------------------------------------
    # Tool 1: compute_budget  (deterministic — no LLM arithmetic)
    # ------------------------------------------------------------------
    try:
        breakdown = compute_budget(
            total_budget_lkr=requirements.budget_lkr,
            venue_cost=chosen_venue.price_per_day_lkr,
            attendees=requirements.attendee_count,
            event_type=requirements.event_type,
        )
    except BudgetError as exc:
        logger.error("BudgetAgent | compute_budget failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # Tool 2: build_schedule  (deterministic — pure Python)
    # ------------------------------------------------------------------
    # Extract start time from special_requirements if provided
    # e.g. special_requirements may include "start_time:14:00"
    start_time = _DEFAULT_START_TIME
    for req in (requirements.special_requirements or []):
        if isinstance(req, str) and req.startswith("start_time:"):
            start_time = req.split(":", 1)[1].strip()
            break

    try:
        schedule = build_schedule(
            start_time=start_time,
            duration_hours=requirements.duration_hours,
            event_type=requirements.event_type,
        )
    except ScheduleError as exc:
        logger.error("BudgetAgent | build_schedule failed: %s", exc)
        raise

    # ------------------------------------------------------------------
    # LLM narration — wraps tool outputs; does NO arithmetic itself
    # ------------------------------------------------------------------
    budget_lines = "\n".join(
        f"  {item.category}: LKR {item.amount_lkr:,} ({item.percentage:.1f}%)"
        for item in breakdown.line_items
    )
    schedule_lines = "\n".join(
        f"  {e.start_time}–{e.end_time}: {e.activity}"
        for e in schedule
    )
    per_head = breakdown.total_budget_lkr // requirements.attendee_count

    narration_prompt = (
        f"Event: {requirements.event_type.replace('_', ' ').title()}\n"
        f"Venue: {chosen_venue.name}, {chosen_venue.location}\n"
        f"Attendees: {requirements.attendee_count}  |  Per-head: LKR {per_head:,}\n"
        f"Total budget: LKR {breakdown.total_budget_lkr:,}\n\n"
        f"Budget breakdown (exact — do not alter):\n{budget_lines}\n\n"
        f"Run-of-show (exact — do not alter):\n{schedule_lines}\n\n"
        "Write a 3–4 sentence professional summary of the budget strategy and "
        "how the schedule supports the event goals."
    )

    try:
        narration = get_llm_response(
            system_prompt=BUDGET_SYSTEM_PROMPT,
            user_prompt=narration_prompt,
            json_mode=False,   # narration is plain prose, not JSON
        )
        logger.info("BudgetAgent | narration complete | %d chars", len(narration))
    except LLMError as exc:
        narration = "(LLM narration unavailable.)"
        logger.warning("BudgetAgent | narration skipped: %s", exc)

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info("BudgetAgent | done | elapsed_ms=%d", elapsed_ms)

    # Return only the keys this agent owns (LangGraph merges into state)
    return {
        **state,
        "budget":   breakdown,
        "schedule": schedule,
    }