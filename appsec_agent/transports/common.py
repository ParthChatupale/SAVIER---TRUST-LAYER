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
            "default": "security",
            "description": "Type of analysis to run.",
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


def clear_history_payload(developer_id: str) -> dict[str, Any]:
    return {"status": "cleared", "developer_id": developer_id}


def _failed_request_response(payload: dict[str, Any], error: str) -> AnalysisResponse:
    developer_id = str(payload.get("developer_id", "anonymous"))
    mode = "security"
    return AnalysisResponse(
        status="failed",
        developer_id=developer_id,
        mode=mode,
        errors=[error],
    )
