from __future__ import annotations

from dataclasses import dataclass

from appsec_agent.agents.coding import coding_agent
from appsec_agent.agents.planning import planning_agent
from appsec_agent.agents.security import security_agent
from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import (
    AgentTraceEntry,
    AnalysisRequest,
    AnalysisResponse,
    FindingCandidate,
    PlanningResult,
    SecurityAssessment,
)
from appsec_agent.core.taxonomy import severity_for_issue
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.base import ModelOutputError, ModelProvider, ProviderError


@dataclass(slots=True)
class AnalysisService:
    config: AppConfig
    provider: ModelProvider
    repository: SQLiteFindingsRepository

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

        planning = self._run_planning(request, history, response)
        if planning is None:
            return response

        finding = self._run_coding(request, planning, response)
        if finding is None:
            response.planning = planning.to_dict()
            return response

        response.planning = planning.to_dict()
        response.vuln_found = finding.vuln_found
        response.vuln_type = finding.vuln_type
        response.vulnerable_line = finding.vulnerable_line
        response.attack_scenario = finding.attack_scenario
        response.suggested_fix = finding.suggested_fix
        response.confidence = finding.confidence

        if not finding.vuln_found:
            response.full_explanation = "No vulnerability detected in this code snippet."
            response.developer_note = "No vulnerability found. Code looks clean."
            return response

        security = self._run_security(request, finding, history, response)
        if security is None:
            response.severity = severity_for_issue(finding.vuln_type)
            if response.status == "success":
                response.status = "partial"
        else:
            response.severity = security.severity
            response.owasp_category = security.owasp_category
            response.data_flow = security.data_flow
            response.developer_note = security.developer_note
            response.full_explanation = security.full_explanation

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

    def _run_planning(
        self,
        request: AnalysisRequest,
        history: list,
        response: AnalysisResponse,
    ) -> PlanningResult | None:
        try:
            planning = planning_agent(
                provider=self.provider,
                model=self.config.model_planning,
                code=request.code,
                developer_history=[finding.to_dict() for finding in history],
                mode=request.mode,
            )
        except ProviderError as exc:
            response.status = "failed"
            response.errors.append(str(exc))
            response.agent_trace.append(
                AgentTraceEntry(
                    name="planning",
                    stage="planning",
                    status="failed",
                    model=self.config.model_planning,
                    error=str(exc),
                )
            )
            return None

        response.agent_trace.append(
            AgentTraceEntry(
                name="planning",
                stage="planning",
                status="success",
                model=self.config.model_planning,
            )
        )
        return planning

    def _run_coding(
        self,
        request: AnalysisRequest,
        planning: PlanningResult,
        response: AnalysisResponse,
    ) -> FindingCandidate | None:
        try:
            finding = coding_agent(
                provider=self.provider,
                model=self.config.model_coding,
                code=request.code,
                planning_result=planning,
            )
        except ProviderError as exc:
            response.status = "failed"
            response.errors.append(str(exc))
            response.agent_trace.append(
                AgentTraceEntry(
                    name="coding",
                    stage="coding",
                    status="failed",
                    model=self.config.model_coding,
                    error=str(exc),
                )
            )
            return None

        response.agent_trace.append(
            AgentTraceEntry(
                name="coding",
                stage="coding",
                status="success",
                model=self.config.model_coding,
            )
        )
        return finding

    def _run_security(
        self,
        request: AnalysisRequest,
        finding: FindingCandidate,
        history: list,
        response: AnalysisResponse,
    ) -> SecurityAssessment | None:
        try:
            security = security_agent(
                provider=self.provider,
                model=self.config.model_security,
                code=request.code,
                coding_result=finding,
                developer_history=[finding_item.to_dict() for finding_item in history],
            )
        except (ModelOutputError, ProviderError) as exc:
            response.warnings.append(str(exc))
            response.agent_trace.append(
                AgentTraceEntry(
                    name="security",
                    stage="security",
                    status="failed",
                    model=self.config.model_security,
                    error=str(exc),
                )
            )
            return None

        response.agent_trace.append(
            AgentTraceEntry(
                name="security",
                stage="security",
                status="success",
                model=self.config.model_security,
            )
        )
        return security
