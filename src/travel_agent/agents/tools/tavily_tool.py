"""LangChain tool for mock Tavily search results."""

from __future__ import annotations

from typing import Any

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from travel_agent.services.tavily import tavily_search


class TavilySearchInput(BaseModel):
    """Input schema for Tavily search requests."""

    query: str = Field(description="Web search query")


class TavilySearchTool(BaseTool):
    """Tool that surfaces canned Tavily-like search results."""

    name: str = "tavily_search_tool"
    description: str = "Perform a lightweight web search for general knowledge or events."
    args_schema: type[BaseModel] = TavilySearchInput

    def _run(self, query: str, **_: Any) -> str:
        results = tavily_search(query)
        if not results:
            return "No search results available."
        lines = [doc.format(index) for index, doc in enumerate(results, 1)]
        return "\n\n".join(lines)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - delegator
        return self._run(*args, **kwargs)


tavily_search_tool = TavilySearchTool()
