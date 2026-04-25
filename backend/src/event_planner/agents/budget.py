"""Budget & Scheduling Agent — Member 3.

Computes a deterministic, balanced budget breakdown and generates the
event run-of-show schedule. The LLM only narrates; all arithmetic is
done by deterministic tools.
"""

# TODO: Member 3 — implement this agent
# Reference: PROJECT-BOOTSTRAP.md § 7.3

from event_planner.state.event_state import EventState


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

    Raises:
        NotImplementedError: Until Member 3 implements this agent.
    """
    raise NotImplementedError(
        "budget_node is not yet implemented. "
        "Member 3: see PROJECT-BOOTSTRAP.md § 7.3 for the full implementation guide."
    )
