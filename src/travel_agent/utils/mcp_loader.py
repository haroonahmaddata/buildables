"""Helpers for loading MCP-compatible LangChain tools."""

from __future__ import annotations

from typing import List

from langchain.tools import BaseTool

from travel_agent.mcp_services import (
    MCPGooglePlacesAdapter,
    MCPIntentExtractorAdapter,
    MCPTranslationAdapter,
    MCPTavilySearchAdapter,
)


async def get_mcp_tools() -> List[BaseTool]:
    """Return a set of MCP-style tools backed by local adapters."""

    # Adapters fall back to local tool implementations if no remote tool is supplied.
    return [
        MCPGooglePlacesAdapter(),
        MCPIntentExtractorAdapter(),
        MCPTranslationAdapter(),
        MCPTavilySearchAdapter(),
    ]
