from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    REPO_ROOT = Path(__file__).resolve().parents[1]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from appsec_agent.bootstrap import get_analysis_service, get_plugin_registry, get_repository
from appsec_agent.core.plugins import ToolExecutionContext

app = Server("appsec-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    registry = get_plugin_registry()
    return [
        Tool(name=spec.name, description=spec.description, inputSchema=spec.input_schema)
        for spec in registry.get_enabled_tools()
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    registry = get_plugin_registry()
    spec = registry.tools.get(name)
    if spec is None or not spec.enabled:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2))]

    context = ToolExecutionContext(
        config=get_analysis_service().config,
        analysis_service=get_analysis_service(),
        repository=get_repository(),
    )
    payload = spec.handler(context, arguments)
    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
