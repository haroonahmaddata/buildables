"""Agent API endpoint exposing the Travel Agent demo."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from travel_agent.agents import process_with_agent
from travel_agent.models.chat import AgentRequest, AgentResponse, Message

router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/agent", response_model=AgentResponse)
async def invoke_agent(payload: AgentRequest) -> AgentResponse:
    """Execute the lightweight conversational agent."""

    try:
        result = await process_with_agent(
            user_input=payload.input or "",
            messages=[message.model_dump() for message in payload.messages],
            location=payload.location,
            debug=payload.debug,
        )
    except Exception as exc:  # pragma: no cover - surface unexpected errors
        raise HTTPException(status_code=500, detail=str(exc))

    message = Message(role="assistant", content=result["content"])
    debug_payload = result.get("debug") or {}
    usage = result.get("usage") or {}

    return AgentResponse(message=message, debug=debug_payload, usage=usage)
