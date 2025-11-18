"""Google Distance Matrix integration for travel-agent."""

from __future__ import annotations

from typing import Iterable, List, Union

import httpx

from travel_agent.app.config import settings
from travel_agent.models.places import DistanceResult, LatLng
from travel_agent.utils.exceptions import MissingAPIKeyError, UpstreamServiceError
from travel_agent.utils.logger import setup_logger

logger = setup_logger(__name__)

DistanceDestination = Union[LatLng, dict[str, str]]


async def calculate_distance_matrix(
    origins: Iterable[LatLng],
    destinations: Iterable[DistanceDestination],
    *,
    mode: str = "driving",
    units: str = "metric",
) -> List[DistanceResult]:
    """Call Google Distance Matrix API and return parsed results."""

    if not settings.GOOGLE_MAPS_API_KEY:
        raise MissingAPIKeyError("GOOGLE_MAPS_API_KEY is required for distance matrix")

    origin_str = "|".join(f"{origin.lat},{origin.lng}" for origin in origins)

    destination_parts: list[str] = []
    for dest in destinations:
        if isinstance(dest, LatLng):
            destination_parts.append(f"{dest.lat},{dest.lng}")
        elif isinstance(dest, dict) and "place_id" in dest:
            destination_parts.append(f"place_id:{dest['place_id']}")
        else:
            logger.debug("Skipping unsupported destination: %s", dest)
    if not destination_parts:
        return []

    params = {
        "origins": origin_str,
        "destinations": "|".join(destination_parts),
        "mode": mode,
        "units": units,
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params=params,
            timeout=20,
        )

    if response.status_code != 200:
        raise UpstreamServiceError(
            "Distance Matrix request failed",
            error_code="DISTANCE_MATRIX_HTTP_ERROR",
            details={"status": response.status_code, "body": response.text[:200]},
        )

    payload = response.json()
    if payload.get("status") != "OK":
        raise UpstreamServiceError(
            "Distance Matrix responded with error",
            error_code="DISTANCE_MATRIX_STATUS_ERROR",
            details={"status": payload.get("status")},
        )

    rows = payload.get("rows", [])
    if not rows:
        return []

    results: List[DistanceResult] = []
    elements = rows[0].get("elements", [])
    for index, element in enumerate(elements):
        status = element.get("status", "UNKNOWN_ERROR")
        distance = element.get("distance") or {}
        duration = element.get("duration") or {}
        results.append(
            DistanceResult(
                index=index,
                status=status,
                distanceText=distance.get("text"),
                distanceValue=distance.get("value"),
                durationText=duration.get("text"),
                durationValue=duration.get("value"),
            )
        )

    return results
