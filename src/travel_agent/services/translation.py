"""Language detection and translation using OpenAI with graceful fallbacks."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from travel_agent.app.config import settings
from travel_agent.utils.exceptions import MissingAPIKeyError
from travel_agent.utils.logger import setup_logger

logger = setup_logger(__name__)

_ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")

_openai_client: Optional[OpenAI] = None


@dataclass(slots=True)
class LanguageDetectionResult:
    language: str
    confidence: float


@dataclass(slots=True)
class TranslationResult:
    translatedText: str
    sourceLanguage: str
    targetLanguage: str
    confidence: float
    needsTranslation: bool


def _get_openai_client() -> OpenAI:
    if not settings.OPENAI_API_KEY:
        raise MissingAPIKeyError("OPENAI_API_KEY is required for translation")

    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _heuristic_detect(text: str) -> LanguageDetectionResult:
    if not text:
        return LanguageDetectionResult(language="en", confidence=0.0)

    has_arabic = bool(_ARABIC_CHAR_RE.search(text))
    language = "ar" if has_arabic else "en"
    confidence = 0.9 if has_arabic else 0.6
    return LanguageDetectionResult(language=language, confidence=confidence)


async def detect_language(text: str | None) -> LanguageDetectionResult:
    if not text:
        return LanguageDetectionResult(language="en", confidence=0.0)

    if not settings.OPENAI_API_KEY:
        return _heuristic_detect(text)

    client = _get_openai_client()

    try:
        completion = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a language detection expert. Reply with a JSON object\n"
                            "containing `language` (ISO code) and `confidence` (0-1)."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
        )

        content = completion.choices[0].message.content if completion.choices else None
        if not content:
            return _heuristic_detect(text)

        payload = json.loads(content)
        language = payload.get("language", "en")
        confidence = float(payload.get("confidence", 0.5))
        return LanguageDetectionResult(language=language, confidence=confidence)
    except MissingAPIKeyError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime issues
        logger.warning("OpenAI language detection failed: %s", exc)
        return _heuristic_detect(text)


async def _translate_via_openai(text: str, target_language: str, source_language: str) -> str:
    client = _get_openai_client()

    completion = await asyncio.to_thread(
        lambda: client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=
            [
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator. Preserve meaning and tone."
                        " Respond with the translated text only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Source language: {source_language}\n"
                        f"Target language: {target_language}\n"
                        f"Text: {text}"
                    ),
                },
            ],
            temperature=0.1,
        )
    )

    translated = completion.choices[0].message.content if completion.choices else text
    return translated.strip() if translated else text


async def translate_text(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
) -> TranslationResult:
    detection = await detect_language(text)
    resolved_source = source_language or detection.language or "en"

    resolved_target = target_language
    if resolved_target in {"", "auto", None}:
        resolved_target = detection.language

    if resolved_source == resolved_target:
        return TranslationResult(
            translatedText=text,
            sourceLanguage=resolved_source,
            targetLanguage=resolved_target,
            confidence=detection.confidence,
            needsTranslation=False,
        )

    if not settings.OPENAI_API_KEY:
        # Without API access we cannot translate—return original text.
        return TranslationResult(
            translatedText=text,
            sourceLanguage=resolved_source,
            targetLanguage=resolved_target,
            confidence=detection.confidence,
            needsTranslation=False,
        )

    try:
        translated = await _translate_via_openai(text, resolved_target, resolved_source)
    except MissingAPIKeyError:
        raise
    except Exception as exc:  # pragma: no cover - network/runtime issues
        logger.warning("Translation failed: %s", exc)
        translated = text

    needs_translation = translated.strip() != text.strip()
    return TranslationResult(
        translatedText=translated,
        sourceLanguage=resolved_source,
        targetLanguage=resolved_target,
        confidence=detection.confidence,
        needsTranslation=needs_translation,
    )


async def ensure_language_consistency(
    user_query: str,
    ai_response: str,
    preferred_language: Optional[str] = None,
) -> TranslationResult:
    user_language = preferred_language
    if not user_language:
        user_detection = await detect_language(user_query)
        user_language = user_detection.language
    else:
        user_detection = LanguageDetectionResult(language=user_language, confidence=1.0)

    translation = await translate_text(ai_response, user_language)

    if settings.DEBUG_LANGUAGE:
        debug_suffix = (
            f"\n\n[debug] user_language={user_detection.language} "
            f"target={translation.targetLanguage} needs_translation={translation.needsTranslation}"
        )
        translation.translatedText = translation.translatedText + debug_suffix

    return translation
