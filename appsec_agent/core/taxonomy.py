from __future__ import annotations


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


def normalize_vulnerability_type(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""
    if value in SEVERITY_MAP:
        return value

    lowered = value.lower()
    if lowered in _ALIASES:
        return _ALIASES[lowered]

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
