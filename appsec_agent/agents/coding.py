from __future__ import annotations

from appsec_agent.core.models import FindingCandidate, PlanningResult
from appsec_agent.providers.base import ModelOutputError, ModelProvider


def coding_agent(
    *,
    provider: ModelProvider,
    model: str,
    code: str,
    planning_result: PlanningResult,
) -> FindingCandidate:
    mode_prompts = {
        "security": "Find security vulnerabilities such as SQL injection, hardcoded secrets, XSS, path traversal, and insecure deserialization.",
        "quality": "Find code quality issues such as god functions, missing error handling, missing input validation, magic numbers, and missing type hints.",
        "performance": "Find performance issues such as nested loops, database queries inside loops, missing caching, blocking I/O in async code, and redundant computation.",
        "full": "Find the most important security, quality, or performance issue in the code.",
    }

    prompt = f"""You are a code review expert.
Return only valid JSON with this exact shape:
{{
  "vuln_found": true,
  "vuln_type": "string",
  "vulnerable_line": "string",
  "pattern": "string",
  "attack_scenario": "string",
  "suggested_fix": "string",
  "confidence": 0.0
}}

If no issue is found, return:
{{
  "vuln_found": false,
  "vuln_type": "",
  "vulnerable_line": "",
  "pattern": "",
  "attack_scenario": "",
  "suggested_fix": "",
  "confidence": 0.0
}}

Mode guidance: {mode_prompts[planning_result.mode]}
Intent: {planning_result.intent}
Entry points: {planning_result.entry_points or ['NONE']}
Sensitive operations: {planning_result.sensitive_operations or ['NONE']}
Focus areas: {planning_result.security_focus or ['NONE']}

Code:
{code}
"""

    payload = provider.generate_json(model=model, prompt=prompt, stage="coding")
    finding = FindingCandidate.from_payload(payload)

    if finding.vuln_found:
        required_fields = [finding.vuln_type, finding.attack_scenario, finding.suggested_fix]
        if not all(field.strip() for field in required_fields):
            raise ModelOutputError("coding stage returned an incomplete finding.")
    return finding
