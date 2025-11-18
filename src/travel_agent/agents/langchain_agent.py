"""High-level agent orchestration for the Travel Agent service."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from travel_agent.agents.tools import (
    google_places_tool,
    intent_extractor_tool,
    tavily_search_tool,
    translation_tool,
)
from travel_agent.models.chat import LatLng
from travel_agent.models.places import Place, TavilyDocument, TavilyResponse
from travel_agent.services.google_places import search_places
from travel_agent.services.intent_extractor import ExtractedIntent, extract_intent
from travel_agent.services.tavily import tavily_search
from travel_agent.services.translation import ensure_language_consistency
from travel_agent.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_LOCATION = LatLng(lat=29.3759, lng=47.9774)  # Kuwait City (example)

_GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|yo|salam|salaam|مرحبا|هلا|أهلين|good (morning|afternoon|evening))\b",
    re.IGNORECASE,
)
_CHITCHAT_PATTERN = re.compile(
    r"^(how are you|thanks|thank you|ok|okay|got it|شكرا|تسلم)\b",
    re.IGNORECASE,
)


async def create_travel_agent(location: Optional[LatLng] = None) -> Dict[str, Any]:
    """Return metadata describing the configured agent instance."""

    return {
        "location": (location or DEFAULT_LOCATION).model_dump(),
        "tools": [
            google_places_tool.name,
            intent_extractor_tool.name,
            tavily_search_tool.name,
            translation_tool.name,
        ],
        "version": "0.1.0",
    }


async def _resolve_intent(
    text: str, messages: List[Dict[str, str]]
) -> ExtractedIntent:
    """Extract intent using Groq with heuristic fallback and sticky context."""

    previous_intent: Optional[ExtractedIntent] = None
    for message in reversed(messages):
        if message.get("role") == "user":
            previous_intent = await extract_intent(message.get("content", ""))
            break

    intent = await extract_intent(text, previous_intent=previous_intent)
    logger.debug("Extracted intent", extra={"intent": intent.model_dump()})
    return intent


def _format_places_response(results: List[Any]) -> str:
    header = "Here are some places you might like:\n"
    body = "\n\n".join(place.format_for_agent(index) for index, place in enumerate(results, 1))
    return header + body


def _format_search_response(results: List[Any]) -> str:
    header = "Here is what I found:\n"
    body = "\n\n".join(result.format_for_agent(index) for index, result in enumerate(results, 1))
    return header + body


async def process_with_agent(
    user_input: str,
    messages: Optional[List[Dict[str, str]]] = None,
    location: Optional[LatLng] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """Process a user query using lightweight heuristics and mock tools."""

    messages = messages or []
    text = user_input.strip()
    if not text and messages:
        text = messages[-1]["content"].strip()

    if not text:
        text = "hello"

    if _GREETING_PATTERN.match(text) or _CHITCHAT_PATTERN.match(text):
        content = "Hi there! I can recommend places, events, or general travel tips. What are you in the mood for?"
        return {
            "content": content,
            "debug": {"mode": "greeting"} if debug else None,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    intent = await _resolve_intent(text, messages)

    active_location = location or DEFAULT_LOCATION
    debug_payload: Dict[str, Any] = {
        "intent": intent.model_dump(),
        "location": active_location.model_dump(),
    }

    if intent.intent == "places":
        results = await search_places(intent, active_location)
        content = (
            _format_places_response(results)
            if results
            else "I couldn't find matching places right now."
        )
        used_tool = google_places_tool.name
        debug_payload["tool"] = used_tool
        debug_payload["result_count"] = len(results)
        debug_payload["results"] = [place.model_dump() for place in results]
    else:
        search_response: TavilyResponse
        try:
            search_response = tavily_search(text)
        except Exception as exc:  # pragma: no cover - upstream runtime errors
            logger.warning("Tavily search failed", exc_info=True)
            search_response = TavilyResponse(query=text, results=[], answer=None)

        results = search_response.results
        if results:
            content = _format_search_response(results)
            if search_response.answer:
                content = f"{search_response.answer}\n\n" + content
        else:
            content = "I couldn't find any helpful information yet."
        used_tool = tavily_search_tool.name
        debug_payload["tool"] = used_tool
        debug_payload["result_count"] = len(results)
        debug_payload["answer"] = search_response.answer

    translation = await ensure_language_consistency(text, content)
    final_content = translation.translatedText
    debug_payload["translation"] = {
        "sourceLanguage": translation.sourceLanguage,
        "targetLanguage": translation.targetLanguage,
        "needsTranslation": translation.needsTranslation,
        "confidence": translation.confidence,
    }

    return {
        "content": final_content,
        "debug": debug_payload if debug else None,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
