from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import re
from typing import Any, Literal

from appsec_agent.core.taxonomy import (
    dimension_for_issue,
    is_known_issue_type,
    normalize_owasp_category,
    normalize_severity,
    normalize_suggested_fix,
    normalize_vulnerability_type,
    score_penalty_for_severity,
    severity_for_issue,
)


AnalysisMode = Literal["security", "quality", "performance", "full"]
VALID_MODES = {"security", "quality", "performance", "full"}


@dataclass(slots=True)
class AnalysisRequest:
    code: str
    developer_id: str = "anonymous"
    mode: AnalysisMode = "full"
    debug: bool = False
    file_uri: str | None = None
    source: str = "ide_extension"
    project_id: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise ValueError(f"Unsupported analysis mode: {self.mode}")

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> "AnalysisRequest":
        payload = payload or {}
        return cls(
            code=str(payload.get("code", "")),
            developer_id=str(payload.get("developer_id", "anonymous")),
            mode=str(payload.get("mode", "full")),  # type: ignore[arg-type]
            debug=bool(payload.get("debug", False)),
            file_uri=_coerce_optional_string(payload.get("file_uri")),
            source=_coerce_optional_string(payload.get("source")) or "ide_extension",
            project_id=_coerce_optional_string(payload.get("project_id")),
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
    dimension: str = ""
    vuln_found: bool = False
    vuln_type: str = ""
    vulnerable_line: str = ""
    pattern: str = ""
    attack_scenario: str = ""
    suggested_fix: str = ""
    confidence: float = 0.0

    @classmethod
    def from_payload(cls, payload: dict[str, Any], mode: AnalysisMode = "security") -> "FindingCandidate":
        vuln_found = bool(payload.get("vuln_found", False))
        vuln_type = normalize_vulnerability_type(str(payload.get("vuln_type", "")).strip())
        dimension = str(payload.get("dimension", "")).strip().lower()
        if vuln_type:
            canonical_dimension = dimension_for_issue(vuln_type, mode=mode)
            if dimension != canonical_dimension:
                dimension = canonical_dimension
        candidate = cls(
            dimension=dimension,
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
class FindingCollection:
    findings: list[FindingCandidate] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any], mode: AnalysisMode) -> "FindingCollection":
        if isinstance(payload.get("findings"), list):
            candidates = [
                FindingCandidate.from_payload(item, mode=mode)
                for item in payload.get("findings", [])
                if isinstance(item, dict)
            ]
        else:
            candidates = [FindingCandidate.from_payload(payload, mode=mode)]
        deduped: list[FindingCandidate] = []
        seen: set[tuple[str, str, str]] = set()
        for finding in candidates:
            if not finding.vuln_found or not finding.vuln_type:
                continue
            if not is_known_issue_type(finding.vuln_type):
                continue
            if not finding.dimension:
                finding.dimension = dimension_for_issue(finding.vuln_type, mode=mode)
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
            deduped.append(finding)
        return cls(findings=deduped)

    @property
    def vuln_found(self) -> bool:
        return bool(self.findings)

    def primary_finding(self) -> FindingCandidate:
        if not self.findings:
            return FindingCandidate()
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        return sorted(
            self.findings,
            key=lambda finding: (
                severity_rank.get(severity_for_issue(finding.vuln_type), 0),
                finding.confidence,
            ),
            reverse=True,
        )[0]

    def to_records(self) -> list["FindingRecord"]:
        records: list[FindingRecord] = []
        for finding in self.findings:
            normalized_type = normalize_vulnerability_type(finding.vuln_type)
            normalized_severity = normalize_severity(
                severity_for_issue(normalized_type),
                vuln_type=normalized_type,
            )
            line_or_snippet = (finding.vulnerable_line or finding.pattern or finding.attack_scenario).strip()
            dimension = finding.dimension or dimension_for_issue(normalized_type)
            key = finding_key(
                dimension=dimension,
                issue_type=normalized_type,
                line_or_snippet=line_or_snippet,
            )
            records.append(
                FindingRecord(
                    key=key,
                    dimension=dimension,
                    issue_type=normalized_type,
                    severity=normalized_severity,
                    line=finding.vulnerable_line.strip(),
                    explanation=(finding.attack_scenario or finding.pattern).strip(),
                )
            )
        return records

    def to_dict(self) -> dict[str, Any]:
        return {"findings": [finding.to_dict() for finding in self.findings]}


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
    findings: list[dict[str, Any]] = field(default_factory=list)
    dimensions: dict[str, Any] = field(default_factory=dict)
    primary_finding: dict[str, Any] = field(default_factory=dict)
    analysis_profile: dict[str, Any] = field(default_factory=dict)
    file_uri: str = ""
    event_id: str = ""
    scores: dict[str, Any] = field(default_factory=dict)
    diff: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["agent_trace"] = [entry.to_dict() for entry in self.agent_trace]
        return data


@dataclass(slots=True)
class FindingRecord:
    key: str
    dimension: str
    issue_type: str
    severity: str
    line: str = ""
    explanation: str = ""

    @classmethod
    def from_analysis(
        cls,
        *,
        mode: AnalysisMode,
        findings: list[FindingCandidate] | None = None,
        vuln_found: bool = False,
        vuln_type: str = "",
        severity: str = "NONE",
        vulnerable_line: str = "",
        explanation: str = "",
    ) -> list["FindingRecord"]:
        if findings is not None:
            collection = FindingCollection(findings=findings)
            return collection.to_records()
        if not vuln_found or not vuln_type:
            return []
        normalized_type = normalize_vulnerability_type(vuln_type)
        normalized_severity = normalize_severity(severity, vuln_type=normalized_type)
        line_or_snippet = (vulnerable_line or explanation).strip()
        dimension = dimension_for_issue(normalized_type, mode=mode)
        key = finding_key(dimension=dimension, issue_type=normalized_type, line_or_snippet=line_or_snippet)
        return [
            cls(
                key=key,
                dimension=dimension,
                issue_type=normalized_type,
                severity=normalized_severity,
                line=vulnerable_line.strip(),
                explanation=explanation.strip(),
            )
        ]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DimensionScores:
    security: int = 100
    quality: int = 100
    performance: int = 100
    overall: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DimensionAnalysisResult:
    dimension: str
    findings: list[FindingCandidate] = field(default_factory=list)
    status: str = "success"
    warnings: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def top_severity(self) -> str:
        if not self.findings:
            return "NONE"
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
        return sorted(
            (normalize_severity("", vuln_type=finding.vuln_type) for finding in self.findings),
            key=lambda severity: severity_rank.get(severity, 0),
            reverse=True,
        )[0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "status": self.status,
            "warnings": list(self.warnings),
            "summary": self.summary,
            "finding_count": self.finding_count,
            "top_severity": self.top_severity,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(slots=True)
class PrimaryFinding:
    dimension: str = ""
    vuln_type: str = ""
    severity: str = "NONE"
    vulnerable_line: str = ""
    pattern: str = ""
    explanation: str = ""
    suggested_fix: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisProfile:
    pipeline_version: str
    provider: str
    enabled_agents: list[str]
    model_profile: dict[str, str]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "provider": self.provider,
            "enabled_agents": list(self.enabled_agents),
            "model_profile": dict(self.model_profile),
            "fingerprint": self.fingerprint,
        }


@dataclass(slots=True)
class AggregatedReviewResult:
    dimensions: dict[str, DimensionAnalysisResult] = field(default_factory=dict)
    findings: list[FindingCandidate] = field(default_factory=list)
    primary_finding: PrimaryFinding = field(default_factory=PrimaryFinding)
    status: str = "success"
    warnings: list[str] = field(default_factory=list)

    @property
    def vuln_found(self) -> bool:
        return bool(self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimensions": {name: result.to_dict() for name, result in self.dimensions.items()},
            "findings": [finding.to_dict() for finding in self.findings],
            "primary_finding": self.primary_finding.to_dict(),
            "status": self.status,
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class ScoreDelta:
    score_delta: int = 0
    fixed_findings: list[str] = field(default_factory=list)
    new_findings: list[str] = field(default_factory=list)
    unchanged_findings: list[str] = field(default_factory=list)

    @property
    def fixed_count(self) -> int:
        return len(self.fixed_findings)

    @property
    def new_issue_count(self) -> int:
        return len(self.new_findings)

    @property
    def unchanged_count(self) -> int:
        return len(self.unchanged_findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score_delta": self.score_delta,
            "fixed_findings": list(self.fixed_findings),
            "new_findings": list(self.new_findings),
            "unchanged_findings": list(self.unchanged_findings),
            "fixed_count": self.fixed_count,
            "new_issue_count": self.new_issue_count,
            "unchanged_count": self.unchanged_count,
        }


@dataclass(slots=True)
class AnalysisEvent:
    event_id: str
    developer_id: str
    file_uri: str
    source: str
    mode: AnalysisMode
    content_hash: str
    status: str
    analysis_profile: str = ""
    timestamp: str = ""
    project_id: str = ""
    scores: DimensionScores = field(default_factory=DimensionScores)
    findings: list[FindingRecord] = field(default_factory=list)
    diff: ScoreDelta = field(default_factory=ScoreDelta)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "developer_id": self.developer_id,
            "file_uri": self.file_uri,
            "source": self.source,
            "mode": self.mode,
            "content_hash": self.content_hash,
            "analysis_profile": self.analysis_profile,
            "status": self.status,
            "timestamp": self.timestamp,
            "project_id": self.project_id,
            "scores": self.scores.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
            "diff": self.diff.to_dict(),
            "summary": dict(self.summary),
        }


@dataclass(slots=True)
class FileState:
    developer_id: str
    file_uri: str
    content_hash: str
    analysis_profile: str = ""
    last_event_id: str = ""
    source: str = ""
    mode: AnalysisMode = "security"
    status: str = "success"
    updated_at: str = ""
    project_id: str = ""
    scores: DimensionScores = field(default_factory=DimensionScores)
    findings: list[FindingRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "developer_id": self.developer_id,
            "file_uri": self.file_uri,
            "content_hash": self.content_hash,
            "analysis_profile": self.analysis_profile,
            "last_event_id": self.last_event_id,
            "source": self.source,
            "mode": self.mode,
            "status": self.status,
            "updated_at": self.updated_at,
            "project_id": self.project_id,
            "scores": self.scores.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(slots=True)
class DashboardSummary:
    developer_id: str
    total_files: int = 0
    total_events: int = 0
    files_with_findings: int = 0
    open_findings: int = 0
    average_scores: DimensionScores = field(default_factory=DimensionScores)
    score_trend: list[dict[str, Any]] = field(default_factory=list)
    current_files: list[FileState] = field(default_factory=list)
    recent_events: list[AnalysisEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "developer_id": self.developer_id,
            "total_files": self.total_files,
            "total_events": self.total_events,
            "files_with_findings": self.files_with_findings,
            "open_findings": self.open_findings,
            "average_scores": self.average_scores.to_dict(),
            "score_trend": [dict(item) for item in self.score_trend],
            "current_files": [state.to_dict() for state in self.current_files],
            "recent_events": [event.to_dict() for event in self.recent_events],
        }


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


def _coerce_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


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


def finding_key(*, dimension: str, issue_type: str, line_or_snippet: str) -> str:
    normalized_line = re.sub(r"\s+", " ", (line_or_snippet or "").strip()).lower()
    normalized_type = normalize_vulnerability_type(issue_type) or issue_type.strip()
    return f"{dimension}:{normalized_type}:{normalized_line}"


def finding_signature(
    *,
    dimension: str,
    issue_type: str,
    vulnerable_line: str = "",
    pattern: str = "",
    explanation: str = "",
) -> tuple[str, str, str]:
    normalized_type = normalize_vulnerability_type(issue_type) or issue_type.strip()
    normalized_dimension = dimension_for_issue(normalized_type, mode=dimension)
    dedupe_by_type = {
        "No Input Validation",
        "Nested Loop",
        "Unbounded Memory Growth",
        "Global State Misuse",
        "God Function",
    }
    if normalized_type in dedupe_by_type:
        anchor = normalized_type.lower()
    else:
        anchor_source = vulnerable_line or pattern or explanation
        anchor = re.sub(r"\s+", " ", anchor_source.strip()).lower()
        if not anchor or anchor.isdigit():
            anchor = re.sub(r"\s+", " ", (pattern or explanation or normalized_type).strip()).lower()
        if not anchor:
            anchor = normalized_type.lower()
    return (normalized_dimension, normalized_type, anchor)


def code_content_hash(code: str) -> str:
    return sha256(code.encode("utf-8")).hexdigest()


def merge_dimension_scores(
    *,
    previous: DimensionScores | None,
    findings: list[FindingRecord],
    evaluated_dimensions: list[str],
) -> DimensionScores:
    base = previous.to_dict() if previous is not None else DimensionScores().to_dict()
    dimension_penalties = {"security": 0, "quality": 0, "performance": 0}
    for finding in findings:
        dimension_penalties[finding.dimension] += score_penalty_for_severity(finding.severity)

    scores: dict[str, int] = {}
    for dimension in ("security", "quality", "performance"):
        if previous is None or dimension in evaluated_dimensions:
            scores[dimension] = max(0, 100 - dimension_penalties[dimension])
        else:
            scores[dimension] = int(base[dimension])
    scores["overall"] = round((scores["security"] + scores["quality"] + scores["performance"]) / 3)
    return DimensionScores(**scores)


def findings_for_dimension(findings: list[FindingRecord], dimension: str) -> list[FindingRecord]:
    return [finding for finding in findings if finding.dimension == dimension]


def diff_findings(
    previous: list[FindingRecord],
    current: list[FindingRecord],
    *,
    previous_scores: DimensionScores | None,
    current_scores: DimensionScores,
) -> ScoreDelta:
    previous_keys = {finding.key for finding in previous}
    current_keys = {finding.key for finding in current}

    fixed = sorted(previous_keys - current_keys)
    new = sorted(current_keys - previous_keys)
    unchanged = sorted(previous_keys & current_keys)
    previous_overall = previous_scores.overall if previous_scores is not None else current_scores.overall
    return ScoreDelta(
        score_delta=current_scores.overall - previous_overall,
        fixed_findings=fixed,
        new_findings=new,
        unchanged_findings=unchanged,
    )
