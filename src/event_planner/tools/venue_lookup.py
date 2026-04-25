"""Venue lookup tool — Member 2.

Queries the local SQLite venue database and returns ranked Venue objects.
All returned venues carry source="venue_db" to prove no hallucination.
"""

# TODO: Member 2 — implement this tool
# Reference: PROJECT-BOOTSTRAP.md § 7.2 step 3

from __future__ import annotations

from event_planner.state.event_state import Venue


class VenueDBError(Exception):
    """SQLite connection or query failure."""


class NoVenuesFoundError(Exception):
    """No venues matched the given constraints."""


def search_venues(
    capacity: int,
    max_price_lkr: int,
    required_amenities: list[str],
    location: str,
) -> list[Venue]:
    """Search the venue database and return matching venues ranked by fit.

    Filters by capacity range (capacity_min <= capacity <= capacity_max)
    and price (price_per_day_lkr <= max_price_lkr). Ranks results by:
      1. Amenity match ratio (required_amenities ∩ venue_amenities)
      2. Price headroom (lower price relative to budget = better)

    Args:
        capacity: Required attendee capacity.
        max_price_lkr: Maximum venue price per day in LKR.
        required_amenities: List of amenity strings the venue must have.
        location: Location string for display/filtering (case-insensitive match).

    Returns:
        List of Venue objects sorted by fit_score descending. May be empty
        if no venues satisfy the hard capacity/price constraints.

    Raises:
        VenueDBError: If the database file is missing or the query fails.
        NotImplementedError: Until Member 2 implements this tool.
    """
    raise NotImplementedError(
        "search_venues is not yet implemented. "
        "Member 2: see PROJECT-BOOTSTRAP.md § 7.2 step 3."
    )
