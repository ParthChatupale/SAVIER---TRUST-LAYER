from __future__ import annotations

from appsec_agent.core.models import (
    AggregatedReviewResult,
    DimensionAnalysisResult,
    FindingCandidate,
    PrimaryFinding,
    finding_signature,
)
from appsec_agent.core.plugins import AgentSpec, ExecutionContext
from appsec_agent.core.taxonomy import normalize_owasp_category, normalize_severity, severity_for_issue
from appsec_agent.providers.base import ModelOutputError, ProviderError


SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
DIMENSION_PRIORITY = {"security": 3, "quality": 2, "performance": 1}


def run_aggregation(context: ExecutionContext) -> None:
    dimension_results = {
        "security": context.get_artifact("security_review") or DimensionAnalysisResult(dimension="security", status="skipped"),
        "quality": context.get_artifact("quality_review") or DimensionAnalysisResult(dimension="quality", status="skipped"),
        "performance": context.get_artifact("performance_review") or DimensionAnalysisResult(dimension="performance", status="skipped"),
    }
    merged_findings = _merge_findings(dimension_results)
    primary = _select_primary_finding(merged_findings)
    aggregated = AggregatedReviewResult(
        dimensions={name: _with_default_summary(result) for name, result in dimension_results.items()},
        findings=merged_findings,
        primary_finding=primary,
        status="success",
    )

    if not merged_findings:
        context.set_artifact("aggregation", aggregated)
        return

    try:
        payload = _generate_aggregation_explanation(context, primary, merged_findings)
        aggregated.primary_finding.explanation = str(payload.get("full_explanation", "")).strip() or aggregated.primary_finding.explanation
        aggregated.primary_finding.suggested_fix = str(payload.get("suggested_fix", "")).strip() or aggregated.primary_finding.suggested_fix
        context.response.owasp_category = normalize_owasp_category(
            str(payload.get("owasp_category", "")).strip(),
            vuln_type=aggregated.primary_finding.vuln_type,
        )
        context.response.data_flow = str(payload.get("data_flow", "")).strip()
        context.response.developer_note = str(payload.get("developer_note", "")).strip()
        context.response.full_explanation = aggregated.primary_finding.explanation
    except (ProviderError, ModelOutputError) as exc:
        context.response.warnings.append(f"aggregation explanation fallback: {exc}")
        context.response.owasp_category = normalize_owasp_category("", vuln_type=aggregated.primary_finding.vuln_type)
        context.response.data_flow = ""
        context.response.developer_note = (
            f"Prioritize fixing the {aggregated.primary_finding.vuln_type} issue and then address the remaining dimension findings."
        )
        context.response.full_explanation = aggregated.primary_finding.explanation

    context.set_artifact("aggregation", aggregated)


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="aggregation",
        stage="aggregation",
        order=30,
        description="Merge specialist analyzer outputs into one normalized review result.",
        input_type=dict,
        output_type=AggregatedReviewResult,
        model_config_key="model_aggregation",
        artifact_key="aggregation",
        runner=run_aggregation,
        required=True,
    )


def _merge_findings(dimension_results: dict[str, DimensionAnalysisResult]) -> list[FindingCandidate]:
    merged: list[FindingCandidate] = []
    seen: set[tuple[str, str, str]] = set()
    for dimension in ("security", "quality", "performance"):
        result = dimension_results[dimension]
        for finding in result.findings:
            key = finding_signature(
                dimension=finding.dimension,
                issue_type=finding.vuln_type,
                vulnerable_line=finding.vulnerable_line,
                pattern=finding.pattern,
                explanation=finding.attack_scenario,
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(finding)
    return sorted(
        merged,
        key=lambda finding: (
            SEVERITY_RANK.get(normalize_severity("", vuln_type=finding.vuln_type), 0),
            DIMENSION_PRIORITY.get(finding.dimension, 0),
            finding.confidence,
        ),
        reverse=True,
    )


def _select_primary_finding(findings: list[FindingCandidate]) -> PrimaryFinding:
    if not findings:
        return PrimaryFinding()
    finding = findings[0]
    return PrimaryFinding(
        dimension=finding.dimension,
        vuln_type=finding.vuln_type,
        severity=normalize_severity("", vuln_type=finding.vuln_type),
        vulnerable_line=finding.vulnerable_line,
        pattern=finding.pattern,
        explanation=finding.attack_scenario or finding.pattern,
        suggested_fix=finding.suggested_fix,
        confidence=finding.confidence,
    )


def _with_default_summary(result: DimensionAnalysisResult) -> DimensionAnalysisResult:
    if result.summary or not result.findings:
        return result
    result.summary = f"{result.finding_count} {result.dimension} issue(s) detected; top severity {result.top_severity}."
    return result


def _generate_aggregation_explanation(
    context: ExecutionContext,
    primary: PrimaryFinding,
    findings: list[FindingCandidate],
) -> dict[str, object]:
    prompt = f"""You are a senior code review explainer.
Return only valid JSON with this exact shape:
{{
  "owasp_category": "string",
  "data_flow": "string",
  "developer_note": "string",
  "full_explanation": "string",
  "suggested_fix": "string"
}}

Primary finding:
- dimension: {primary.dimension}
- type: {primary.vuln_type}
- severity: {primary.severity}
- line: {primary.vulnerable_line}

All findings:
{_findings_summary(findings)}

Code:
{context.request.code}
"""
    return context.provider.generate_json(
        model=context.metadata.get("active_model", context.config.model_aggregation),
        prompt=prompt,
        stage="aggregation",
    )


def _findings_summary(findings: list[FindingCandidate]) -> str:
    return "\n".join(
        f"- [{finding.dimension}] {finding.vuln_type}: {finding.vulnerable_line or finding.pattern}"
        for finding in findings
    )
