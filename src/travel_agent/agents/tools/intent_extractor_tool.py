"""LangChain tool wrapping the lightweight intent extraction service."""

from __future__ import annotations

from typing import Any, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from travel_agent.services.intent_extractor import ExtractedIntent, extract_intent


class IntentExtractorInput(BaseModel):
    """Payload accepted by the intent extractor tool."""

    query: str = Field(description="User utterance to analyse")
    previous_descriptor: Optional[str] = Field(
        default=None, description="Optional descriptor from the previous turn"
    )
    previous_brand: Optional[str] = Field(
        default=None, description="Optional brand context from the previous turn"
    )


def _format(intent: ExtractedIntent) -> str:
    lines = [
        "Intent analysis:",
        f"- intent: {intent.intent}",
        f"- descriptor: {intent.descriptor or 'none'}",
        f"- brand: {intent.brand or 'none'}",
        f"- proximity: {intent.proximity or 'none'}",
        f"- ranking: {intent.ranking or 'relevance'}",
        f"- open_now: {intent.openNow if intent.openNow is not None else 'unknown'}",
        f"- confidence: {intent.confidence:.2f}",
    ]
    return "\n".join(lines)


class IntentExtractorTool(BaseTool):
    """Expose the heuristic intent extractor as a LangChain tool."""

    name: str = "intent_extractor_tool"
    description: str = (
        "Analyse the user's query to determine descriptors, brands, and search intent."
    )
    args_schema: type[BaseModel] = IntentExtractorInput

    def _run(
        self,
        query: str,
        previous_descriptor: Optional[str] = None,
        previous_brand: Optional[str] = None,
        **_: Any,
    ) -> str:
        previous = None
        if previous_descriptor or previous_brand:
            previous = ExtractedIntent(
                intent="places",
                descriptor=previous_descriptor,
                brand=previous_brand,
            )
        intent = _sync(extract_intent(query, previous))
        return _format(intent)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover
        return self._run(*args, **kwargs)


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


intent_extractor_tool = IntentExtractorTool()
