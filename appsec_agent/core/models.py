from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from appsec_agent.core.taxonomy import normalize_vulnerability_type


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
    def from_payload(cls, payload: dict[str, Any], mode: AnalysisMode) -> "PlanningResult":
        return cls(
            intent=str(payload.get("intent", "")).strip(),
            entry_points=_coerce_str_list(payload.get("entry_points")),
            sensitive_operations=_coerce_str_list(payload.get("sensitive_operations")),
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
    def from_payload(cls, payload: dict[str, Any]) -> "SecurityAssessment":
        return cls(
            severity=str(payload.get("severity", "NONE")).strip() or "NONE",
            owasp_category=str(payload.get("owasp_category", "")).strip(),
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
