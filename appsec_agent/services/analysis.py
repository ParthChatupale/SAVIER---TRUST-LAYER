from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256

from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import (
    AggregatedReviewResult,
    AgentTraceEntry,
    AnalysisProfile,
    AnalysisEvent,
    AnalysisRequest,
    AnalysisResponse,
    FileState,
    FindingRecord,
    code_content_hash,
    diff_findings,
    merge_dimension_scores,
)
from appsec_agent.core.plugins import AgentRegistry, AgentSpec, ExecutionContext
from appsec_agent.core.taxonomy import normalize_severity, severity_for_issue
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.base import ModelProvider, ProviderError


@dataclass(slots=True)
class AnalysisService:
    PIPELINE_FINGERPRINT_VERSION = "pipeline-v2.1-normalized"

    config: AppConfig
    provider: ModelProvider
    repository: SQLiteFindingsRepository
    registry: AgentRegistry

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        response = AnalysisResponse(
            status="success",
            developer_id=request.developer_id,
            mode=request.mode,
            file_uri=request.file_uri or "",
        )

        if not request.code.strip():
            response.status = "failed"
            response.errors.append("No code provided.")
            return response

        history = self.repository.get_developer_history(request.developer_id)
        context = ExecutionContext(
            config=self.config,
            request=request,
            response=response,
            provider=self.provider,
            repository=self.repository,
            history=history,
        )

        if not self._run_pipeline(context):
            return response

        if context.planning is not None:
            response.planning = context.planning.to_dict()

        if context.aggregation is None:
            response.status = "failed"
            response.errors.append("Pipeline completed without an aggregated review result.")
            return response

        aggregate = context.aggregation
        response.findings = [finding.to_dict() for finding in aggregate.findings]
        for finding in response.findings:
            finding["severity"] = normalize_severity("", vuln_type=str(finding.get("vuln_type", "")))
        response.dimensions = {name: result.to_dict() for name, result in aggregate.dimensions.items()}
        response.primary_finding = aggregate.primary_finding.to_dict()
        primary_finding = aggregate.primary_finding
        response.vuln_found = aggregate.vuln_found
        response.vuln_type = primary_finding.vuln_type
        response.vulnerable_line = primary_finding.vulnerable_line
        response.attack_scenario = primary_finding.explanation
        response.suggested_fix = primary_finding.suggested_fix
        response.confidence = primary_finding.confidence
        response.severity = primary_finding.severity
        profile = self._analysis_profile()
        response.analysis_profile = profile.to_dict()

        if not aggregate.vuln_found:
            response.full_explanation = "No vulnerability detected in this code snippet."
            response.developer_note = "No vulnerability found. Code looks clean."
        else:
            try:
                for finding in aggregate.findings:
                    self.repository.save_finding(
                        developer=request.developer_id,
                        vuln_type=finding.vuln_type,
                        code_snippet=(finding.vulnerable_line or request.code[:200])[:200],
                        explanation=finding.attack_scenario or finding.pattern,
                    )
            except Exception as exc:  # pragma: no cover - defensive guard
                response.warnings.append(f"Could not save finding history: {exc}")
                if response.status == "success":
                    response.status = "partial"

        self._enrich_with_revision_state(request, response, profile)
        return response

    def get_dashboard_summary(self, developer_id: str) -> dict[str, object]:
        return self.repository.get_dashboard_summary(developer_id).to_dict()

    def get_analysis_timeline(self, developer_id: str, file_uri: str | None = None, limit: int = 20) -> list[dict[str, object]]:
        return [event.to_dict() for event in self.repository.list_analysis_events(developer_id, file_uri=file_uri, limit=limit)]

    def get_file_state(self, developer_id: str, file_uri: str) -> dict[str, object] | None:
        state = self.repository.get_file_state(developer_id, file_uri)
        return state.to_dict() if state is not None else None

    def _run_pipeline(self, context: ExecutionContext) -> bool:
        enabled_specs = self.registry.get_enabled_agents(self.config)
        index = 0
        while index < len(enabled_specs):
            spec = enabled_specs[index]
            if spec.parallel_group:
                group = [spec]
                index += 1
                while index < len(enabled_specs) and enabled_specs[index].parallel_group == spec.parallel_group:
                    group.append(enabled_specs[index])
                    index += 1
                should_continue = self._run_parallel_group(group, context)
            else:
                should_continue = self._run_agent(spec, context)
                index += 1
            if not should_continue:
                return False
        return True

    def _run_agent(self, spec: AgentSpec, context: ExecutionContext) -> bool:
        result = self._execute_spec(spec, context)
        context.response.warnings.extend(result.warnings)
        context.response.agent_trace.append(
            AgentTraceEntry(
                name=spec.name,
                stage=spec.stage,
                status=result.status,
                model=result.model_name,
                error=result.error,
            )
        )
        if result.status != "failed":
            return True
        self._record_failure(spec, context.response, result.model_name, result.error, required=spec.required)
        return False if spec.required else True

    def _run_parallel_group(self, specs: list[AgentSpec], context: ExecutionContext) -> bool:
        submissions: list[tuple[AgentSpec, ExecutionContext]] = []
        for spec in specs:
            child = context.spawn_child()
            submissions.append((spec, child))

        results: list[tuple[AgentSpec, ExecutionContext, StageExecutionResult]] = []
        with ThreadPoolExecutor(max_workers=len(submissions)) as executor:
            future_map = {
                executor.submit(self._execute_spec, spec, child): (spec, child)
                for spec, child in submissions
            }
            for future, pair in future_map.items():
                spec, child = pair
                results.append((spec, child, future.result()))

        results.sort(key=lambda item: (item[0].order, item[0].name))
        runnable = 0
        successes = 0
        failures: list[tuple[AgentSpec, StageExecutionResult]] = []
        for spec, child, result in results:
            context.response.warnings.extend(result.warnings)
            context.response.warnings.extend(child.response.warnings)
            context.response.agent_trace.append(
                AgentTraceEntry(
                    name=spec.name,
                    stage=spec.stage,
                    status=result.status,
                    model=result.model_name,
                    error=result.error,
                )
            )
            if result.status == "skipped":
                continue
            runnable += 1
            if result.status == "success":
                successes += 1
                if spec.artifact_key and spec.artifact_key in child.artifacts:
                    context.set_artifact(spec.artifact_key, child.get_artifact(spec.artifact_key))
            else:
                failures.append((spec, result))

        if failures and successes:
            if context.response.status == "success":
                context.response.status = "partial"
            context.response.warnings.extend(result.error for _, result in failures if result.error)
            return True

        if failures and not successes and runnable:
            context.response.status = "failed"
            context.response.errors.extend(result.error for _, result in failures if result.error)
            return False

        return True

    def _execute_spec(self, spec: AgentSpec, context: ExecutionContext) -> "StageExecutionResult":
        model_candidates = context.model_candidates_for(spec)
        model_name = model_candidates[0]
        warnings: list[str] = []
        if spec.should_run is not None and not spec.should_run(context):
            return StageExecutionResult(status="skipped", model_name=model_name)
        for candidate in model_candidates:
            context.metadata["active_model"] = candidate
            try:
                spec.runner(context)
                context.metadata.pop("active_model", None)
                return StageExecutionResult(status="success", model_name=candidate, warnings=warnings)
            except ProviderError as exc:
                if candidate != model_candidates[-1]:
                    warnings.append(f"{spec.stage} stage fallback from {candidate} to next model: {exc}")
                    continue
                context.metadata.pop("active_model", None)
                return StageExecutionResult(status="failed", model_name=candidate, error=str(exc), warnings=warnings)
            except Exception as exc:
                context.metadata.pop("active_model", None)
                return StageExecutionResult(status="failed", model_name=candidate, error=str(exc), warnings=warnings)
        context.metadata.pop("active_model", None)
        return StageExecutionResult(status="failed", model_name=model_name, error=f"{spec.stage} stage failed", warnings=warnings)

    def _record_failure(
        self,
        spec: AgentSpec,
        response: AnalysisResponse,
        model_name: str,
        error: str,
        *,
        required: bool,
    ) -> None:
        if required:
            response.status = "failed"
            response.errors.append(error)
        else:
            response.warnings.append(error)
            if response.status == "success":
                response.status = "partial"

    def _enrich_with_revision_state(self, request: AnalysisRequest, response: AnalysisResponse, profile: AnalysisProfile) -> None:
        findings = FindingRecord.from_analysis(
            mode=request.mode,
            findings=context_finding_candidates(response),
        )
        previous_state = self.repository.get_file_state(request.developer_id, request.file_uri) if request.file_uri else None
        evaluated_dimensions = self._evaluated_dimensions(request.mode, findings)
        scores = merge_dimension_scores(
            previous=previous_state.scores if previous_state is not None else None,
            findings=findings,
            evaluated_dimensions=evaluated_dimensions,
        )
        diff = diff_findings(
            previous=previous_state.findings if previous_state is not None else [],
            current=findings,
            previous_scores=previous_state.scores if previous_state is not None else None,
            current_scores=scores,
        )

        response.scores = scores.to_dict()
        response.diff = diff.to_dict()

        if not request.file_uri:
            return

        content_hash = code_content_hash(request.code)
        if (
            previous_state is not None
            and previous_state.content_hash == content_hash
            and previous_state.analysis_profile == profile.fingerprint
        ):
            response.event_id = previous_state.last_event_id
            return

        event = AnalysisEvent(
            event_id="",
            developer_id=request.developer_id,
            file_uri=request.file_uri,
            source=request.source,
            mode=request.mode,
            content_hash=content_hash,
            status=response.status,
            analysis_profile=profile.fingerprint,
            project_id=request.project_id or "",
            scores=scores,
            findings=findings,
            diff=diff,
            summary={
                "vuln_type": response.vuln_type,
                "severity": response.severity,
                "status": response.status,
                "finding_count": len(findings),
                "dimensions": response.dimensions,
                "primary_finding": response.primary_finding,
            },
        )
        stored_event = self.repository.insert_analysis_event(event)
        self.repository.upsert_file_state(
            FileState(
                developer_id=request.developer_id,
                file_uri=request.file_uri,
                content_hash=content_hash,
                analysis_profile=profile.fingerprint,
                last_event_id=stored_event.event_id,
                source=request.source,
                mode=request.mode,
                status=response.status,
                updated_at=stored_event.timestamp,
                project_id=request.project_id or "",
                scores=scores,
                findings=findings,
            )
        )
        response.event_id = stored_event.event_id

    def _evaluated_dimensions(self, mode: str, findings: list[FindingRecord]) -> list[str]:
        if mode == "full":
            return ["security", "quality", "performance"]
        if findings:
            dimensions = {finding.dimension for finding in findings}
            if dimensions:
                return sorted(dimensions)
        if mode in {"security", "quality", "performance"}:
            return [mode]
        return ["security"]

    def _analysis_profile(self) -> AnalysisProfile:
        enabled_agents = [spec.name for spec in self.registry.get_enabled_agents(self.config)]
        model_profile = {
            "planning": self.config.model_planning,
            "security_review": self.config.model_security_review,
            "quality_review": self.config.model_quality_review,
            "performance_review": self.config.model_performance_review,
            "aggregation": self.config.model_aggregation,
        }
        fingerprint_source = "|".join(
            [
                self.PIPELINE_FINGERPRINT_VERSION,
                self.config.provider_name,
                ",".join(enabled_agents),
                *[f"{key}={value}" for key, value in sorted(model_profile.items())],
            ]
        )
        fingerprint = sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
        return AnalysisProfile(
            pipeline_version="v2-specialist-r2",
            provider=self.config.provider_name,
            enabled_agents=enabled_agents,
            model_profile=model_profile,
            fingerprint=fingerprint,
        )


def context_finding_candidates(response: AnalysisResponse):
    from appsec_agent.core.models import FindingCandidate

    candidates: list[FindingCandidate] = []
    for finding in response.findings:
        if not isinstance(finding, dict):
            continue
        payload = dict(finding)
        if not payload.get("suggested_fix"):
            payload["suggested_fix"] = response.suggested_fix
        if not payload.get("attack_scenario"):
            payload["attack_scenario"] = response.attack_scenario or response.developer_note
        candidates.append(FindingCandidate.from_payload(payload, mode=response.mode))
    if candidates:
        return candidates
    if not response.vuln_found:
        return []
    return [
        FindingCandidate.from_payload(
            {
                "dimension": "",
                "vuln_found": response.vuln_found,
                "vuln_type": response.vuln_type,
                "vulnerable_line": response.vulnerable_line,
                "pattern": "",
                "attack_scenario": response.attack_scenario or response.full_explanation or response.developer_note,
                "suggested_fix": response.suggested_fix,
                "confidence": response.confidence,
            },
            mode=response.mode,
        )
    ]


@dataclass(slots=True)
class StageExecutionResult:
    status: str
    model_name: str
    error: str = ""
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
