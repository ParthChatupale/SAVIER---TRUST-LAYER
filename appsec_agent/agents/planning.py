from __future__ import annotations

from appsec_agent.core.models import AnalysisMode, PlanningResult
from appsec_agent.providers.base import ModelOutputError, ModelProvider


def planning_agent(
    *,
    provider: ModelProvider,
    model: str,
    code: str,
    developer_history: list[dict],
    mode: AnalysisMode = "security",
) -> PlanningResult:
    history_summary = ""
    if developer_history:
        vuln_types = [entry.get("vuln_type", "") for entry in developer_history if entry.get("vuln_type")]
        if vuln_types:
            history_summary = (
                "This developer has previously been flagged for: "
                f"{', '.join(vuln_types)}. Pay extra attention to repeated patterns."
            )

    mode_instructions = {
        "security": "Focus on security vulnerabilities such as SQL injection, secrets exposure, XSS, path traversal, insecure deserialization, and auth issues.",
        "quality": "Focus on code quality issues such as god functions, missing error handling, missing input validation, magic numbers, and missing type hints.",
        "performance": "Focus on performance issues such as nested loops, repeated queries, missing caching, blocking I/O, and redundant work.",
        "full": "Focus on security, code quality, and performance. Identify the highest-risk issue categories present in the code.",
    }

    prompt = f"""You are a code analysis planning expert.
Return only valid JSON with this exact shape:
{{
  "intent": "string",
  "entry_points": ["string"],
  "sensitive_operations": ["string"],
  "security_focus": ["string"]
}}

Analysis mode: {mode}
Mode guidance: {mode_instructions[mode]}
{history_summary}

Code:
{code}
"""

    payload = provider.generate_json(model=model, prompt=prompt, stage="planning")
    planning = PlanningResult.from_payload(payload, mode)
    if not planning.intent:
        raise ModelOutputError("planning stage returned an empty intent.")
    return planning
