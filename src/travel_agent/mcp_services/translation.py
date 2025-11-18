"""MCP adapters for the translation tool."""

from __future__ import annotations

from typing import Any, Dict, Optional

from langchain.tools import BaseTool
from pydantic import BaseModel

from travel_agent.agents.tools.translation_tool import TranslationInput, translation_tool


class MCPTranslationAdapter(BaseTool):
    """Adapter that aligns an MCP translation tool with local schema."""

    name: str = translation_tool.name
    description: str = translation_tool.description
    args_schema: type[BaseModel] = TranslationInput

    def __init__(self, remote_tool: Optional[BaseTool] = None) -> None:
        super().__init__()
        self._remote_tool = remote_tool or translation_tool
        if getattr(self._remote_tool, "description", None):
            self.description = self._remote_tool.description  # type: ignore[assignment]

    def _build_payload(self, **kwargs: Any) -> Dict[str, Any]:
        payload = TranslationInput(**kwargs)
        return {"payload": payload.model_dump()}

    def _run(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is translation_tool:
            return self._remote_tool.run(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return self._remote_tool.invoke(call_args)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        if self._remote_tool is translation_tool:
            return await self._remote_tool.arun(*args, **kwargs)
        call_args = self._build_payload(**kwargs)
        return await self._remote_tool.ainvoke(call_args)


async def run_translation(payload: TranslationInput) -> str:
    """Execute the translation tool via MCP payload."""

    return await translation_tool.arun(**payload.model_dump())
