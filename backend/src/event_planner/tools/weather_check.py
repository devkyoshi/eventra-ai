"""Weather check tool — Member 2.

Fetches a weather forecast from Open-Meteo (free, no API key required)
for the event date and derives outdoor-friendliness.
"""

from __future__ import annotations

import logging
import time

import httpx

from event_planner.state.event_state import WeatherInfo

logger = logging.getLogger(__name__)

_API_BASE = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_S = 10.0

# WMO Weather Interpretation Codes → human-readable string
_WMO_CONDITIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


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

    Calls the Open-Meteo daily forecast API with temperature_2m_max,
    precipitation_probability_max, and weathercode variables.

    Outdoor-friendliness is derived as:
        precipitation_probability < 30  AND  20 <= temperature_c <= 32

    If the date is beyond the ~16-day forecast window, returns a WeatherInfo
    with conditions="forecast_unavailable" and is_outdoor_friendly=False
    rather than raising — callers should handle this graceful degradation.

    Args:
        latitude: Venue latitude in decimal degrees.
        longitude: Venue longitude in decimal degrees.
        date: ISO-format date string ("YYYY-MM-DD").

    Returns:
        WeatherInfo with forecast data for the given date.

    Raises:
        WeatherAPIError: On network failure or unexpected API response format.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,precipitation_probability_max,weathercode",
        "start_date": date,
        "end_date": date,
        "timezone": "Asia/Colombo",
    }

    logger.debug(
        "GET %s | lat=%.4f lon=%.4f date=%s timezone=Asia/Colombo timeout=%.1fs",
        _API_BASE, latitude, longitude, date, _TIMEOUT_S,
    )

    t0 = time.monotonic_ns()
    try:
        response = httpx.get(_API_BASE, params=params, timeout=_TIMEOUT_S)
        http_latency_ms = (time.monotonic_ns() - t0) // 1_000_000

        if response.status_code == 400:
            # Open-Meteo returns 400 when the date is outside the ~16-day window.
            # Treat this as a known, non-exceptional case identical to the null-values path.
            elapsed_ms = (time.monotonic_ns() - t0) // 1_000_000
            try:
                reason = response.json().get("reason", response.text[:200])
            except Exception:
                reason = response.text[:200]
            logger.info(
                "date %s is outside Open-Meteo forecast window after %dms "
                "(HTTP 400: %s) — returning forecast_unavailable",
                date, elapsed_ms, reason,
            )
            return WeatherInfo(
                date=date,
                temperature_c=0.0,
                precipitation_probability=0,
                conditions="forecast_unavailable",
                is_outdoor_friendly=False,
            )

        response.raise_for_status()
    except httpx.TimeoutException as exc:
        elapsed_ms = (time.monotonic_ns() - t0) // 1_000_000
        logger.error(
            "Open-Meteo request timed out after %dms (timeout=%.1fs): %s",
            elapsed_ms, _TIMEOUT_S, exc,
        )
        raise WeatherAPIError(f"Open-Meteo request timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        elapsed_ms = (time.monotonic_ns() - t0) // 1_000_000
        logger.error(
            "Open-Meteo returned HTTP %d after %dms: %s",
            exc.response.status_code, elapsed_ms, exc.response.text[:300],
        )
        raise WeatherAPIError(
            f"Open-Meteo returned HTTP {exc.response.status_code}: {exc.response.text[:200]}"
        ) from exc
    except Exception as exc:
        elapsed_ms = (time.monotonic_ns() - t0) // 1_000_000
        logger.error("Open-Meteo request failed after %dms: %s", elapsed_ms, exc)
        raise WeatherAPIError(f"Open-Meteo request failed: {exc}") from exc

    logger.debug("HTTP %d received in %dms", response.status_code, http_latency_ms)

    try:
        data = response.json()
    except Exception as exc:
        logger.error("failed to parse Open-Meteo JSON response: %s", exc)
        raise WeatherAPIError(f"Invalid JSON from Open-Meteo: {exc}") from exc

    daily = data.get("daily", {})
    temps: list = daily.get("temperature_2m_max", [])
    precips: list = daily.get("precipitation_probability_max", [])
    codes: list = daily.get("weathercode", [])

    logger.debug(
        "raw daily fields | temperature_2m_max=%s precipitation_probability_max=%s weathercode=%s",
        temps, precips, codes,
    )

    # Empty or null values mean the date is outside the forecast window (~16 days)
    if not temps or temps[0] is None:
        logger.warning(
            "date %s is outside the Open-Meteo forecast window (~16 days) "
            "for lat=%.4f lon=%.4f — returning forecast_unavailable",
            date, latitude, longitude,
        )
        return WeatherInfo(
            date=date,
            temperature_c=0.0,
            precipitation_probability=0,
            conditions="forecast_unavailable",
            is_outdoor_friendly=False,
        )

    temp = float(temps[0])
    precip = int(precips[0]) if precips and precips[0] is not None else 0
    code = int(codes[0]) if codes and codes[0] is not None else 0
    conditions = _WMO_CONDITIONS.get(code, f"Code {code}")

    # is_outdoor_friendly: low rain probability and comfortable temperature range
    precip_ok = precip < 30
    temp_ok = 20.0 <= temp <= 32.0
    is_outdoor_friendly = precip_ok and temp_ok

    logger.info(
        "weather for %s | %s %.1f°C precip=%d%% wmo_code=%d | "
        "outdoor_friendly=%s (precip_ok=%s temp_ok=%s) | latency=%dms",
        date, conditions, temp, precip, code,
        is_outdoor_friendly, precip_ok, temp_ok, http_latency_ms,
    )

    if not is_outdoor_friendly:
        reasons = []
        if not precip_ok:
            reasons.append(f"precipitation {precip}% >= 30%")
        if not temp_ok:
            reasons.append(f"temperature {temp}°C outside 20–32°C range")
        logger.info("not outdoor friendly because: %s", ", ".join(reasons))

    return WeatherInfo(
        date=date,
        temperature_c=temp,
        precipitation_probability=precip,
        conditions=conditions,
        is_outdoor_friendly=is_outdoor_friendly,
    )
