"""Intent extraction utilities leveraging Groq with heuristic fallback."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import asdict, dataclass
from typing import Optional

from groq import Groq

from travel_agent.app.config import settings
from travel_agent.utils.exceptions import MissingAPIKeyError
from travel_agent.utils.logger import setup_logger

logger = setup_logger(__name__)

_groq_client: Optional[Groq] = None


@dataclass(slots=True)
class ExtractedIntent:
    intent: str
    descriptor: Optional[str] = None
    brand: Optional[str] = None
    proximity: Optional[str] = None
    ranking: Optional[str] = None
    openNow: Optional[bool] = None
    price: Optional[str] = None
    language: Optional[str] = None
    confidence: float = 0.0

    def model_dump(self) -> dict[str, object]:
        return asdict(self)


_PLACES_KEYWORDS = (
    "restaurant",
    "coffee",
    "cafe",
    "hotel",
    "shop",
    "store",
    "mall",
    "park",
    "museum",
    "food",
    "dinner",
    "lunch",
    "breakfast",
    "bar",
    "club",
    "gym",
)

_QUESTION_WORDS = {"what", "where", "when", "who", "why", "how", "which", "find", "show", "list"}
_NEAR_PATTERN = re.compile(r"near\s+(me|by|here|[a-zA-Z ]+)", re.IGNORECASE)
_BEST_PATTERN = re.compile(r"best|top|popular|famous", re.IGNORECASE)
_OPEN_PATTERN = re.compile(r"open now|open late", re.IGNORECASE)

INTENT_PROMPT = """You are ExtractorAI. Convert the user's request into a JSON object with:
intent: "places" or "other"
descriptor: clean descriptor (e.g. "coffee shop") or null
brand: brand name or null
proximity: "near_me" or null
openNow: boolean
price: "low" | "mid" | "high" | null
ranking: "prominence" | null
language: ISO code ("en" or "ar")
confidence: float 0-1

Rules:
- Strip filler phrases like "what's the best" from descriptor.
- If unsure, set intent="other" and confidence<0.45.
- Keep response strictly JSON."""


def _get_groq_client() -> Groq:
    if not settings.GROQ_API_KEY:
        raise MissingAPIKeyError("GROQ_API_KEY is required for intent extraction")

    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client


def _heuristic_intent(query: str, previous: Optional[ExtractedIntent]) -> ExtractedIntent:
    normalized = query.lower().strip()
    if not normalized:
        return ExtractedIntent(intent="other", confidence=0.0)

    descriptor = None
    for word in re.split(r"[^a-z0-9]+", normalized):
        if word in _PLACES_KEYWORDS:
            descriptor = word
            break

    if descriptor is None and previous and previous.descriptor:
        descriptor = previous.descriptor

    brand = None
    for token in re.findall(r"([A-Z][a-zA-Z]+)", query):
        if token.lower() not in _QUESTION_WORDS:
            brand = token
            break

    proximity = "near_me" if _NEAR_PATTERN.search(normalized) else None
    ranking = "prominence" if _BEST_PATTERN.search(normalized) else None
    open_now = bool(_OPEN_PATTERN.search(normalized))

    is_places = descriptor is not None or brand is not None
    confidence = 0.7 if is_places else 0.4
    if previous and previous.intent == "places" and is_places:
        confidence = max(confidence, previous.confidence * 0.9)

    return ExtractedIntent(
        intent="places" if is_places else "other",
        descriptor=descriptor,
        brand=brand,
        proximity=proximity,
        ranking=ranking,
        openNow=open_now or None,
        price=None,
        language=None,
        confidence=confidence,
    )


async def extract_intent(query: str, previous_intent: Optional[ExtractedIntent] = None) -> ExtractedIntent:
    if not query.strip():
        return ExtractedIntent(intent="other", confidence=0.0)

    if not settings.GROQ_API_KEY:
        return _heuristic_intent(query, previous_intent)

    client = _get_groq_client()

    messages = [{"role": "system", "content": INTENT_PROMPT}]
    if previous_intent and (previous_intent.descriptor or previous_intent.brand):
        messages.append(
            {
                "role": "system",
                "content": (
                    "Previous context: "
                    f"descriptor={previous_intent.descriptor or 'null'}, "
                    f"brand={previous_intent.brand or 'null'}."
                    " Use this if the new query is ambiguous."
                ),
            }
        )
    messages.append({"role": "user", "content": query})

    try:
        completion = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
        )
    except MissingAPIKeyError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime issues
        logger.warning("Groq intent extraction failed: %s", exc)
        return _heuristic_intent(query, previous_intent)

    content = completion.choices[0].message.content if completion.choices else None
    if not content:
        return _heuristic_intent(query, previous_intent)

    try:
        parsed = json.loads(content)
        intent = ExtractedIntent(**parsed)
    except Exception as exc:  # pragma: no cover - invalid JSON
        logger.warning("Failed to parse Groq response: %s", exc)
        return _heuristic_intent(query, previous_intent)

    if previous_intent and not intent.descriptor and not intent.brand:
        intent.descriptor = previous_intent.descriptor
        intent.brand = previous_intent.brand

    return intent
