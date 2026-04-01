from __future__ import annotations

from appsec_agent.agents.review_common import run_dimension_review
from appsec_agent.core.models import DimensionAnalysisResult, PlanningResult
from appsec_agent.core.plugins import AgentSpec, ExecutionContext


def should_run_quality_review(context: ExecutionContext) -> bool:
    return context.request.mode in {"quality", "full"}


def run_quality_review(context: ExecutionContext) -> None:
    planning_result = context.get_artifact("planning")
    if planning_result is None:
        raise ValueError("quality_review requires planning output.")
    result = run_dimension_review(
        provider=context.provider,
        model=context.metadata.get("active_model", context.config.model_quality_review),
        code=context.request.code,
        planning_result=planning_result,
        dimension="quality",
    )
    context.set_artifact("quality_review", result)


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="quality_review",
        stage="quality_review",
        order=20,
        description="Find code-quality issues in the snippet.",
        input_type=PlanningResult,
        output_type=DimensionAnalysisResult,
        model_config_key="model_quality_review",
        artifact_key="quality_review",
        should_run=should_run_quality_review,
        parallel_group="dimension_reviews",
        review_dimension="quality",
        runner=run_quality_review,
        required=False,
    )
