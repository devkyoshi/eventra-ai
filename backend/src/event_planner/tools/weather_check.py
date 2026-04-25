"""Weather check tool — Member 2.

Fetches a weather forecast from Open-Meteo (free, no API key required)
for the event date and derives outdoor-friendliness.
"""

# TODO: Member 2 — implement this tool
# Reference: PROJECT-BOOTSTRAP.md § 7.2 step 4

from __future__ import annotations

from event_planner.state.event_state import WeatherInfo


class WeatherAPIError(Exception):
    """Open-Meteo API call failed (network error, timeout, bad status)."""


class ForecastUnavailableError(Exception):
    """Requested date is outside the Open-Meteo ~16-day forecast window."""


def get_weather_forecast(
    latitude: float,
    longitude: float,
    date: str,
) -> WeatherInfo:
    """Fetch weather forecast for a specific date and location.

    Calls https://api.open-meteo.com/v1/forecast with daily variables:
    temperature_2m_max, precipitation_probability_max, weathercode.

    Derives is_outdoor_friendly = (precip_probability < 30) and (20 <= temp <= 32).

    If the date is beyond the ~16-day forecast window, returns a WeatherInfo
    with conditions="forecast_unavailable" and is_outdoor_friendly=False rather
    than raising an error — callers should handle this graceful degradation.

    Args:
        latitude: Venue latitude in decimal degrees.
        longitude: Venue longitude in decimal degrees.
        date: ISO-format date string ("YYYY-MM-DD").

    Returns:
        WeatherInfo with forecast data for the given date.

    Raises:
        WeatherAPIError: On network failure or unexpected API response.
        NotImplementedError: Until Member 2 implements this tool.
    """
    raise NotImplementedError(
        "get_weather_forecast is not yet implemented. "
        "Member 2: see PROJECT-BOOTSTRAP.md § 7.2 step 4."
    )
