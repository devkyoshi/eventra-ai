"""Schedule builder tool — Member 3.

Generates a deterministic run-of-show as 30-minute time blocks.
Event-type-specific block templates ensure appropriate agendas.
"""

# TODO: Member 3 — implement this tool
# Reference: PROJECT-BOOTSTRAP.md § 7.3 step 3

from __future__ import annotations

from event_planner.state.event_state import ScheduleEntry


class ScheduleError(Exception):
    """Invalid schedule parameters (e.g. negative duration, bad time format)."""


# Default block templates per event type.
# Member 3 may extend or replace these — they exist here to document intent.
SCHEDULE_TEMPLATES: dict[str, list[str]] = {
    "tech_meetup": [
        "Registration & Welcome",
        "Opening Remarks",
        "Keynote Talk",
        "Talk Session 1",
        "Break",
        "Talk Session 2",
        "Panel Discussion",
        "Networking",
        "Closing",
    ],
    "wedding": [
        "Guest Arrival",
        "Ceremony",
        "Cocktail Hour",
        "Reception Dinner",
        "Speeches & Toasts",
        "Cake Cutting",
        "Dancing",
        "Farewell",
    ],
    "workshop": [
        "Registration",
        "Introduction & Objectives",
        "Module 1",
        "Break",
        "Module 2",
        "Lunch",
        "Module 3",
        "Q&A",
        "Wrap-up",
    ],
    "conference": [
        "Registration",
        "Opening Keynote",
        "Session 1",
        "Coffee Break",
        "Session 2",
        "Lunch",
        "Session 3",
        "Coffee Break",
        "Session 4",
        "Closing Remarks",
        "Networking Reception",
    ],
}


def build_schedule(
    start_time: str,
    duration_hours: int,
    event_type: str,
) -> list[ScheduleEntry]:
    """Generate a chronological run-of-show for the event.

    Divides the event duration into 30-minute blocks and maps them to
    appropriate activities from SCHEDULE_TEMPLATES. If the event type is
    not in the template dict, falls back to generic "Session N" labels.

    Args:
        start_time: Event start time in "HH:MM" 24-hour format.
        duration_hours: Total event duration in hours (must be > 0).
        event_type: One of the keys in SCHEDULE_TEMPLATES, or any string.

    Returns:
        List of ScheduleEntry objects in chronological order with no gaps
        or overlaps. Total span equals exactly duration_hours.

    Raises:
        ScheduleError: If start_time is malformed or duration_hours <= 0.
        NotImplementedError: Until Member 3 implements this tool.
    """
    raise NotImplementedError(
        "build_schedule is not yet implemented. "
        "Member 3: see PROJECT-BOOTSTRAP.md § 7.3 step 3."
    )
