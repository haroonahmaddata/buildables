"""Tavily web search integration."""

from __future__ import annotations

from typing import List

from tavily import TavilyClient

from travel_agent.app.config import settings
from travel_agent.models.places import TavilyDocument, TavilyResponse
from travel_agent.utils.exceptions import MissingAPIKeyError, UpstreamServiceError


def _get_client() -> TavilyClient:
    if not settings.TAVILY_API_KEY:
        raise MissingAPIKeyError("TAVILY_API_KEY is required for Tavily search")
    return TavilyClient(api_key=settings.TAVILY_API_KEY)


def tavily_search(
    query: str,
    *,
    max_results: int = 5,
    search_depth: str = "basic",
) -> TavilyResponse:
    """Execute a Tavily search and return normalized results."""

    client = _get_client()

    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
        )
    except MissingAPIKeyError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime issues
        raise UpstreamServiceError(
            "Tavily search failed",
            error_code="TAVILY_API_ERROR",
            details={"error": str(exc)},
        ) from exc

    documents = [
        TavilyDocument(
            title=item.get("title", "Untitled"),
            url=item.get("url", ""),
            content=item.get("content", ""),
        )
        for item in response.get("results", [])
    ]

    return TavilyResponse(query=query, results=documents, answer=response.get("answer"))
