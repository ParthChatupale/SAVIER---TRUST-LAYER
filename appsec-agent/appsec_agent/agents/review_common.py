from __future__ import annotations

import ast
import re

from appsec_agent.core.models import (
    DimensionAnalysisResult,
    FindingCandidate,
    FindingCollection,
    PlanningResult,
    finding_signature,
)
from appsec_agent.core.taxonomy import dimension_accepts_issue, is_known_issue_type, normalize_vulnerability_type
from appsec_agent.providers.base import ModelOutputError, ModelProvider


MODE_GUIDANCE = {
    "security": "Find concrete security vulnerabilities such as SQL injection, command injection, path traversal, secrets exposure, and unsafe trust boundaries.",
    "quality": "Find concrete quality issues such as global state misuse, god functions, missing error handling, magic numbers, and poor maintainability.",
    "performance": "Find concrete performance issues such as nested loops, unbounded memory growth, repeated queries, blocking I/O, and redundant work.",
}


def run_dimension_review(
    *,
    provider: ModelProvider,
    model: str,
    code: str,
    planning_result: PlanningResult,
    dimension: str,
) -> DimensionAnalysisResult:
    prompt = f"""You are an expert {dimension} code reviewer.
Return only valid JSON with this exact shape:
{{
  "findings": [
    {{
      "dimension": "{dimension}",
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

If no {dimension} issues are found, return:
{{
  "findings": []
}}

Rules:
- Only return {dimension} findings.
- Return up to 4 distinct findings.
- Findings must reference concrete code lines or operations from the snippet.
- Do not omit a clear suggested fix and explanation.

Mode guidance: {MODE_GUIDANCE[dimension]}
Intent: {planning_result.intent}
Entry points: {planning_result.entry_points or ['NONE']}
Sensitive operations: {planning_result.sensitive_operations or ['NONE']}
Focus areas: {planning_result.security_focus or ['NONE']}

Code:
{code}
    """
    payload = provider.generate_json(model=model, prompt=prompt, stage=f"{dimension}_review")
    model_findings = _filter_dimension_findings(
        FindingCollection.from_payload(payload, mode=dimension),
        code=code,
        dimension=dimension,
    )
    heuristics = heuristic_dimension_findings(code, dimension)
    merged = merge_dimension_findings(model_findings, heuristics)

    for finding in merged.findings:
        required_fields = [finding.vuln_type, finding.attack_scenario, finding.suggested_fix]
        if not all(field.strip() for field in required_fields):
            raise ModelOutputError(f"{dimension}_review stage returned an incomplete finding.")

    return DimensionAnalysisResult(dimension=dimension, findings=merged.findings)


def merge_dimension_findings(*collections: FindingCollection) -> FindingCollection:
    merged: list[FindingCandidate] = []
    seen: set[tuple[str, str, str]] = set()
    for collection in collections:
        for finding in collection.findings:
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
    merged.sort(key=lambda finding: finding.confidence, reverse=True)
    return FindingCollection(findings=merged[:4])


def _filter_dimension_findings(collection: FindingCollection, *, code: str, dimension: str) -> FindingCollection:
    filtered: list[FindingCandidate] = []
    for finding in collection.findings:
        if not is_known_issue_type(finding.vuln_type):
            continue
        finding.dimension = normalize_dimension(finding.vuln_type, requested_dimension=dimension)
        if finding.dimension != dimension:
            continue
        if not _finding_matches_code(finding, code):
            continue
        filtered.append(finding)
    return FindingCollection(findings=filtered)


def normalize_dimension(vuln_type: str, *, requested_dimension: str) -> str:
    if dimension_accepts_issue(requested_dimension, vuln_type):
        return requested_dimension
    return requested_dimension if requested_dimension not in {"security", "quality", "performance"} else ""


def _finding_matches_code(finding: FindingCandidate, code: str) -> bool:
    canonical = normalize_vulnerability_type(finding.vuln_type)
    normalized_code = code.lower()
    line = (finding.vulnerable_line or "").lower()

    if canonical == "SQL Injection":
        return bool(
            re.search(r"(query\s*=\s*f[\"'])|(['\"]\s*\+\s*\w+)|cursor\.execute|db\.execute|select\s+.*where", code, re.IGNORECASE)
        )
    if canonical == "Command Injection":
        return bool(re.search(r"os\.system\s*\(|subprocess\.[a-z_]+\(", code, re.IGNORECASE))
    if canonical == "Path Traversal":
        return bool(re.search(r"\b(open|read_text|write_text)\s*\(\s*\w+", code))
    if canonical == "No Input Validation":
        return "input(" in code or "request." in normalized_code or "argv" in normalized_code
    if canonical == "Hardcoded Secret":
        return bool(
            re.search(r"(api[_-]?key|secret|token|password)\s*=", code, re.IGNORECASE)
            or re.search(r"(api[_-]?key|secret|token|password)\s*[:=]\s*[\"']", line, re.IGNORECASE)
        )
    if canonical == "Global State Misuse":
        return bool(re.search(r"\bglobal\s+\w+", code) or "global variable misuse" in normalized_code)
    if canonical == "God Function":
        _, line_count = _largest_function_block(code)
        return line_count >= 20
    if canonical == "Nested Loop":
        return bool(re.search(r"for .*:\n(\s+)for .*:", code))
    if canonical == "Unbounded Memory Growth":
        return bool(re.search(r"\.append\(", code) and re.search(r"for\s+\w+\s+in\s+range\(", code))
    return True


def heuristic_dimension_findings(code: str, dimension: str) -> FindingCollection:
    findings: list[FindingCandidate] = []
    normalized_code = code.lower()

    def add(issue_type: str, vulnerable_line: str, pattern: str, scenario: str, fix: str, confidence: float) -> None:
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

    if dimension == "security":
        if re.search(r"select .*where .*['\"]\s*\+\s*\w+", normalized_code) or re.search(r"query\s*=\s*f[\"']", code):
            add(
                "SQL Injection",
                matching_line(code, r"select .*where .*[\+{]|query\s*=\s*f[\"']"),
                "User-controlled data is concatenated or interpolated into an SQL query.",
                "An attacker can inject crafted SQL input to read or modify data.",
                "Use parameterized queries and pass user input as bound parameters.",
                0.98,
            )
        if re.search(r"os\.system\s*\(", code) or re.search(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True", code):
            add(
                "Command Injection",
                matching_line(code, r"os\.system|subprocess\."),
                "Untrusted input is passed to a shell command.",
                "An attacker can execute arbitrary shell commands through crafted input.",
                "Use a safe subprocess API with argument lists and validate allowed commands.",
                0.97,
            )
        if re.search(r"open\s*\(\s*\w+\s*,", code):
            add(
                "Path Traversal",
                matching_line(code, r"open\s*\("),
                "A user-controlled filename is opened without path validation.",
                "An attacker can read unintended files by supplying traversal sequences or sensitive paths.",
                "Restrict file access to an allowlisted base directory and validate the requested path.",
                0.9,
            )
        if "input(" in code:
            add(
                "No Input Validation",
                matching_line(code, r"input\s*\(") or matching_line(code, r"def\s+get_.*input"),
                "User input is accepted and consumed without validation.",
                "Malformed or hostile input can reach sensitive operations without being constrained first.",
                "Validate user input against expected formats before using it in queries, files, or commands.",
                0.83,
            )

    if dimension == "quality":
        if re.search(r"global\s+\w+", code) or "global variable misuse" in normalized_code:
            add(
                "Global State Misuse",
                matching_line(code, r"global\s+\w+") or matching_line(code, r"#\s*global"),
                "The function relies on shared mutable state instead of isolated responsibilities.",
                "This increases coupling, makes behavior harder to reason about, and complicates testing.",
                "Refactor the function to avoid shared global state and separate responsibilities.",
                0.86,
            )
        if _function_line_count(code) >= 20:
            function_line, function_line_count = _largest_function_block(code)
            if function_line_count >= 20:
                add(
                    "God Function",
                    function_line,
                    "A function or workflow is doing too many unrelated tasks.",
                    "This reduces readability and makes bugs harder to isolate or fix safely.",
                    "Split the large function into smaller functions with a single responsibility each.",
                    0.74,
                )

    if dimension == "performance":
        if re.search(r"for .*:\n(\s+)for .*:", code):
            add(
                "Nested Loop",
                matching_line(code, r"for .*:"),
                "Nested loops create O(n^2) work for this operation.",
                "Large inputs will grow runtime quadratically and degrade responsiveness.",
                "Use a more efficient algorithm or precomputed lookups to avoid nested scans.",
                0.88,
            )
        if re.search(r"for\s+\w+\s+in\s+range\(\s*\d{5,}\s*\):", code) and re.search(r"\.append\(", code):
            add(
                "Unbounded Memory Growth",
                matching_line(code, r"\.append\("),
                "The code appends into a long-lived collection inside a very large loop.",
                "Repeated execution can cause avoidable memory growth and poor runtime behavior.",
                "Stream, batch, or reset collection state instead of appending unbounded data.",
                0.84,
            )

    return FindingCollection(findings=findings)


def matching_line(code: str, pattern: str) -> str:
    for line in code.splitlines():
        if re.search(pattern, line, flags=re.IGNORECASE):
            return line.strip()
    return ""


def _function_line_count(code: str) -> int:
    return len([line for line in code.splitlines() if line.strip() and not line.strip().startswith("#")])


def _largest_function_block(code: str) -> tuple[str, int]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return matching_line(code, r"def\s+\w+\("), _function_line_count(code)

    best_line = ""
    best_count = 0
    lines = code.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            if start <= 0 or end < start:
                continue
            line_count = end - start + 1
            if line_count > best_count:
                best_count = line_count
                best_line = lines[start - 1].strip() if start - 1 < len(lines) else ""
    return best_line, best_count
