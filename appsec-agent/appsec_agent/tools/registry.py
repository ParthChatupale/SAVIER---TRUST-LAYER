from __future__ import annotations

from collections.abc import Iterable

from appsec_agent.core.plugins import AgentRegistry, ToolExecutionContext, ToolSpec
from appsec_agent.transports.common import (
    analysis_input_schema,
    clear_history_payload,
    parse_analysis_request,
    serialize_dashboard,
    serialize_file_state,
    serialize_history,
    serialize_result,
    serialize_timeline,
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
    yield ToolSpec(
        name="get_dashboard",
        description="Return the current dashboard summary for a developer.",
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
        implementation_ref="appsec_agent.tools.registry.get_dashboard",
        handler=_handle_get_dashboard,
    )
    yield ToolSpec(
        name="get_analysis_timeline",
        description="Return recent analysis events for a developer, optionally filtered to a file.",
        input_schema={
            "type": "object",
            "properties": {
                "developer_id": {
                    "type": "string",
                    "description": "Unique identifier for the developer",
                },
                "file_uri": {
                    "type": "string",
                    "description": "Optional file identifier to filter timeline entries.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of events to return.",
                    "default": 20,
                },
            },
            "required": ["developer_id"],
        },
        implementation_ref="appsec_agent.tools.registry.get_analysis_timeline",
        handler=_handle_get_analysis_timeline,
    )
    yield ToolSpec(
        name="get_file_state",
        description="Return the current state for a tracked developer file.",
        input_schema={
            "type": "object",
            "properties": {
                "developer_id": {
                    "type": "string",
                    "description": "Unique identifier for the developer",
                },
                "file_uri": {
                    "type": "string",
                    "description": "File identifier to retrieve.",
                },
            },
            "required": ["developer_id", "file_uri"],
        },
        implementation_ref="appsec_agent.tools.registry.get_file_state",
        handler=_handle_get_file_state,
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


def _handle_get_dashboard(context: ToolExecutionContext, arguments: dict) -> dict:
    developer_id = str(arguments.get("developer_id", "anonymous"))
    summary = context.analysis_service.get_dashboard_summary(developer_id)
    return serialize_dashboard(summary)


def _handle_get_analysis_timeline(context: ToolExecutionContext, arguments: dict) -> list[dict]:
    developer_id = str(arguments.get("developer_id", "anonymous"))
    file_uri = str(arguments.get("file_uri", "")).strip() or None
    limit = int(arguments.get("limit", 20))
    events = context.analysis_service.get_analysis_timeline(developer_id, file_uri=file_uri, limit=limit)
    return serialize_timeline(events)


def _handle_get_file_state(context: ToolExecutionContext, arguments: dict) -> dict:
    developer_id = str(arguments.get("developer_id", "anonymous"))
    file_uri = str(arguments.get("file_uri", ""))
    state = context.analysis_service.get_file_state(developer_id, file_uri)
    return serialize_file_state(state) or {}
