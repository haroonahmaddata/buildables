"""Context helpers for sharing extracted intent between tool calls."""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional

from travel_agent.services.intent_extractor import ExtractedIntent

_CURRENT_INTENT: ContextVar[Optional[ExtractedIntent]] = ContextVar(
    "travel_agent_current_pre_intent", default=None
)


def set_current_pre_intent(intent: Optional[ExtractedIntent]) -> Token:
    """Store the current pre-extracted intent in a context variable."""

    return _CURRENT_INTENT.set(intent)


def get_current_pre_intent() -> Optional[ExtractedIntent]:
    """Return the intent stored in the current task context, if any."""

    return _CURRENT_INTENT.get()


def reset_current_pre_intent(token: Token) -> None:
    """Restore the previous intent value for the current context."""

    _CURRENT_INTENT.reset(token)
