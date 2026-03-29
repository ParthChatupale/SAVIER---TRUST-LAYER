from __future__ import annotations

from appsec_agent.core.models import FindingCandidate, SecurityAssessment
from appsec_agent.core.taxonomy import severity_for_issue
from appsec_agent.providers.base import ModelOutputError, ModelProvider


def security_agent(
    *,
    provider: ModelProvider,
    model: str,
    code: str,
    coding_result: FindingCandidate,
    developer_history: list[dict],
) -> SecurityAssessment:
    repeat_offender = any(
        entry.get("vuln_type") == coding_result.vuln_type for entry in developer_history
    )

    prompt = f"""You are an application security expert.
Return only valid JSON with this exact shape:
{{
  "severity": "string",
  "owasp_category": "string",
  "cve_reference": "string",
  "data_flow": "string",
  "developer_note": "string",
  "full_explanation": "string"
}}

Vulnerability type: {coding_result.vuln_type}
Vulnerable pattern: {coding_result.pattern}
Attack scenario: {coding_result.attack_scenario}
Suggested fix: {coding_result.suggested_fix}
Repeat offender: {"yes" if repeat_offender else "no"}

Code:
{code}
"""

    payload = provider.generate_json(model=model, prompt=prompt, stage="security")
    security = SecurityAssessment.from_payload(payload)
    security.severity = security.severity or severity_for_issue(
        coding_result.vuln_type,
        repeat_offender=repeat_offender,
    )
    if not security.full_explanation:
        raise ModelOutputError("security stage returned an empty explanation.")
    return security
