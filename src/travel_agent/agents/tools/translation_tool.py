"""LangChain translation tool built on the local translation service."""

from __future__ import annotations

from typing import Any, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from travel_agent.services.translation import (
    TranslationResult,
    ensure_language_consistency,
    translate_text,
)


class TranslationInput(BaseModel):
    """Input payload for translation requests."""

    text: Optional[str] = Field(
        default=None, description="Free form text to translate or analyse."
    )
    targetLanguage: Optional[str] = Field(
        default=None, description="Two-letter language code such as 'en' or 'ar'."
    )
    sourceLanguage: Optional[str] = Field(
        default=None, description="Optional hint for the source language."
    )
    userQuery: Optional[str] = Field(
        default=None,
        description="Original user message for language consistency checks.",
    )
    aiResponse: Optional[str] = Field(
        default=None,
        description="Assistant response text that may require translation.",
    )


def _format_result(result: TranslationResult) -> str:
    translated_flag = "TRANSLATED" if result.needsTranslation else "UNCHANGED"
    return (
        f"source={result.sourceLanguage} target={result.targetLanguage} "
        f"needs_translation={result.needsTranslation} confidence={result.confidence:.2f}\n"
        f"{translated_flag} TEXT:\n{result.translatedText}"
    )


class TranslationTool(BaseTool):
    """Tool wrapper for the translation helpers."""

    name: str = "translate_text"
    description: str = (
        "Translate text or align assistant responses with the user's language."
    )
    args_schema: type[BaseModel] = TranslationInput

    def _run(
        self,
        text: Optional[str] = None,
        targetLanguage: Optional[str] = None,
        sourceLanguage: Optional[str] = None,
        userQuery: Optional[str] = None,
        aiResponse: Optional[str] = None,
        **_: Any,
    ) -> str:
        try:
            if userQuery and aiResponse:
                result = _sync(ensure_language_consistency(userQuery, aiResponse, targetLanguage))
            elif text and targetLanguage:
                result = _sync(translate_text(text, targetLanguage, sourceLanguage))
            elif text:
                result = _sync(translate_text(text, targetLanguage or "auto", sourceLanguage))
            else:
                return "No text provided for translation."
        except Exception as exc:  # pragma: no cover - runtime error surface
            return f"Translation failed: {exc}"

        return _format_result(result)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - delegator
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


translation_tool = TranslationTool()
