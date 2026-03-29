from __future__ import annotations

from dataclasses import dataclass

from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import (
    AgentTraceEntry,
    AnalysisRequest,
    AnalysisResponse,
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
            return response

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

        return response

    def _run_pipeline(self, context: ExecutionContext) -> bool:
        for spec in self.registry.get_enabled_agents(self.config):
            should_continue = self._run_agent(spec, context)
            if not should_continue:
                return False
        return True

    def _run_agent(self, spec: AgentSpec, context: ExecutionContext) -> bool:
        model_name = context.model_for(spec)
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
