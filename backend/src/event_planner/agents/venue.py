"""Venue & Logistics Agent — Member 2.

Searches the local SQLite venue database and fetches Open-Meteo weather
data to produce a ranked list of venue recommendations.
"""

from __future__ import annotations

import json
import logging
import time

import event_planner.llm.client as llm_client
from event_planner.llm.client import LLMError
from event_planner.observability.tracer import get_tracer
from event_planner.prompts.venue_prompt import VENUE_SYSTEM_PROMPT
from event_planner.state.event_state import (
    EventRequirements,
    EventState,
    VenueRecommendation,
    WeatherInfo,
)
from event_planner.tools.venue_lookup import (
    NoVenuesFoundError,
    VenueDBError,
    _KNOWN_AMENITIES,
    search_venues,
)
from event_planner.tools.weather_check import WeatherAPIError, get_weather_forecast

logger = logging.getLogger(__name__)

# Venue is allowed up to this fraction of the total budget when searching.
# Generous ceiling so we don't exclude good venues that are slightly over 55%.
_VENUE_BUDGET_FRACTION = 0.60


def venue_node(state: EventState) -> dict:
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
        Partial state dict with venue_options, chosen_venue, and weather set.

    Raises:
        VenueDBError: If the SQLite database is missing or unreadable.
        NoVenuesFoundError: If no venues match the requirements.
    """
    agent_start_ns = time.monotonic_ns()
    tracer = get_tracer()
    reqs: EventRequirements = state["requirements"]

    logger.info(
        "venue_node starting | event_type=%s location=%s attendees=%d budget_lkr=%d",
        reqs.event_type, reqs.location, reqs.attendee_count, reqs.budget_lkr,
    )

    tracer.log(
        agent="venue",
        event_type="agent_start",
        inputs={
            "event_type": reqs.event_type,
            "location": reqs.location,
            "attendee_count": reqs.attendee_count,
            "budget_lkr": reqs.budget_lkr,
            "event_date": reqs.event_date.isoformat(),
            "duration_hours": reqs.duration_hours,
            "special_requirements": reqs.special_requirements,
        },
    )

    # ── Derive search parameters ──────────────────────────────────────────────
    all_special = reqs.special_requirements
    required_amenities = [s for s in all_special if s in _KNOWN_AMENITIES]
    catering_requirements = [s for s in all_special if s not in _KNOWN_AMENITIES]
    max_price = int(reqs.budget_lkr * _VENUE_BUDGET_FRACTION)

    logger.debug(
        "search parameters | max_price_lkr=%d (%.0f%% of %d) "
        "required_amenities=%s catering_requirements=%s",
        max_price, _VENUE_BUDGET_FRACTION * 100, reqs.budget_lkr,
        required_amenities, catering_requirements,
    )

    if catering_requirements:
        logger.info(
            "special requirements %s are catering concerns, not venue filters — "
            "they will be passed to the budget/communications agent",
            catering_requirements,
        )

    tracer.log(
        agent="venue",
        event_type="tool_call",
        tool_called="derive_search_params",
        inputs={"special_requirements": all_special},
        outputs={
            "max_price_lkr": max_price,
            "venue_budget_fraction": _VENUE_BUDGET_FRACTION,
            "required_amenities": required_amenities,
            "catering_requirements_excluded": catering_requirements,
        },
    )

    # ── Tool: search_venues ───────────────────────────────────────────────────
    logger.info(
        "searching venue DB | capacity=%d max_price_lkr=%d location=%r amenities=%s",
        reqs.attendee_count, max_price, reqs.location, required_amenities,
    )

    t0 = time.monotonic_ns()
    try:
        venues = search_venues(
            capacity=reqs.attendee_count,
            max_price_lkr=max_price,
            required_amenities=required_amenities,
            location=reqs.location,
        )
    except VenueDBError as exc:
        elapsed_ms = (time.monotonic_ns() - t0) // 1_000_000
        logger.error("venue DB query failed after %dms: %s", elapsed_ms, exc)
        tracer.log(
            agent="venue",
            event_type="error",
            error=f"VenueDBError: {exc}",
            latency_ms=elapsed_ms,
        )
        raise
    search_latency_ms = (time.monotonic_ns() - t0) // 1_000_000

    logger.info(
        "venue DB returned %d candidates in %dms",
        len(venues), search_latency_ms,
    )

    if venues:
        logger.debug("all candidates ranked by fit_score:")
        for i, v in enumerate(venues, start=1):
            logger.debug(
                "  #%d fit=%.3f | %-45s | cap %3d–%4d | LKR %7d | %s",
                i, v.fit_score, v.name, v.capacity_min, v.capacity_max,
                v.price_per_day_lkr, v.location,
            )

    tracer.log(
        agent="venue",
        event_type="tool_call",
        tool_called="search_venues",
        inputs={
            "capacity": reqs.attendee_count,
            "max_price_lkr": max_price,
            "location": reqs.location,
            "required_amenities": required_amenities,
        },
        outputs={
            "total_candidates": len(venues),
            "candidates": [
                {
                    "id": v.id,
                    "name": v.name,
                    "fit_score": v.fit_score,
                    "capacity_min": v.capacity_min,
                    "capacity_max": v.capacity_max,
                    "price_per_day_lkr": v.price_per_day_lkr,
                    "amenities": v.amenities,
                    "location": v.location,
                    "lat": v.latitude,
                    "lon": v.longitude,
                }
                for v in venues
            ],
        },
        latency_ms=search_latency_ms,
    )

    if not venues:
        msg = (
            f"No venues found for {reqs.attendee_count} attendees in '{reqs.location}' "
            f"within LKR {max_price:,}. Try a higher budget or a different location."
        )
        logger.warning("no venues matched — %s", msg)
        tracer.log(agent="venue", event_type="error", error=msg)
        raise NoVenuesFoundError(msg)

    top_venues = venues[:3]
    top_venue = top_venues[0]
    date_str = reqs.event_date.strftime("%Y-%m-%d")

    logger.info(
        "selected top %d venue(s) | #1: %r (fit=%.3f)",
        len(top_venues), top_venue.name, top_venue.fit_score,
    )

    tracer.log(
        agent="venue",
        event_type="tool_call",
        tool_called="select_top_venues",
        inputs={"total_candidates": len(venues), "max_to_return": 3},
        outputs={
            "selected": [
                {"rank": i + 1, "id": v.id, "name": v.name, "fit_score": v.fit_score}
                for i, v in enumerate(top_venues)
            ],
            "dropped_candidates": len(venues) - len(top_venues),
        },
    )

    # ── Tool: get_weather_forecast ────────────────────────────────────────────
    weather: WeatherInfo
    if top_venue.latitude is not None and top_venue.longitude is not None:
        logger.info(
            "fetching weather for %r | lat=%.4f lon=%.4f date=%s",
            top_venue.name, top_venue.latitude, top_venue.longitude, date_str,
        )

        t0 = time.monotonic_ns()
        try:
            weather = get_weather_forecast(
                latitude=top_venue.latitude,
                longitude=top_venue.longitude,
                date=date_str,
            )
            weather_latency_ms = (time.monotonic_ns() - t0) // 1_000_000
            logger.info(
                "weather fetched in %dms | %s %.1f°C precip=%d%% outdoor_friendly=%s",
                weather_latency_ms, weather.conditions, weather.temperature_c,
                weather.precipitation_probability, weather.is_outdoor_friendly,
            )
        except WeatherAPIError as exc:
            weather_latency_ms = (time.monotonic_ns() - t0) // 1_000_000
            logger.warning(
                "weather API failed after %dms, using forecast_unavailable: %s",
                weather_latency_ms, exc,
            )
            tracer.log(
                agent="venue",
                event_type="error",
                error=f"WeatherAPIError (degraded gracefully): {exc}",
                latency_ms=weather_latency_ms,
            )
            weather = WeatherInfo(
                date=date_str,
                temperature_c=0.0,
                precipitation_probability=0,
                conditions="forecast_unavailable",
                is_outdoor_friendly=False,
            )
            weather_latency_ms = 0
    else:
        logger.warning(
            "venue %r has no lat/lon — skipping weather forecast", top_venue.name
        )
        weather = WeatherInfo(
            date=date_str,
            temperature_c=0.0,
            precipitation_probability=0,
            conditions="forecast_unavailable",
            is_outdoor_friendly=False,
        )
        weather_latency_ms = 0

    tracer.log(
        agent="venue",
        event_type="tool_call",
        tool_called="get_weather_forecast",
        inputs={
            "venue": top_venue.name,
            "lat": top_venue.latitude,
            "lon": top_venue.longitude,
            "date": date_str,
        },
        outputs={
            "temperature_c": weather.temperature_c,
            "precipitation_probability": weather.precipitation_probability,
            "conditions": weather.conditions,
            "is_outdoor_friendly": weather.is_outdoor_friendly,
            "forecast_available": weather.conditions != "forecast_unavailable",
        },
        latency_ms=weather_latency_ms,
    )

    # ── LLM: generate pros, cons, weather_advisory ───────────────────────────
    venue_data_for_llm = [
        {
            "id": v.id,
            "name": v.name,
            "capacity_min": v.capacity_min,
            "capacity_max": v.capacity_max,
            "price_per_day_lkr": v.price_per_day_lkr,
            "amenities": v.amenities,
            "location": v.location,
            "fit_score": v.fit_score,
        }
        for v in top_venues
    ]

    user_prompt = json.dumps(
        {
            "venues": venue_data_for_llm,
            "weather": weather.model_dump(),
            "requirements": {
                "event_type": reqs.event_type,
                "attendee_count": reqs.attendee_count,
                "budget_lkr": reqs.budget_lkr,
                "special_requirements": reqs.special_requirements,
            },
        },
        ensure_ascii=False,
    )

    logger.info(
        "calling LLM for venue narratives | venues=%d prompt_chars=%d",
        len(top_venues), len(user_prompt),
    )
    logger.debug("LLM user prompt:\n%s", user_prompt)

    tracer.log(
        agent="venue",
        event_type="tool_call",
        tool_called="get_llm_response (pre-call)",
        inputs={
            "venues_sent": [v["name"] for v in venue_data_for_llm],
            "prompt_chars": len(user_prompt),
            "system_prompt_chars": len(VENUE_SYSTEM_PROMPT),
            "weather_conditions": weather.conditions,
        },
    )

    llm_used_fallback = False
    t0 = time.monotonic_ns()
    try:
        llm_raw: dict = llm_client.get_llm_response(
            VENUE_SYSTEM_PROMPT,
            user_prompt,
            json_mode=True,
        )
        llm_latency_ms = (time.monotonic_ns() - t0) // 1_000_000
        logger.info(
            "LLM responded in %dms | narratives_returned=%d",
            llm_latency_ms, len(llm_raw.get("venues", [])),
        )
        logger.debug("LLM raw response: %s", json.dumps(llm_raw, ensure_ascii=False))
    except LLMError as exc:
        llm_latency_ms = (time.monotonic_ns() - t0) // 1_000_000
        llm_used_fallback = True
        logger.warning(
            "LLM call failed after %dms, using template fallback: %s",
            llm_latency_ms, exc,
        )
        tracer.log(
            agent="venue",
            event_type="error",
            error=f"LLMError (fallback triggered): {exc}",
            latency_ms=llm_latency_ms,
        )
        llm_raw = {
            "venues": [
                {
                    "venue_id": v.id,
                    "pros": [
                        f"Fits up to {v.capacity_max} attendees",
                        f"Located in {v.location}",
                        f"LKR {v.price_per_day_lkr:,}/day within budget",
                    ],
                    "cons": ["Confirm all amenity requirements with venue coordinator"],
                    "weather_advisory": (
                        "Outdoor conditions look favourable for your event date."
                        if weather.is_outdoor_friendly
                        else "Weather forecast unavailable — confirm indoor contingency with the venue."
                    ),
                }
                for v in top_venues
            ]
        }

    tracer.log(
        agent="venue",
        event_type="tool_call",
        tool_called="get_llm_response",
        inputs={
            "venues_sent": [v["name"] for v in venue_data_for_llm],
            "prompt_chars": len(user_prompt),
        },
        outputs={
            "narrative_count": len(llm_raw.get("venues", [])),
            "used_fallback": llm_used_fallback,
            "venue_ids_returned": [
                item.get("venue_id") for item in llm_raw.get("venues", [])
            ],
        },
        latency_ms=llm_latency_ms,
    )

    # ── Merge DB data with LLM narratives ────────────────────────────────────
    llm_by_id: dict[int, dict] = {
        item["venue_id"]: item for item in llm_raw.get("venues", [])
    }

    missing_narratives = [v.id for v in top_venues if v.id not in llm_by_id]
    if missing_narratives:
        logger.warning(
            "LLM did not return narratives for venue IDs %s — pros/cons will be empty",
            missing_narratives,
        )
        tracer.log(
            agent="venue",
            event_type="error",
            error=f"Missing LLM narratives for venue IDs: {missing_narratives}",
        )

    venue_options: list[VenueRecommendation] = []
    for rank, venue in enumerate(top_venues, start=1):
        narrative = llm_by_id.get(venue.id, {})
        pros = narrative.get("pros", [])
        cons = narrative.get("cons", [])
        advisory = narrative.get("weather_advisory", "")

        logger.debug(
            "rank %d | %r | fit=%.3f | pros=%d cons=%d advisory_chars=%d",
            rank, venue.name, venue.fit_score, len(pros), len(cons), len(advisory),
        )

        venue_options.append(
            VenueRecommendation(
                venue=venue,
                rank=rank,
                pros=pros,
                cons=cons,
                weather_advisory=advisory,
            )
        )

    total_latency_ms = (time.monotonic_ns() - agent_start_ns) // 1_000_000

    logger.info(
        "venue_node complete in %dms | top venue: %r (fit=%.3f) | weather: %s | "
        "llm_fallback=%s",
        total_latency_ms, top_venue.name, top_venue.fit_score,
        weather.conditions, llm_used_fallback,
    )

    tracer.log(
        agent="venue",
        event_type="agent_end",
        outputs={
            "venue_count": len(venue_options),
            "chosen_venue": {
                "id": top_venue.id,
                "name": top_venue.name,
                "fit_score": top_venue.fit_score,
                "price_per_day_lkr": top_venue.price_per_day_lkr,
                "location": top_venue.location,
            },
            "weather": {
                "conditions": weather.conditions,
                "temperature_c": weather.temperature_c,
                "precipitation_probability": weather.precipitation_probability,
                "is_outdoor_friendly": weather.is_outdoor_friendly,
            },
            "all_recommendations": [
                {
                    "rank": rec.rank,
                    "venue_id": rec.venue.id,
                    "name": rec.venue.name,
                    "fit_score": rec.venue.fit_score,
                    "pros_count": len(rec.pros),
                    "cons_count": len(rec.cons),
                }
                for rec in venue_options
            ],
            "llm_used_fallback": llm_used_fallback,
            "total_latency_ms": total_latency_ms,
        },
        latency_ms=total_latency_ms,
    )

    return {
        "venue_options": venue_options,
        "chosen_venue": top_venue,
        "weather": weather,
    }
