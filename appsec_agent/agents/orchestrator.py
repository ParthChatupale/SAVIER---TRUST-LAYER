from __future__ import annotations

from appsec_agent.bootstrap import get_analysis_service
from appsec_agent.transports.common import parse_analysis_request, serialize_result


def run_appsec_swarm(code: str, developer_id: str, mode: str = "security") -> dict:
    service = get_analysis_service()
    request, error_result = parse_analysis_request(
        {"code": code, "developer_id": developer_id, "mode": mode}
    )
    if error_result is not None:
        return serialize_result(error_result)
    return serialize_result(service.analyze(request))


def format_finding(result: dict) -> str:
    if result.get("status") == "failed":
        return "\n❌ Analysis failed.\n" + "\n".join(result.get("errors", [])) + "\n"

    if not result.get("vuln_found", False):
        return "\n✅ No vulnerability detected. Code looks clean.\n"

    mode_label = result.get("mode", "security").upper()
    lines = [
        f"\n{'=' * 60}",
        f"  APPSEC FINDING [{mode_label}] — {result.get('severity', 'UNKNOWN')}",
        f"{'=' * 60}",
        f"  Status      : {result.get('status', 'success')}",
        f"  Type        : {result.get('vuln_type', '')}",
        f"  OWASP       : {result.get('owasp_category', '')}",
        f"  Severity    : {result.get('severity', '')}",
        f"  Confidence  : {result.get('confidence', 0.0):.2f}",
        "",
        "  Line:",
        f"  {result.get('vulnerable_line', '')}",
        "",
        "  Impact:",
        f"  {result.get('attack_scenario', '')}",
        "",
        "  Data flow:",
        f"  {result.get('data_flow', '')}",
        "",
        "  Suggested fix:",
        f"  {result.get('suggested_fix', '')}",
        "",
        "  Explanation:",
        f"  {result.get('full_explanation', '')}",
        "",
        "  Note for you:",
        f"  {result.get('developer_note', '')}",
        f"{'=' * 60}\n",
    ]
    return "\n".join(lines)
