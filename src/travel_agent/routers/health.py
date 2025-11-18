"""Health check endpoints for the Travel Agent backend."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"], summary="Basic health check")
async def health_check() -> dict[str, str]:
    """Return a simple readiness response."""
    return {"status": "ok"}
