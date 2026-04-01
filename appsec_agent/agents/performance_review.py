from __future__ import annotations

from appsec_agent.agents.review_common import run_dimension_review
from appsec_agent.core.models import DimensionAnalysisResult, PlanningResult
from appsec_agent.core.plugins import AgentSpec, ExecutionContext


def should_run_performance_review(context: ExecutionContext) -> bool:
    return context.request.mode in {"performance", "full"}


def run_performance_review(context: ExecutionContext) -> None:
    planning_result = context.get_artifact("planning")
    if planning_result is None:
        raise ValueError("performance_review requires planning output.")
    result = run_dimension_review(
        provider=context.provider,
        model=context.metadata.get("active_model", context.config.model_performance_review),
        code=context.request.code,
        planning_result=planning_result,
        dimension="performance",
    )
    context.set_artifact("performance_review", result)


def get_agent_spec() -> AgentSpec:
    return AgentSpec(
        name="performance_review",
        stage="performance_review",
        order=20,
        description="Find performance issues in the snippet.",
        input_type=PlanningResult,
        output_type=DimensionAnalysisResult,
        model_config_key="model_performance_review",
        artifact_key="performance_review",
        should_run=should_run_performance_review,
        parallel_group="dimension_reviews",
        review_dimension="performance",
        runner=run_performance_review,
        required=False,
    )
