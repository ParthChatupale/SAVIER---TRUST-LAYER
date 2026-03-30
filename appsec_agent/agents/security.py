from __future__ import annotations

from appsec_agent.core.models import FindingCandidate, SecurityAssessment
from appsec_agent.core.plugins import AgentSpec, ExecutionContext
from appsec_agent.core.taxonomy import normalize_owasp_category, normalize_severity
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
    security = SecurityAssessment.from_payload(
        payload,
        vuln_type=coding_result.vuln_type,
        repeat_offender=repeat_offender,
    )
    security.severity = normalize_severity(
        security.severity,
        vuln_type=coding_result.vuln_type,
        repeat_offender=repeat_offender,
    )
    security.owasp_category = normalize_owasp_category(
        security.owasp_category,
        vuln_type=coding_result.vuln_type,
    )
    if not security.full_explanation:
        raise ModelOutputError("security stage returned an empty explanation.")
    return security


def should_run_security_agent(context: ExecutionContext) -> bool:
    finding = context.get_artifact("coding")
    return bool(finding and finding.vuln_found)


def run_security_agent(context: ExecutionContext) -> None:
    finding = context.get_artifact("coding")
    if finding is None:
        raise ValueError("security agent requires coding output.")
    security = security_agent(
        provider=context.provider,
        model=context.config.model_security,
        code=context.request.code,
        coding_result=finding,
        developer_history=context.history_payload(),
    )
    context.set_artifact("security", security)


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="security",
        stage="security",
        order=30,
        description="Explain severity, impact, and remediation for a finding.",
        input_type=FindingCandidate,
        output_type=SecurityAssessment,
        model_config_key="model_security",
        artifact_key="security",
        should_run=should_run_security_agent,
        runner=run_security_agent,
        required=False,
    )
