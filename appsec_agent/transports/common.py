from __future__ import annotations

import copy
from typing import Any

from appsec_agent.core.models import AnalysisRequest, AnalysisResponse


ANALYZE_CODE_SCHEMA = {
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
            "default": "full",
            "description": "Type of analysis to run.",
        },
        "file_uri": {
            "type": "string",
            "description": "Optional file identifier used for timeline and dashboard tracking.",
        },
        "source": {
            "type": "string",
            "default": "ide_extension",
            "description": "Origin of the analysis request such as ide_extension, mcp_agent, cli, or http_client.",
        },
        "project_id": {
            "type": "string",
            "description": "Optional project identifier for future grouping.",
        },
    },
    "required": ["code", "developer_id"],
}


def analysis_input_schema() -> dict[str, Any]:
    return copy.deepcopy(ANALYZE_CODE_SCHEMA)


def parse_analysis_request(payload: dict[str, Any] | None) -> tuple[AnalysisRequest | None, AnalysisResponse | None]:
    payload = payload or {}
    try:
        request = AnalysisRequest.from_mapping(payload)
    except ValueError as exc:
        return None, _failed_request_response(payload, str(exc))
    return request, None


def http_status_for_result(result: AnalysisResponse) -> int:
    if result.status != "failed":
        return 200
    if any("Unsupported analysis mode" in error for error in result.errors):
        return 400
    if any("No code provided" in error for error in result.errors):
        return 400
    return 200


def serialize_result(result: AnalysisResponse) -> dict[str, Any]:
    return result.to_dict()


def serialize_history(history_items: list[Any]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in history_items]


def serialize_file_state(file_state: Any | None) -> dict[str, Any] | None:
    if file_state is None:
        return None
    if isinstance(file_state, dict):
        return file_state
    return file_state.to_dict()


def serialize_dashboard(summary: Any) -> dict[str, Any]:
    if isinstance(summary, dict):
        return summary
    return summary.to_dict()


def serialize_timeline(events: list[Any]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for event in events:
        if isinstance(event, dict):
            serialized.append(event)
        else:
            serialized.append(event.to_dict())
    return serialized


def clear_history_payload(developer_id: str) -> dict[str, Any]:
    return {"status": "cleared", "developer_id": developer_id}


def _failed_request_response(payload: dict[str, Any], error: str) -> AnalysisResponse:
    developer_id = str(payload.get("developer_id", "anonymous"))
    raw_mode = str(payload.get("mode", "full")).strip().lower()
    mode = raw_mode if raw_mode in {"security", "quality", "performance", "full"} else "full"
    return AnalysisResponse(
        status="failed",
        developer_id=developer_id,
        mode=mode,
        errors=[error],
    )
