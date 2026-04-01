from __future__ import annotations

from collections.abc import Iterable

from appsec_agent.agents.aggregation import get_agent_spec as get_aggregation_agent_spec
from appsec_agent.agents.performance_review import get_agent_spec as get_performance_review_spec
from appsec_agent.agents.planning import get_agent_spec as get_planning_agent_spec
from appsec_agent.agents.quality_review import get_agent_spec as get_quality_review_spec
from appsec_agent.agents.security_review import get_agent_spec as get_security_review_spec
from appsec_agent.core.plugins import AgentRegistry, AgentSpec


DEFAULT_AGENT_SPEC_FACTORIES = (
    get_planning_agent_spec,
    get_security_review_spec,
    get_quality_review_spec,
    get_performance_review_spec,
    get_aggregation_agent_spec,
)


def iter_default_agent_specs() -> Iterable[AgentSpec]:
    for factory in DEFAULT_AGENT_SPEC_FACTORIES:
        yield factory()


def register_default_agents(registry: AgentRegistry) -> AgentRegistry:
    for spec in iter_default_agent_specs():
        registry.register_agent(spec)
    return registry
