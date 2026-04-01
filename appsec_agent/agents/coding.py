from __future__ import annotations

import re

from appsec_agent.core.models import FindingCandidate, FindingCollection, PlanningResult
from appsec_agent.core.plugins import AgentSpec, ExecutionContext
from appsec_agent.core.taxonomy import dimension_for_issue
from appsec_agent.providers.base import ModelOutputError, ModelProvider


def coding_agent(
    *,
    provider: ModelProvider,
    model: str,
    code: str,
    planning_result: PlanningResult,
) -> FindingCollection:
    mode_prompts = {
        "security": "Find security vulnerabilities such as SQL injection, hardcoded secrets, XSS, path traversal, and insecure deserialization.",
        "quality": "Find code quality issues such as god functions, missing error handling, missing input validation, magic numbers, and missing type hints.",
        "performance": "Find performance issues such as nested loops, database queries inside loops, missing caching, blocking I/O in async code, and redundant computation.",
        "full": "Find the most important security, quality, or performance issue in the code.",
    }

    prompt = f"""You are a code review expert.
Return only valid JSON with this exact shape:
{{
  "findings": [
    {{
      "dimension": "security|quality|performance",
      "vuln_found": true,
      "vuln_type": "string",
      "vulnerable_line": "string",
      "pattern": "string",
      "attack_scenario": "string",
      "suggested_fix": "string",
      "confidence": 0.0
    }}
  ]
}}

If no issues are found, return:
{{
  "findings": []
}}

Mode guidance: {mode_prompts[planning_result.mode]}
Intent: {planning_result.intent}
Entry points: {planning_result.entry_points or ['NONE']}
Sensitive operations: {planning_result.sensitive_operations or ['NONE']}
Focus areas: {planning_result.security_focus or ['NONE']}

Return up to 5 distinct findings. Include multiple issues if the code has them.
For mode=security only return security findings.
For mode=quality only return quality findings.
For mode=performance only return performance findings.
For mode=full return the most important cross-dimensional findings.

Code:
{code}
"""

    payload = provider.generate_json(model=model, prompt=prompt, stage="coding")
    findings = FindingCollection.from_payload(payload, mode=planning_result.mode)
    findings = _merge_findings(findings, _heuristic_findings(code, planning_result.mode))

    for finding in findings.findings:
        required_fields = [finding.vuln_type, finding.attack_scenario, finding.suggested_fix]
        if not all(field.strip() for field in required_fields):
            raise ModelOutputError("coding stage returned an incomplete finding.")
    return findings


def run_coding_agent(context: ExecutionContext) -> None:
    planning_result = context.get_artifact("planning")
    if planning_result is None:
        raise ValueError("coding agent requires planning output.")
    finding = coding_agent(
        provider=context.provider,
        model=context.metadata.get("active_model", context.config.model_coding),
        code=context.request.code,
        planning_result=planning_result,
    )
    context.set_artifact("coding", finding)


def _merge_findings(*collections: FindingCollection) -> FindingCollection:
    merged: list[FindingCandidate] = []
    seen: set[tuple[str, str, str]] = set()
    for collection in collections:
        for finding in collection.findings:
            key = (
                finding.dimension,
                finding.vuln_type,
                re.sub(r"\s+", " ", finding.vulnerable_line.strip().lower()),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(finding)
    if not merged:
        return FindingCollection(findings=[])

    merged.sort(key=lambda finding: finding.confidence, reverse=True)
    curated: list[FindingCandidate] = []
    covered_dimensions: set[str] = set()
    for finding in merged:
        if finding.dimension and finding.dimension not in covered_dimensions:
            curated.append(finding)
            covered_dimensions.add(finding.dimension)

    for finding in merged:
        if finding in curated:
            continue
        curated.append(finding)

    return FindingCollection(findings=curated[:6])


def _heuristic_findings(code: str, mode: str) -> FindingCollection:
    findings: list[FindingCandidate] = []
    normalized_code = code.lower()

    def add(issue_type: str, vulnerable_line: str, pattern: str, scenario: str, fix: str, confidence: float) -> None:
        dimension = dimension_for_issue(issue_type, mode=mode)
        if mode != "full" and dimension != mode:
            return
        findings.append(
            FindingCandidate(
                dimension=dimension,
                vuln_found=True,
                vuln_type=issue_type,
                vulnerable_line=vulnerable_line,
                pattern=pattern,
                attack_scenario=scenario,
                suggested_fix=fix,
                confidence=confidence,
            )
        )

    if re.search(r"select .*where .*['\"]\s*\+\s*\w+", normalized_code) or re.search(r"query\s*=\s*f[\"']", code):
        add(
            "SQL Injection",
            _matching_line(code, r"select .*where .*[\+{]"),
            "User-controlled data is concatenated into an SQL query.",
            "An attacker can inject crafted SQL input to read or modify data.",
            "Use parameterized queries and pass user input as bound parameters.",
            0.98,
        )
    if re.search(r"os\.system\s*\(", code) or re.search(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True", code):
        add(
            "Command Injection",
            _matching_line(code, r"os\.system|subprocess\."),
            "Untrusted input is passed to a shell command.",
            "An attacker can execute arbitrary shell commands through crafted input.",
            "Use a safe subprocess API with argument lists and validate allowed commands.",
            0.97,
        )
    if re.search(r"open\s*\(\s*\w+\s*,", code):
        add(
            "Path Traversal",
            _matching_line(code, r"open\s*\("),
            "A user-controlled filename is opened without path validation.",
            "An attacker can read unintended files by supplying traversal sequences or sensitive paths.",
            "Restrict file access to an allowlisted base directory and validate the requested path.",
            0.9,
        )
    if "input(" in code and mode in {"security", "full"}:
        add(
            "No Input Validation",
            _matching_line(code, r"input\s*\("),
            "User input is accepted and consumed without validation.",
            "Malformed or hostile input can reach sensitive operations without being constrained first.",
            "Validate user input against expected formats before using it in queries, files, or commands.",
            0.83,
        )
    if re.search(r"for .*:\n(\s+)for .*:", code):
        add(
            "Nested Loop",
            _matching_line(code, r"for .*:"),
            "Nested loops create O(n^2) work for this operation.",
            "Large inputs will grow runtime quadratically and degrade responsiveness.",
            "Use a more efficient algorithm or precomputed lookups to avoid nested scans.",
            0.88,
        )
    if re.search(r"global\s+\w+", code):
        add(
            "Global State Misuse",
            _matching_line(code, r"global\s+\w+"),
            "The function relies on shared mutable state instead of isolated responsibilities.",
            "This increases coupling, makes behavior harder to reason about, and complicates testing.",
            "Refactor the function to avoid shared global state and separate responsibilities.",
            0.86,
        )
    return FindingCollection(findings=findings)


def _matching_line(code: str, pattern: str) -> str:
    for line in code.splitlines():
        if re.search(pattern, line, flags=re.IGNORECASE):
            return line.strip()
    return ""


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="coding",
        stage="coding",
        order=20,
        description="Find the highest value code issue in the snippet.",
        input_type=PlanningResult,
        output_type=FindingCollection,
        model_config_key="model_coding",
        artifact_key="coding",
        runner=run_coding_agent,
        required=True,
    )
