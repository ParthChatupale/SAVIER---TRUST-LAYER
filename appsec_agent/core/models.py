from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Literal

from appsec_agent.core.taxonomy import (
    normalize_owasp_category,
    normalize_severity,
    normalize_suggested_fix,
    normalize_vulnerability_type,
)


AnalysisMode = Literal["security", "quality", "performance", "full"]
VALID_MODES = {"security", "quality", "performance", "full"}


@dataclass(slots=True)
class AnalysisRequest:
    code: str
    developer_id: str = "anonymous"
    mode: AnalysisMode = "security"
    debug: bool = False

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise ValueError(f"Unsupported analysis mode: {self.mode}")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> "AnalysisRequest":
        payload = payload or {}
        return cls(
            code=str(payload.get("code", "")),
            developer_id=str(payload.get("developer_id", "anonymous")),
            mode=str(payload.get("mode", "security")),  # type: ignore[arg-type]
            debug=bool(payload.get("debug", False)),
        )


@dataclass(slots=True)
class DeveloperFinding:
    vuln_type: str
    code_snippet: str
    explanation: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PlanningResult:
    intent: str = ""
    entry_points: list[str] = field(default_factory=list)
    sensitive_operations: list[str] = field(default_factory=list)
    security_focus: list[str] = field(default_factory=list)
    mode: AnalysisMode = "security"

    @classmethod
    def from_payload(cls, payload: dict[str, Any], mode: AnalysisMode, code: str = "") -> "PlanningResult":
        intent = str(payload.get("intent", "")).strip()
        if _is_generic_intent(intent, mode):
            intent = _fallback_intent(code)
        entry_points = _normalize_entry_points(_coerce_str_list(payload.get("entry_points")), code)
        sensitive_operations = _normalize_sensitive_operations(
            _coerce_str_list(payload.get("sensitive_operations")),
            code,
        )
        return cls(
            intent=intent,
            entry_points=entry_points,
            sensitive_operations=sensitive_operations,
            security_focus=_coerce_str_list(payload.get("security_focus")),
            mode=mode,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FindingCandidate:
    vuln_found: bool = False
    vuln_type: str = ""
    vulnerable_line: str = ""
    pattern: str = ""
    attack_scenario: str = ""
    suggested_fix: str = ""
    confidence: float = 0.0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "FindingCandidate":
        vuln_found = bool(payload.get("vuln_found", False))
        vuln_type = normalize_vulnerability_type(str(payload.get("vuln_type", "")).strip())
        candidate = cls(
            vuln_found=vuln_found,
            vuln_type=vuln_type,
            vulnerable_line=str(payload.get("vulnerable_line", "")).strip(),
            pattern=str(payload.get("pattern", "")).strip(),
            attack_scenario=str(payload.get("attack_scenario", "")).strip(),
            suggested_fix=str(payload.get("suggested_fix", "")).strip(),
            confidence=_coerce_confidence(payload.get("confidence", 0.0)),
        )
        if candidate.vuln_found and not candidate.vuln_type:
            raise ValueError("Finding candidate reported a vulnerability without a vulnerability type.")
        if candidate.vuln_found:
            candidate.suggested_fix = normalize_suggested_fix(
                candidate.suggested_fix,
                vuln_type=candidate.vuln_type,
                vulnerable_line=candidate.vulnerable_line,
            )
        return candidate

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SecurityAssessment:
    severity: str = "NONE"
    owasp_category: str = ""
    cve_reference: str = ""
    data_flow: str = ""
    developer_note: str = ""
    full_explanation: str = ""

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        vuln_type: str = "",
        repeat_offender: bool = False,
    ) -> "SecurityAssessment":
        return cls(
            severity=normalize_severity(
                str(payload.get("severity", "NONE")).strip(),
                vuln_type=vuln_type,
                repeat_offender=repeat_offender,
            ),
            owasp_category=normalize_owasp_category(
                str(payload.get("owasp_category", "")).strip(),
                vuln_type=vuln_type,
            ),
            cve_reference=str(payload.get("cve_reference", "")).strip(),
            data_flow=str(payload.get("data_flow", "")).strip(),
            developer_note=str(payload.get("developer_note", "")).strip(),
            full_explanation=str(payload.get("full_explanation", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentTraceEntry:
    name: str
    stage: str
    status: str
    model: str
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisResponse:
    status: str
    developer_id: str
    mode: AnalysisMode
    vuln_found: bool = False
    vuln_type: str = ""
    severity: str = "NONE"
    owasp_category: str = ""
    vulnerable_line: str = ""
    attack_scenario: str = ""
    suggested_fix: str = ""
    data_flow: str = ""
    developer_note: str = ""
    full_explanation: str = ""
    confidence: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    agent_trace: list[AgentTraceEntry] = field(default_factory=list)
    planning: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["agent_trace"] = [entry.to_dict() for entry in self.agent_trace]
        return data


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text or text.upper() == "NONE":
            return []
        return [item.strip() for item in text.split(",") if item.strip()]
    return []


def _coerce_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def _is_generic_intent(intent: str, mode: AnalysisMode) -> bool:
    if not intent:
        return True
    lowered = intent.lower().strip()
    if lowered == mode:
        return True
    return lowered in VALID_MODES


def _fallback_intent(code: str) -> str:
    function_names = re.findall(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
    if function_names:
        return f"Implements logic in function(s): {', '.join(function_names[:3])}."
    return "Analyze the provided code snippet and determine what it is trying to do."


def _normalize_entry_points(values: list[str], code: str) -> list[str]:
    cleaned = [value for value in values if not _is_generic_entry_point(value)]
    if cleaned:
        return cleaned
    return _extract_function_parameters(code)


def _normalize_sensitive_operations(values: list[str], code: str) -> list[str]:
    cleaned = [
        value
        for value in values
        if not _looks_like_issue_label(value) and not _is_generic_sensitive_operation(value)
    ]
    if cleaned:
        return cleaned
    return _extract_sensitive_operations(code)


def _is_generic_entry_point(value: str) -> bool:
    lowered = value.lower().strip()
    generic_markers = {
        "function definitions",
        "database access",
        "user authentication",
        "user input",
        "request handling",
    }
    return lowered in generic_markers


def _is_generic_sensitive_operation(value: str) -> bool:
    lowered = value.lower().strip()
    generic_markers = {
        "database access",
        "file access",
        "network access",
        "security review",
        "security audit",
    }
    return lowered in generic_markers


def _looks_like_issue_label(value: str) -> bool:
    lowered = value.lower()
    markers = ("injection", "xss", "secret", "auth issue", "vulnerability", "traversal")
    return any(marker in lowered for marker in markers)


def _extract_function_parameters(code: str) -> list[str]:
    matches = re.findall(r"def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(([^)]*)\)", code)
    params: list[str] = []
    for match in matches:
        for raw_param in match.split(","):
            param = raw_param.strip()
            if not param:
                continue
            param = param.split(":")[0].split("=")[0].strip()
            if param and param not in {"self", "cls"} and param not in params:
                params.append(param)
    return params[:5]


def _extract_sensitive_operations(code: str) -> list[str]:
    patterns = [
        (r"db\.execute\s*\(", "db.execute(...)"),
        (r"open\s*\(", "open(...)"),
        (r"requests\.(get|post|put|delete)\s*\(", "requests.<method>(...)"),
        (r"subprocess\.", "subprocess call"),
        (r"os\.system\s*\(", "os.system(...)"),
        (r"eval\s*\(", "eval(...)"),
        (r"exec\s*\(", "exec(...)"),
    ]
    operations: list[str] = []
    for pattern, label in patterns:
        if re.search(pattern, code) and label not in operations:
            operations.append(label)
    return operations
