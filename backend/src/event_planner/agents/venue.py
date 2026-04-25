"""Venue & Logistics Agent — Member 2.

Searches the local SQLite venue database and fetches Open-Meteo weather
data to produce a ranked list of venue recommendations.
"""

# TODO: Member 2 — implement this agent
# Reference: PROJECT-BOOTSTRAP.md § 7.2

from event_planner.state.event_state import EventState


def venue_node(state: EventState) -> EventState:
    """Search venues and retrieve weather for the chosen event date.

    Reads:
        state["requirements"]  — validated EventRequirements from coordinator

    Writes:
        state["venue_options"]   — list[VenueRecommendation], ranked 1–3
        state["chosen_venue"]    — Venue (= venue_options[0].venue)
        state["weather"]         — WeatherInfo for the event date

    Args:
        state: Current EventState from the LangGraph runtime.

    Returns:
        Updated EventState with venue_options, chosen_venue, and weather set.

    Raises:
        NotImplementedError: Until Member 2 implements this agent.
    """
    raise NotImplementedError(
        "venue_node is not yet implemented. "
        "Member 2: see PROJECT-BOOTSTRAP.md § 7.2 for the full implementation guide."
    )
