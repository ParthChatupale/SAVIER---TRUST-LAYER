from __future__ import annotations

from appsec_agent.agents.review_common import run_dimension_review
from appsec_agent.core.models import DimensionAnalysisResult, PlanningResult
from appsec_agent.core.plugins import AgentSpec, ExecutionContext


def should_run_security_review(context: ExecutionContext) -> bool:
    return context.request.mode in {"security", "full"}


def run_security_review(context: ExecutionContext) -> None:
    planning_result = context.get_artifact("planning")
    if planning_result is None:
        raise ValueError("security_review requires planning output.")
    result = run_dimension_review(
        provider=context.provider,
        model=context.metadata.get("active_model", context.config.model_security_review),
        code=context.request.code,
        planning_result=planning_result,
        dimension="security",
    )
    context.set_artifact("security_review", result)


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="security_review",
        stage="security_review",
        order=20,
        description="Find security-specific issues in the snippet.",
        input_type=PlanningResult,
        output_type=DimensionAnalysisResult,
        model_config_key="model_security_review",
        artifact_key="security_review",
        should_run=should_run_security_review,
        parallel_group="dimension_reviews",
        review_dimension="security",
        runner=run_security_review,
        required=False,
    )
