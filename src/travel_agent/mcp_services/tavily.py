"""MCP adapters for the Tavily search tool."""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel

from travel_agent.agents.tools.tavily_tool import TavilySearchInput, tavily_search_tool


class MCPTavilySearchAdapter(BaseTool):
    """Wrap an MCP Tavily search tool so it speaks the local schema."""

    name: str = tavily_search_tool.name
    description: str = tavily_search_tool.description
    args_schema: type[BaseModel] = TavilySearchInput

    def __init__(self, remote_tool: Optional[BaseTool] = None) -> None:
        super().__init__()
        self._remote_tool = remote_tool or tavily_search_tool
        if getattr(self._remote_tool, "description", None):
            self.description = self._remote_tool.description  # type: ignore[assignment]

    def _build_payload(self, **kwargs: Any) -> Dict[str, Any]:
        payload = TavilySearchInput(**kwargs)
        return {"payload": payload.model_dump()}

    def _run(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is tavily_search_tool:
            return self._remote_tool.run(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return self._remote_tool.invoke(call_args)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is tavily_search_tool:
            return await self._remote_tool.arun(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return await self._remote_tool.ainvoke(call_args)


async def run_tavily_search(payload: TavilySearchInput) -> str:
    """Execute the mock Tavily search tool using an MCP payload."""

    return await tavily_search_tool.arun(**payload.model_dump())
