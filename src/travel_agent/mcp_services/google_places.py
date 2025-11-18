"""MCP-style adapters for the mock Google Places tool."""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel

from travel_agent.agents.tools.google_places_tool import GooglePlacesInput, google_places_tool


class MCPGooglePlacesAdapter(BaseTool):
    """Wrap an MCP provided Google Places tool with the local schema."""

    name: str = google_places_tool.name
    description: str = google_places_tool.description
    args_schema: type[BaseModel] = GooglePlacesInput

    def __init__(self, remote_tool: Optional[BaseTool] = None) -> None:
        super().__init__()
        self._remote_tool = remote_tool or google_places_tool
        if getattr(self._remote_tool, "description", None):
            self.description = self._remote_tool.description  # type: ignore[assignment]

    def _build_payload(self, **kwargs: Any) -> Dict[str, Any]:
        payload = GooglePlacesInput(**kwargs)
        return {"payload": payload.model_dump()}

    def _run(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is google_places_tool:
            return self._remote_tool.run(*args, **kwargs)  # uses BaseTool.run for schema handling
        call_args = self._build_payload(**kwargs)
        return self._remote_tool.invoke(call_args)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is google_places_tool:
            return await self._remote_tool.arun(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return await self._remote_tool.ainvoke(call_args)


async def run_google_places(payload: GooglePlacesInput) -> str:
    """Execute the local Google Places tool with an MCP payload."""

    return await google_places_tool.arun(**payload.model_dump())
