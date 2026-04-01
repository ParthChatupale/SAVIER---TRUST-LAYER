from __future__ import annotations

from dataclasses import dataclass

from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import (
    AgentTraceEntry,
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
from appsec_agent.core.taxonomy import severity_for_issue
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.base import ModelProvider, ProviderError


@dataclass(slots=True)
class AnalysisService:
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

        if context.finding is None:
            response.status = "failed"
            response.errors.append("Pipeline completed without a finding result.")
            return response

        response.vuln_found = context.finding.vuln_found
        response.vuln_type = context.finding.vuln_type
        response.vulnerable_line = context.finding.vulnerable_line
        response.attack_scenario = context.finding.attack_scenario
        response.suggested_fix = context.finding.suggested_fix
        response.confidence = context.finding.confidence

        if not context.finding.vuln_found:
            response.full_explanation = "No vulnerability detected in this code snippet."
            response.developer_note = "No vulnerability found. Code looks clean."
        else:
            if context.security is None:
                response.severity = severity_for_issue(context.finding.vuln_type)
                if response.status == "success":
                    response.status = "partial"
            else:
                response.severity = context.security.severity
                response.owasp_category = context.security.owasp_category
                response.data_flow = context.security.data_flow
                response.developer_note = context.security.developer_note
                response.full_explanation = context.security.full_explanation

            try:
                self.repository.save_finding(
                    developer=request.developer_id,
                    vuln_type=response.vuln_type,
                    code_snippet=request.code[:200],
                    explanation=response.full_explanation or response.attack_scenario,
                )
            except Exception as exc:  # pragma: no cover - defensive guard
                response.warnings.append(f"Could not save finding history: {exc}")
                if response.status == "success":
                    response.status = "partial"

        self._enrich_with_revision_state(request, response)
        return response

    def get_dashboard_summary(self, developer_id: str) -> dict[str, object]:
        return self.repository.get_dashboard_summary(developer_id).to_dict()

    def get_analysis_timeline(self, developer_id: str, file_uri: str | None = None, limit: int = 20) -> list[dict[str, object]]:
        return [event.to_dict() for event in self.repository.list_analysis_events(developer_id, file_uri=file_uri, limit=limit)]

    def get_file_state(self, developer_id: str, file_uri: str) -> dict[str, object] | None:
        state = self.repository.get_file_state(developer_id, file_uri)
        return state.to_dict() if state is not None else None

    def _run_pipeline(self, context: ExecutionContext) -> bool:
        for spec in self.registry.get_enabled_agents(self.config):
            should_continue = self._run_agent(spec, context)
            if not should_continue:
                return False
        return True

    def _run_agent(self, spec: AgentSpec, context: ExecutionContext) -> bool:
        model_name = context.model_for(spec)
        if spec.should_run is not None and not spec.should_run(context):
            context.response.agent_trace.append(
                AgentTraceEntry(
                    name=spec.name,
                    stage=spec.stage,
                    status="skipped",
                    model=model_name,
                )
            )
            return True
        try:
            spec.runner(context)
        except ProviderError as exc:
            self._record_failure(spec, context.response, model_name, str(exc), required=spec.required)
            return False if spec.required else True
        except Exception as exc:
            self._record_failure(spec, context.response, model_name, str(exc), required=spec.required)
            return False if spec.required else True

        context.response.agent_trace.append(
            AgentTraceEntry(
                name=spec.name,
                stage=spec.stage,
                status="success",
                model=model_name,
            )
        )
        return True

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
        response.agent_trace.append(
            AgentTraceEntry(
                name=spec.name,
                stage=spec.stage,
                status="failed",
                model=model_name,
                error=error,
            )
        )

    def _enrich_with_revision_state(self, request: AnalysisRequest, response: AnalysisResponse) -> None:
        findings = FindingRecord.from_analysis(
            mode=request.mode,
            vuln_found=response.vuln_found,
            vuln_type=response.vuln_type,
            severity=response.severity,
            vulnerable_line=response.vulnerable_line,
            explanation=response.full_explanation or response.attack_scenario or response.developer_note,
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
        if previous_state is not None and previous_state.content_hash == content_hash:
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
            project_id=request.project_id or "",
            scores=scores,
            findings=findings,
            diff=diff,
            summary={
                "vuln_type": response.vuln_type,
                "severity": response.severity,
                "status": response.status,
            },
        )
        stored_event = self.repository.insert_analysis_event(event)
        self.repository.upsert_file_state(
            FileState(
                developer_id=request.developer_id,
                file_uri=request.file_uri,
                content_hash=content_hash,
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
