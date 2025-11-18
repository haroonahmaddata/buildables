"""Pydantic models describing chat inputs and outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Single chat message exchanged with the agent."""

    role: str = Field(description="Either 'user' or 'assistant'.")
    content: str = Field(description="Message body in plain text.")


class LatLng(BaseModel):
    """Simple latitude/longitude container."""

    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in degrees")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude in degrees")


class AgentRequest(BaseModel):
    """Request payload sent to the agent endpoint."""

    input: Optional[str] = Field(
        default=None, description="Latest user utterance. Optional when messages provided."
    )
    messages: List[Message] = Field(default_factory=list, description="Chat history.")
    location: Optional[LatLng] = Field(
        default=None, description="Optional user location for geo-aware queries."
    )
    user_id: Optional[int] = Field(
        default=None,
        description="Optional caller identifier propagated to downstream systems.",
    )
    debug: bool = Field(
        default=False,
        description="Whether to include debug details from the LangChain agent.",
    )


class AgentResponse(BaseModel):
    """Response envelope returned by the agent endpoint."""

    message: Message = Field(description="Assistant reply message.")
    debug: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional debug information when `debug=true` is provided.",
    )
    usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Token accounting metadata reported by the model.",
    )
