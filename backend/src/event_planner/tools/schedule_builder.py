"""Schedule builder tool — Member 3.

Generates a deterministic run-of-show as 30-minute time blocks.
Event-type-specific block templates ensure appropriate agendas.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from event_planner.state.event_state import ScheduleEntry

logger = logging.getLogger(__name__)


class ScheduleError(Exception):
    """Invalid schedule parameters (e.g. negative duration, bad time format)."""


# Default block templates per event type.
# Each string maps to one 30-minute slot. Slots beyond the template length
# are filled with "Open Networking"; the very last slot is always
# "Venue Clearance / Departure".
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

# Notes to accompany each template activity (optional, keyed by activity name)
_ACTIVITY_NOTES: dict[str, str] = {
    "Registration & Welcome":    "Attendees arrive and collect name badges.",
    "Registration":              "Participants sign in and collect materials.",
    "Guest Arrival":             "Ushers guide guests to their seats.",
    "Opening Remarks":           "Host/organiser opens the event.",
    "Opening Keynote":           "Welcome address and sponsor acknowledgements.",
    "Break":                     "Tea, coffee, and light snacks.",
    "Coffee Break":              "Tea, coffee, and light snacks.",
    "Lunch":                     "Catered lunch.",
    "Networking":                "Informal networking with speakers and attendees.",
    "Networking Reception":      "Post-event drinks and canapés.",
    "Closing":                   "Organiser closing remarks; attendees depart.",
    "Closing Remarks":           "Summary and next steps; attendees depart.",
    "Venue Clearance / Departure": "Guests depart; crew begins teardown.",
    "Open Networking":           "Unstructured networking time.",
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
    """
    # --- validate inputs ----------------------------------------------------
    if duration_hours <= 0:
        raise ScheduleError(f"duration_hours must be > 0, got {duration_hours}")

    try:
        base_dt = datetime.strptime(start_time, "%H:%M")
    except ValueError:
        raise ScheduleError(
            f"start_time must be in HH:MM 24-hour format, got '{start_time}'"
        )

    # normalise event type
    norm = event_type.lower().replace(" ", "_").replace("-", "_")
    template = SCHEDULE_TEMPLATES.get(norm)

    logger.info(
        "build_schedule | start=%s duration=%dh type=%s",
        start_time, duration_hours, norm,
    )

    total_slots = duration_hours * 2   # 30-min blocks
    slot_delta = timedelta(minutes=30)

    entries: list[ScheduleEntry] = []

    for i in range(total_slots):
        slot_start = base_dt + slot_delta * i
        slot_end   = slot_start + slot_delta

        # Determine activity label
        if i == total_slots - 1:
            # Final slot is always a clean close
            activity = "Venue Clearance / Departure"
        elif template is not None and i < len(template):
            activity = template[i]
        elif template is None:
            # Unknown event type — generic labels
            activity = f"Session {i + 1}"
        else:
            # Template exhausted before duration ends
            activity = "Open Networking"

        entries.append(
            ScheduleEntry(
                start_time=slot_start.strftime("%H:%M"),
                end_time=slot_end.strftime("%H:%M"),
                activity=activity,
                notes=_ACTIVITY_NOTES.get(activity),
            )
        )

    logger.info("build_schedule complete | slots=%d", len(entries))
    return entries