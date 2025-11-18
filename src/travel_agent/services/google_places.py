"""Google Places API integration mirroring the shtabi-backend implementation."""

from __future__ import annotations

from typing import List, Optional

import httpx

from travel_agent.app.config import settings
from travel_agent.models.places import Place, LatLng
from travel_agent.services.intent_extractor import ExtractedIntent
from travel_agent.services.distance_matrix import calculate_distance_matrix
from travel_agent.utils.logger import setup_logger
from travel_agent.utils.exceptions import (
    MissingAPIKeyError,
    TimeoutError,
    NetworkError,
    UpstreamServiceError,
)

logger = setup_logger(__name__)

DEFAULT_RADIUS_M = 5000
RADIUS_STEPS = [2500, 5000, 10000, 15000]


def _map_result_to_place(result: dict) -> Place:
    display_name = result.get("displayName", {})
    opening_hours = result.get("currentOpeningHours", {})

    price_level_str = result.get("priceLevel")
    price_level = None
    if price_level_str:
        price_map = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        }
        price_level = price_map.get(price_level_str)

    return Place(
        name=display_name.get("text", "Unknown"),
        address=result.get("formattedAddress", ""),
        place_id=result.get("id"),
        rating=result.get("rating"),
        price_level=price_level,
        open_now=opening_hours.get("openNow") if opening_hours else None,
        url=f"https://www.google.com/maps/place/?q=place_id:{result.get('id')}"
        if result.get("id")
        else None,
    )


def search_places_text(
    query: str, location: Optional[LatLng], radius_m: int = DEFAULT_RADIUS_M
) -> List[Place]:
    if not settings.GOOGLE_MAPS_API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not configured")
        raise MissingAPIKeyError("GOOGLE_MAPS_API_KEY is required")

    try:
        logger.info(
            "Searching places by text",
            extra={
                "query": query,
                "has_location": location is not None,
                "radius_m": radius_m,
            },
        )

        url = "https://places.googleapis.com/v1/places:searchText"

        body = {
            "textQuery": query,
            "languageCode": "en",
            "maxResultCount": 5,
        }

        if location:
            body["locationBias"] = {
                "circle": {
                    "center": {"latitude": location.lat, "longitude": location.lng},
                    "radius": radius_m,
                }
            }

        field_mask = ",".join(
            [
                "places.id",
                "places.displayName",
                "places.formattedAddress",
                "places.location",
                "places.rating",
                "places.userRatingCount",
                "places.priceLevel",
                "places.currentOpeningHours",
                "places.primaryTypeDisplayName",
                "places.types",
            ]
        )

        response = httpx.post(
            url,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
                "X-Goog-FieldMask": field_mask,
            },
            json=body,
            timeout=30.0,
        )

        if not response.is_success:
            logger.error(
                "Google Places API error",
                extra={
                    "status_code": response.status_code,
                    "response": response.text[:500],
                },
            )
            raise UpstreamServiceError(
                "Google Places API returned an error",
                error_code="GOOGLE_PLACES_ERROR",
                details={
                    "status_code": response.status_code,
                    "response": response.text[:200],
                },
            )

        data = response.json()
        places = data.get("places", [])

        logger.info("Found %d places", len(places))
        return [_map_result_to_place(p) for p in places]

    except httpx.TimeoutException as exc:
        logger.error("Google Places API timeout", exc_info=True)
        raise TimeoutError(
            "Google Places API request timed out", error_code="GOOGLE_PLACES_TIMEOUT"
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Network error calling Google Places API", exc_info=True)
        raise NetworkError(
            "Failed to connect to Google Places API",
            error_code="GOOGLE_PLACES_NETWORK_ERROR",
            details={"error": str(exc)},
        ) from exc
    except UpstreamServiceError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        logger.critical(
            "Unexpected error in Google Places text search: %s", type(exc).__name__, exc_info=True
        )
        raise UpstreamServiceError(
            "Unexpected error in Google Places search",
            error_code="GOOGLE_PLACES_UNEXPECTED_ERROR",
            details={"error_type": type(exc).__name__, "error": str(exc)},
        ) from exc


def search_places_nearby(
    descriptor: str, location: LatLng, radius_m: int = DEFAULT_RADIUS_M
) -> List[Place]:
    try:
        if not settings.GOOGLE_MAPS_API_KEY:
            logger.warning("Missing GOOGLE_MAPS_API_KEY for nearby search")
            return []

        url = "https://places.googleapis.com/v1/places:searchNearby"

        body = {
            "languageCode": "en",
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": location.lat, "longitude": location.lng},
                    "radius": radius_m,
                }
            },
        }

        field_mask = ",".join(
            [
                "places.id",
                "places.displayName",
                "places.formattedAddress",
                "places.location",
                "places.rating",
                "places.userRatingCount",
                "places.priceLevel",
                "places.currentOpeningHours",
                "places.primaryTypeDisplayName",
                "places.types",
            ]
        )

        response = httpx.post(
            url,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
                "X-Goog-FieldMask": field_mask,
            },
            json=body,
            timeout=30.0,
        )

        if not response.is_success:
            logger.warning(
                "Nearby search failed",
                extra={"status": response.status_code, "response": response.text[:200]},
            )
            return []

        data = response.json()
        places = data.get("places", [])
        return [_map_result_to_place(p) for p in places]

    except Exception as exc:
        logger.warning("Nearby search error: %s", exc)
        return []


def universal_search(intent: ExtractedIntent, location: Optional[LatLng]) -> List[Place]:
    query = None
    if intent.brand:
        query = intent.brand
    elif intent.descriptor:
        query = intent.descriptor
    else:
        query = "restaurant"

    wants_near = intent.proximity == "near_me"

    if wants_near and location:
        return _expand_radius_nearby(query, location)

    return _expand_radius_text(query, location)


def _expand_radius_text(query: str, location: Optional[LatLng]) -> List[Place]:
    for radius in RADIUS_STEPS:
        results = search_places_text(query, location, radius)
        if results:
            return results
    return []


def _expand_radius_nearby(descriptor: str, location: LatLng) -> List[Place]:
    for radius in RADIUS_STEPS:
        results = search_places_nearby(descriptor, location, radius)
        if results:
            return results
    return []


async def search_places(intent: ExtractedIntent, location: Optional[LatLng]) -> List[Place]:
    results = universal_search(intent, location)

    # the shtabi backend runs synchronously for search functions; maintain compatibility
    # by handling enrichment asynchronously only when required
    if location and results:
        try:
            enriched = await enrich_places_with_distances(results, location)
            results = enriched
        except Exception:  # pragma: no cover - enrichment should not crash search
            logger.warning("Distance enrichment failed", exc_info=True)

    if intent.openNow is True:
        results = [place for place in results if place.open_now is True]
    elif intent.openNow is False:
        results = [place for place in results if place.open_now is False]

    ranking = (intent.ranking or "").lower()
    if ranking in {"best", "prominence"}:
        results = sorted(results, key=lambda place: place.rating or 0.0, reverse=True)

    return results


async def enrich_places_with_distances(places: List[Place], user_location: LatLng) -> List[Place]:
    if not places or not user_location:
        return places

    try:
        destinations = []
        for place in places:
            if place.place_id:
                destinations.append({"place_id": place.place_id})
            else:
                destinations.append(user_location)

        if not destinations:
            logger.warning("No valid destinations for distance calculation")
            return places

        logger.info("Calculating distances for %d places", len(destinations))
        distance_results = await calculate_distance_matrix(
            origins=[user_location], destinations=destinations
        )

        for index, place in enumerate(places):
            if index < len(distance_results):
                result = distance_results[index]
                if result.status == "OK":
                    place.distance_text = result.distanceText
                    place.duration_text = result.durationText
        return places

    except Exception as exc:
        logger.error("Failed to enrich places with distances: %s", exc, exc_info=True)
        return places
