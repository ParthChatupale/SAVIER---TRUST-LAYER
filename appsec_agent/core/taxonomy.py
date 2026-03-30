from __future__ import annotations

import re


SEVERITY_MAP = {
    "SQL Injection": "CRITICAL",
    "Command Injection": "CRITICAL",
    "Hardcoded Secret": "HIGH",
    "XSS": "HIGH",
    "Path Traversal": "HIGH",
    "Insecure Deserialization": "HIGH",
    "Broken Authentication": "HIGH",
    "Sensitive Data Exposure": "MEDIUM",
    "Security Misconfiguration": "MEDIUM",
    "God Function": "MEDIUM",
    "Missing Error Handling": "MEDIUM",
    "No Input Validation": "HIGH",
    "Magic Numbers": "LOW",
    "Missing Type Hints": "LOW",
    "N+1 Query": "HIGH",
    "Nested Loop": "MEDIUM",
    "Missing Cache": "MEDIUM",
    "Blocking IO": "HIGH",
    "Redundant Computation": "LOW",
}

OWASP_CATEGORY_MAP = {
    "SQL Injection": "A03:2021 - Injection",
    "Command Injection": "A03:2021 - Injection",
    "Hardcoded Secret": "A02:2021 - Cryptographic Failures",
    "XSS": "A03:2021 - Injection",
    "Path Traversal": "A01:2021 - Broken Access Control",
    "Insecure Deserialization": "A08:2021 - Software and Data Integrity Failures",
    "Broken Authentication": "A07:2021 - Identification and Authentication Failures",
    "Sensitive Data Exposure": "A02:2021 - Cryptographic Failures",
    "Security Misconfiguration": "A05:2021 - Security Misconfiguration",
}

FIX_TEMPLATE_MAP = {
    "SQL Injection": (
        "Use a parameterized query instead of string concatenation, for example: "
        "\"SELECT * FROM users WHERE id = ?\" and call db.execute(query, (user_id,))."
    ),
    "Command Injection": (
        "Avoid passing untrusted input into shell commands. Use a safe API with argument lists "
        "and validate or allowlist user-controlled values."
    ),
    "Hardcoded Secret": (
        "Remove the secret from source code and load it from environment variables or a dedicated secrets manager."
    ),
    "XSS": (
        "Escape or encode untrusted output before rendering it in HTML, and use framework-safe templating by default."
    ),
    "Path Traversal": (
        "Validate and normalize the user-supplied path, then enforce that the final resolved path stays within an allowed base directory."
    ),
    "Insecure Deserialization": (
        "Do not deserialize untrusted input into executable objects. Use a safe data format and validate the parsed structure explicitly."
    ),
    "Broken Authentication": (
        "Add strong authentication checks, enforce session validation, and avoid trusting user identity without verification."
    ),
    "Sensitive Data Exposure": (
        "Protect sensitive data with appropriate encryption, avoid logging secrets, and limit exposure in responses."
    ),
    "Security Misconfiguration": (
        "Apply secure defaults, remove unnecessary functionality, and explicitly configure the component for the intended security posture."
    ),
    "God Function": (
        "Split this function into smaller focused functions so each one has a single responsibility and clearer inputs and outputs."
    ),
    "Missing Error Handling": (
        "Wrap the risky operation in explicit error handling and return or log a controlled failure path instead of letting it fail silently."
    ),
    "No Input Validation": (
        "Validate and reject malformed or unsafe input before using it in business logic, file paths, or database operations."
    ),
    "Magic Numbers": (
        "Replace hard-coded numbers with named constants so their purpose is clear and easier to change safely."
    ),
    "Missing Type Hints": (
        "Add explicit type hints for parameters and return values to make contracts clearer and improve static analysis."
    ),
    "N+1 Query": (
        "Batch the data fetch into a single query or a small fixed number of queries instead of executing one query per item in the loop."
    ),
    "Nested Loop": (
        "Reduce the nested-loop work by precomputing lookups, using a set or dict, or restructuring the algorithm to avoid O(n^2) behavior."
    ),
    "Missing Cache": (
        "Cache repeated expensive reads or computations behind a clear invalidation strategy so identical requests do not recompute the same result."
    ),
    "Blocking IO": (
        "Move blocking I/O off the async path or switch to a non-blocking API so it does not stall the event loop."
    ),
    "Redundant Computation": (
        "Compute the expensive value once and reuse it instead of recomputing the same result multiple times."
    ),
}

_ALIASES = {
    "sql injection vulnerability": "SQL Injection",
    "sqli": "SQL Injection",
    "hardcoded api key": "Hardcoded Secret",
    "hard-coded secret": "Hardcoded Secret",
    "hardcoded secret": "Hardcoded Secret",
    "cross site scripting": "XSS",
    "cross-site scripting": "XSS",
    "xss vulnerability": "XSS",
    "god method": "God Function",
    "god function": "God Function",
    "n+1 query problem": "N+1 Query",
    "n+1 queries": "N+1 Query",
    "nested loops": "Nested Loop",
    "missing type hints": "Missing Type Hints",
}

_OWASP_ALIASES = {
    "a03": "A03:2021 - Injection",
    "injection": "A03:2021 - Injection",
    "a02": "A02:2021 - Cryptographic Failures",
    "cryptographic failures": "A02:2021 - Cryptographic Failures",
    "a01": "A01:2021 - Broken Access Control",
    "broken access control": "A01:2021 - Broken Access Control",
    "a05": "A05:2021 - Security Misconfiguration",
    "security misconfiguration": "A05:2021 - Security Misconfiguration",
    "a07": "A07:2021 - Identification and Authentication Failures",
    "identification and authentication failures": "A07:2021 - Identification and Authentication Failures",
    "a08": "A08:2021 - Software and Data Integrity Failures",
    "software and data integrity failures": "A08:2021 - Software and Data Integrity Failures",
}

VALID_SEVERITIES = {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}


def normalize_vulnerability_type(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""
    value = re.sub(r"\s*\([^)]*\)", "", value).strip()
    if value in SEVERITY_MAP:
        return value

    lowered = value.lower()
    if lowered in _ALIASES:
        return _ALIASES[lowered]

    if "sql injection" in lowered:
        return "SQL Injection"
    if "hardcoded secret" in lowered or "hard-coded secret" in lowered:
        return "Hardcoded Secret"
    if "path traversal" in lowered:
        return "Path Traversal"
    if "xss" in lowered or "cross site scripting" in lowered or "cross-site scripting" in lowered:
        return "XSS"

    for alias, canonical in _ALIASES.items():
        if alias in lowered:
            return canonical
    for canonical in SEVERITY_MAP:
        if canonical.lower() == lowered:
            return canonical
    return value


def severity_for_issue(vuln_type: str, repeat_offender: bool = False) -> str:
    canonical = normalize_vulnerability_type(vuln_type)
    severity = SEVERITY_MAP.get(canonical, "MEDIUM")
    if repeat_offender and severity != "CRITICAL":
        return "HIGH"
    return severity


def normalize_severity(raw_value: str, vuln_type: str = "", repeat_offender: bool = False) -> str:
    canonical = severity_for_issue(vuln_type, repeat_offender=repeat_offender) if vuln_type else ""
    value = (raw_value or "").strip()
    if not value:
        return canonical or "MEDIUM"

    normalized = value.upper()
    if normalized in VALID_SEVERITIES:
        if canonical:
            return canonical
        return normalized

    for severity in VALID_SEVERITIES:
        if severity.lower() == value.lower():
            if canonical:
                return canonical
            return severity

    return canonical or "MEDIUM"


def canonical_owasp_category_for_issue(vuln_type: str) -> str:
    canonical = normalize_vulnerability_type(vuln_type)
    return OWASP_CATEGORY_MAP.get(canonical, "")


def normalize_owasp_category(raw_value: str, vuln_type: str = "") -> str:
    value = (raw_value or "").strip()
    if not value:
        return canonical_owasp_category_for_issue(vuln_type)

    lowered = value.lower()
    for alias, canonical in _OWASP_ALIASES.items():
        if alias in lowered:
            canonical_for_issue = canonical_owasp_category_for_issue(vuln_type)
            if canonical_for_issue:
                return canonical_for_issue
            return canonical

    canonical_for_issue = canonical_owasp_category_for_issue(vuln_type)
    if canonical_for_issue:
        return canonical_for_issue
    return value


def normalize_suggested_fix(raw_value: str, vuln_type: str = "", vulnerable_line: str = "") -> str:
    canonical = FIX_TEMPLATE_MAP.get(normalize_vulnerability_type(vuln_type), "")
    if canonical:
        return canonical

    value = (raw_value or "").strip()
    if value and value != vulnerable_line.strip():
        return value
    return "Refactor this code to remove the identified risk and apply the safe pattern for this operation."
