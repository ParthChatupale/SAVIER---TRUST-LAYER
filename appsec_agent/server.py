from __future__ import annotations

import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from appsec_agent.bootstrap import get_analysis_service, get_repository
from appsec_agent.core.models import AnalysisRequest

app = Server("appsec-agent")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analyze_code",
            description="Analyze a code snippet for security, quality, or performance issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code snippet to analyze",
                    },
                    "developer_id": {
                        "type": "string",
                        "description": "Unique identifier for the developer",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["security", "quality", "performance", "full"],
                        "default": "security",
                        "description": "Type of analysis to run.",
                    },
                },
                "required": ["code", "developer_id"],
            },
        ),
        Tool(
            name="get_developer_history",
            description="Return recent findings for a developer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "developer_id": {
                        "type": "string",
                        "description": "Unique identifier for the developer",
                    }
                },
                "required": ["developer_id"],
            },
        ),
        Tool(
            name="clear_developer_history",
            description="Clear stored findings for a developer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "developer_id": {
                        "type": "string",
                        "description": "Unique identifier for the developer",
                    }
                },
                "required": ["developer_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "analyze_code":
        request = AnalysisRequest.from_mapping(arguments)
        result = get_analysis_service().analyze(request)
        return [TextContent(type="text", text=json.dumps(result.to_dict(), indent=2))]

    if name == "get_developer_history":
        developer_id = str(arguments.get("developer_id", "anonymous"))
        history = get_repository().get_developer_history(developer_id)
        payload = [item.to_dict() for item in history]
        return [TextContent(type="text", text=json.dumps(payload, indent=2))]

    if name == "clear_developer_history":
        developer_id = str(arguments.get("developer_id", "anonymous"))
        get_repository().clear_developer_history(developer_id)
        message = {"status": "cleared", "developer_id": developer_id}
        return [TextContent(type="text", text=json.dumps(message, indent=2))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
