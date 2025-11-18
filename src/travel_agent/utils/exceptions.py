"""Custom exceptions for travel_agent services."""

from __future__ import annotations

from typing import Optional


class TravelAgentError(Exception):
    """Base class for travel agent related runtime errors."""

    def __init__(self, message: str, *, error_code: Optional[str] = None, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class MissingAPIKeyError(TravelAgentError):
    """Raised when a required API key has not been configured."""


class UpstreamServiceError(TravelAgentError):
    """Raised when an upstream API returns an error response."""


class TimeoutError(TravelAgentError):
    """Raised when an upstream API request times out."""


class NetworkError(TravelAgentError):
    """Raised when an upstream API request fails due to network issues."""


class IntentExtractionError(TravelAgentError):
    """Raised when Groq intent extraction fails."""
