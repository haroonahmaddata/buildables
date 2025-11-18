"""LangChain tool for Google Places searches."""

from __future__ import annotations

from typing import Any, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from travel_agent.models.chat import LatLng
from travel_agent.services.google_places import search_places
from travel_agent.services.intent_extractor import ExtractedIntent


class GooglePlacesInput(BaseModel):
    """Input schema accepted by the Google Places tool."""

    query: str = Field(
        description="Descriptor or brand describing what the user wants, e.g. 'coffee'"
    )
    lat: Optional[float] = Field(
        default=None, description="Latitude for location-biased results"
    )
    lng: Optional[float] = Field(
        default=None, description="Longitude for location-biased results"
    )
    wantsNear: Optional[bool] = Field(
        default=False, description="Whether to prioritize nearby venues"
    )
    wantsBest: Optional[bool] = Field(
        default=False, description="Whether to prioritize top-rated venues"
    )
    openNow: Optional[bool] = Field(
        default=None, description="Filter for venues currently open"
    )


class GooglePlacesTool(BaseTool):
    """Tool implementation that formats live Google Places search results."""

    name: str = "google_places_search"
    description: str = (
        "Search a curated catalogue of places. Useful for food, coffee, and venue queries."
    )
    args_schema: type[BaseModel] = GooglePlacesInput

    def _run(
        self,
        query: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        wantsNear: Optional[bool] = False,
        wantsBest: Optional[bool] = False,
        openNow: Optional[bool] = None,
        **_: Any,
    ) -> str:
        location = None
        if lat is not None and lng is not None:
            location = LatLng(lat=lat, lng=lng)

        intent = ExtractedIntent(
            intent="places",
            descriptor=query,
            brand=None,
            proximity="near_me" if wantsNear else None,
            ranking="prominence" if wantsBest else None,
            openNow=openNow,
        )

        results = _sync(search_places(intent, location))

        if not results:
            return "No matching places were found."

        lines = [place.format_for_agent(index) for index, place in enumerate(results, 1)]
        return "\n\n".join(lines)

    async def _arun(
        self,
        query: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        wantsNear: Optional[bool] = False,
        wantsBest: Optional[bool] = False,
        openNow: Optional[bool] = None,
        **_: Any,
    ) -> str:
        location = None
        if lat is not None and lng is not None:
            location = LatLng(lat=lat, lng=lng)

        intent = ExtractedIntent(
            intent="places",
            descriptor=query,
            brand=None,
            proximity="near_me" if wantsNear else None,
            ranking="prominence" if wantsBest else None,
            openNow=openNow,
        )

        results = await search_places(intent, location)

        if not results:
            return "No matching places were found."

        lines = [place.format_for_agent(index) for index, place in enumerate(results, 1)]
        return "\n\n".join(lines)


def _sync(coro):
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    return loop.run_until_complete(coro)


google_places_tool = GooglePlacesTool()
