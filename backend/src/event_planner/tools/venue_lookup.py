"""Venue lookup tool — Member 2.

Queries the local SQLite venue database and returns ranked Venue objects.
All returned venues carry source="venue_db" to prove no hallucination.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path

from event_planner.state.event_state import Venue

logger = logging.getLogger(__name__)

_DB_PATH = Path(
    os.getenv(
        "VENUE_DB_PATH",
        str(Path(__file__).parent.parent.parent.parent / "data" / "venues.db"),
    )
)

_KNOWN_AMENITIES: frozenset[str] = frozenset({
    "projector", "screen", "stage", "av_equipment", "catering", "wifi", "parking",
    "ac", "valet", "breakout_rooms", "sea_view", "beach_access", "outdoor",
    "sound_system", "whiteboard", "bar", "rooftop", "simultaneous_translation",
    "exhibition_hall", "lake_view",
})


class VenueDBError(Exception):
    """SQLite connection or query failure."""


class NoVenuesFoundError(Exception):
    """No venues matched the given constraints."""


def _fit_score(
    capacity_min: int,
    capacity_max: int,
    price_per_day_lkr: int,
    amenities: list[str],
    required_capacity: int,
    max_price_lkr: int,
    required_amenities: list[str],
) -> float:
    """Compute a 0.0–1.0 fit score. Weights: capacity 50%, price 30%, amenities 20%."""
    # Capacity: 1.0 if the attendee count fits, partial credit if slightly over max
    if capacity_min <= required_capacity <= capacity_max:
        cap_score = 1.0
    else:
        overage = abs(required_capacity - capacity_max)
        cap_score = max(0.0, 1.0 - overage / capacity_max)

    # Price: score by remaining budget headroom; cheaper venues score higher.
    if max_price_lkr > 0:
        remaining_budget = max_price_lkr - price_per_day_lkr
        price_score = max(0.0, min(1.0, remaining_budget / max_price_lkr))
    else:
        price_score = 0.0

    # Amenities: fraction of required amenities the venue has
    if required_amenities:
        venue_amenity_set = set(amenities)
        matched = len(set(required_amenities) & venue_amenity_set)
        amenity_score = matched / len(required_amenities)
    else:
        amenity_score = 1.0

    return round(cap_score * 0.5 + price_score * 0.3 + amenity_score * 0.2, 3)


def search_venues(
    capacity: int,
    max_price_lkr: int,
    required_amenities: list[str],
    location: str,
) -> list[Venue]:
    """Search the venue database and return matching venues ranked by fit.

    Filters by capacity range (capacity_min <= capacity <= capacity_max)
    and price (price_per_day_lkr <= max_price_lkr). Location is matched
    as a case-insensitive substring against the venue's location field.

    Ranks results by a weighted score: capacity fit (50%), price headroom
    (30%), and amenity match ratio (20%).

    Args:
        capacity: Required attendee capacity.
        max_price_lkr: Maximum venue price per day in LKR.
        required_amenities: Amenity strings the venue should have (already
            filtered to known venue amenities by the caller).
        location: Location string for filtering (case-insensitive substring).

    Returns:
        List of Venue objects sorted by fit_score descending. Empty list if
        no venues satisfy the hard capacity/price/location constraints.

    Raises:
        VenueDBError: If the database file is missing or the query fails.
    """
    logger.debug(
        "search_venues called | capacity=%d max_price_lkr=%d location=%r amenities=%s db=%s",
        capacity, max_price_lkr, location, required_amenities, _DB_PATH,
    )

    if not _DB_PATH.exists():
        msg = (
            f"Venue database not found at {_DB_PATH}. "
            "Run `python data/seed_db.py` from the backend/ directory."
        )
        logger.error(msg)
        raise VenueDBError(msg)

    logger.debug("opening DB connection to %s", _DB_PATH)
    t_connect = time.monotonic_ns()
    try:
        conn = sqlite3.connect(_DB_PATH)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        logger.error("failed to connect to venue DB: %s", exc)
        raise VenueDBError(f"Cannot open venue database: {exc}") from exc
    connect_ms = (time.monotonic_ns() - t_connect) // 1_000_000
    logger.debug("DB connection opened in %dms", connect_ms)

    location_pattern = f"%{location.lower()}%"
    logger.debug(
        "executing SQL filter | capacity_min<=%d capacity_max>=%d price<=%d location LIKE %r",
        capacity, capacity, max_price_lkr, location_pattern,
    )

    t_query = time.monotonic_ns()
    try:
        rows = conn.execute(
            """
            SELECT id, name, capacity_min, capacity_max, price_per_day_lkr,
                   amenities_json, location, description, latitude, longitude
            FROM venues
            WHERE capacity_min <= ?
              AND capacity_max >= ?
              AND price_per_day_lkr <= ?
              AND LOWER(location) LIKE ?
            """,
            (capacity, capacity, max_price_lkr, location_pattern),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("SQL query failed: %s", exc)
        raise VenueDBError(f"Venue query failed: {exc}") from exc
    finally:
        conn.close()
        logger.debug("DB connection closed")
    query_ms = (time.monotonic_ns() - t_query) // 1_000_000

    logger.info(
        "SQL returned %d row(s) in %dms (capacity=%d, max_price=%d, location=%r)",
        len(rows), query_ms, capacity, max_price_lkr, location,
    )

    if not rows:
        logger.warning(
            "no rows matched — capacity=%d max_price_lkr=%d location=%r. "
            "Consider relaxing budget or broadening location.",
            capacity, max_price_lkr, location,
        )
        return []

    # Score every row and log individual calculations
    scored: list[tuple[Venue, float]] = []
    for row in rows:
        amenities: list[str] = json.loads(row["amenities_json"])

        # Amenity match detail
        matched_amenities = set(required_amenities) & set(amenities)
        missing_amenities = set(required_amenities) - set(amenities)

        score = _fit_score(
            capacity_min=row["capacity_min"],
            capacity_max=row["capacity_max"],
            price_per_day_lkr=row["price_per_day_lkr"],
            amenities=amenities,
            required_capacity=capacity,
            max_price_lkr=max_price_lkr,
            required_amenities=required_amenities,
        )

        cap_ok = row["capacity_min"] <= capacity <= row["capacity_max"]
        logger.debug(
            "scored venue id=%d %r | fit=%.3f | cap_ok=%s (%d–%d) | "
            "price=LKR %d | amenity_match=%d/%d matched=%s missing=%s",
            row["id"], row["name"], score,
            cap_ok, row["capacity_min"], row["capacity_max"],
            row["price_per_day_lkr"],
            len(matched_amenities), len(required_amenities),
            sorted(matched_amenities), sorted(missing_amenities),
        )

        venue = Venue(
            id=row["id"],
            name=row["name"],
            capacity_min=row["capacity_min"],
            capacity_max=row["capacity_max"],
            price_per_day_lkr=row["price_per_day_lkr"],
            amenities=amenities,
            location=row["location"],
            description=row["description"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            fit_score=score,
            source="venue_db",
        )
        scored.append((venue, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    result = [v for v, _ in scored]

    logger.info(
        "ranking complete | top venue: %r fit=%.3f | bottom: %r fit=%.3f",
        result[0].name, result[0].fit_score,
        result[-1].name, result[-1].fit_score,
    )

    return result
