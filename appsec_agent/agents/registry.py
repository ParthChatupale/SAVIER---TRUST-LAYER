from __future__ import annotations

from appsec_agent.agents.coding import coding_agent
from appsec_agent.agents.planning import planning_agent
from appsec_agent.agents.security import security_agent
from appsec_agent.core.models import FindingCandidate, PlanningResult, SecurityAssessment
from appsec_agent.core.plugins import AgentRegistry, AgentSpec, ExecutionContext


def register_default_agents(registry: AgentRegistry) -> AgentRegistry:
    registry.register_agent(
        AgentSpec(
            name="planning",
            stage="planning",
            order=10,
            description="Identify intent, entry points, and relevant risk areas.",
            input_type=str,
            output_type=PlanningResult,
            model_config_key="model_planning",
            runner=_run_planning,
            required=True,
        )
    )
    registry.register_agent(
        AgentSpec(
            name="coding",
            stage="coding",
            order=20,
            description="Find the highest value code issue in the snippet.",
            input_type=PlanningResult,
            output_type=FindingCandidate,
            model_config_key="model_coding",
            runner=_run_coding,
            required=True,
        )
    )
    registry.register_agent(
        AgentSpec(
            name="security",
            stage="security",
            order=30,
            description="Explain severity, impact, and remediation for a finding.",
            input_type=FindingCandidate,
            output_type=SecurityAssessment,
            model_config_key="model_security",
            runner=_run_security,
            required=False,
        )
    )
    return registry


def _run_planning(context: ExecutionContext) -> None:
    context.planning = planning_agent(
        provider=context.provider,
        model=context.config.model_planning,
        code=context.request.code,
        developer_history=context.history_payload(),
        mode=context.request.mode,
    )


def _run_coding(context: ExecutionContext) -> None:
    if context.planning is None:
        raise ValueError("coding agent requires planning output.")
    context.finding = coding_agent(
        provider=context.provider,
        model=context.config.model_coding,
        code=context.request.code,
        planning_result=context.planning,
    )


def _run_security(context: ExecutionContext) -> None:
    if context.finding is None or not context.finding.vuln_found:
        return
    context.security = security_agent(
        provider=context.provider,
        model=context.config.model_security,
        code=context.request.code,
        coding_result=context.finding,
        developer_history=context.history_payload(),
    )
