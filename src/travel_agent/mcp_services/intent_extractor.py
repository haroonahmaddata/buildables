"""MCP adapters for the lightweight intent extractor."""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel

from travel_agent.agents.tools.intent_extractor_tool import (
    IntentExtractorInput,
    intent_extractor_tool,
)


class MCPIntentExtractorAdapter(BaseTool):
    """Adapter that allows calling an MCP intent extractor with flat args."""

    name: str = intent_extractor_tool.name
    description: str = intent_extractor_tool.description
    args_schema: type[BaseModel] = IntentExtractorInput

    def __init__(self, remote_tool: Optional[BaseTool] = None) -> None:
        super().__init__()
        self._remote_tool = remote_tool or intent_extractor_tool
        if getattr(self._remote_tool, "description", None):
            self.description = self._remote_tool.description  # type: ignore[assignment]

    def _build_payload(self, **kwargs: Any) -> Dict[str, Any]:
        payload = IntentExtractorInput(**kwargs)
        return {"payload": payload.model_dump()}

    def _run(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is intent_extractor_tool:
            return self._remote_tool.run(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return self._remote_tool.invoke(call_args)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is intent_extractor_tool:
            return await self._remote_tool.arun(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return await self._remote_tool.ainvoke(call_args)


async def run_intent_extractor(payload: IntentExtractorInput) -> str:
    """Execute the local intent extractor as an MCP tool."""

    return await intent_extractor_tool.arun(**payload.model_dump())
