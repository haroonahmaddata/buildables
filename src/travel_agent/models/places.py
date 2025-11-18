"""Pydantic models describing place search outputs."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    """Latitude/longitude pair."""

    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)


class Place(BaseModel):
    """Single place entry returned by Google Places API."""

    name: str
    address: Optional[str] = None
    place_id: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    open_now: Optional[bool] = None
    url: Optional[str] = None
    distance_text: Optional[str] = None
    duration_text: Optional[str] = None
    distance_value: Optional[int] = None
    duration_value: Optional[int] = None

    def format_for_agent(self, index: int) -> str:
        """Render a human-readable summary for conversational responses."""

        rating = f"{self.rating:.1f}★" if self.rating is not None else "Rating unavailable"
        price_map = {0: "free", 1: "low", 2: "mid", 3: "high", 4: "premium"}
        price = price_map.get(self.price_level, "unknown")
        status_map = {True: "Open now", False: "Closed now", None: "Hours unavailable"}
        status = status_map.get(self.open_now)

        distance_line = ""
        if self.duration_text and self.distance_text:
            distance_line = f"\n⏱ {self.duration_text} · 📍 {self.distance_text}"

        return (
            f"{index}. {self.name}\n"
            f"  {self.address or 'Address unavailable'}\n"
            f"  Rating: {rating}\n"
            f"  Budget: {price}\n"
            f"  Status: {status}{distance_line}\n"
            f"  Map: {self.url or 'N/A'}"
        )


class DistanceResult(BaseModel):
    """Result row returned by the Distance Matrix API."""

    index: int
    status: str
    distanceText: Optional[str] = None
    distanceValue: Optional[int] = None
    durationText: Optional[str] = None
    durationValue: Optional[int] = None


class TavilyDocument(BaseModel):
    """Document returned from Tavily web search."""

    title: str
    url: str
    content: str

    def format_for_agent(self, index: int) -> str:
        return f"{index}. {self.title}\n   {self.content}\n   {self.url}"


class TavilyResponse(BaseModel):
    """Normalized Tavily search response."""

    query: str
    results: list[TavilyDocument]
    answer: Optional[str] = None
