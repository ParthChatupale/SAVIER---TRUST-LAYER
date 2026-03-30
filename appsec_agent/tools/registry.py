from __future__ import annotations

from collections.abc import Iterable

from appsec_agent.core.plugins import AgentRegistry, ToolExecutionContext, ToolSpec
from appsec_agent.transports.common import (
    analysis_input_schema,
    clear_history_payload,
    parse_analysis_request,
    serialize_history,
    serialize_result,
)


def iter_default_tool_specs() -> Iterable[ToolSpec]:
    yield ToolSpec(
        name="analyze_code",
        description="Analyze a code snippet for security, quality, or performance issues.",
        input_schema=analysis_input_schema(),
        implementation_ref="appsec_agent.tools.registry.analyze_code",
        handler=_handle_analyze_code,
    )
    yield ToolSpec(
        name="get_developer_history",
        description="Return recent findings for a developer.",
        input_schema={
            "type": "object",
            "properties": {
                "developer_id": {
                    "type": "string",
                    "description": "Unique identifier for the developer",
                }
            },
            "required": ["developer_id"],
        },
        implementation_ref="appsec_agent.tools.registry.get_developer_history",
        handler=_handle_get_developer_history,
    )
    yield ToolSpec(
        name="clear_developer_history",
        description="Clear stored findings for a developer.",
        input_schema={
            "type": "object",
            "properties": {
                "developer_id": {
                    "type": "string",
                    "description": "Unique identifier for the developer",
                }
            },
            "required": ["developer_id"],
        },
        implementation_ref="appsec_agent.tools.registry.clear_developer_history",
        handler=_handle_clear_developer_history,
    )


def register_default_tools(registry: AgentRegistry) -> AgentRegistry:
    for spec in iter_default_tool_specs():
        registry.register_tool(spec)
    return registry


def _handle_analyze_code(context: ToolExecutionContext, arguments: dict) -> dict:
    request, error_result = parse_analysis_request(arguments)
    if error_result is not None:
        return serialize_result(error_result)
    result = context.analysis_service.analyze(request)
    return serialize_result(result)


def _handle_get_developer_history(context: ToolExecutionContext, arguments: dict) -> list[dict]:
    developer_id = str(arguments.get("developer_id", "anonymous"))
    history = context.repository.get_developer_history(developer_id)
    return serialize_history(history)


def _handle_clear_developer_history(context: ToolExecutionContext, arguments: dict) -> dict:
    developer_id = str(arguments.get("developer_id", "anonymous"))
    context.repository.clear_developer_history(developer_id)
    return clear_history_payload(developer_id)
