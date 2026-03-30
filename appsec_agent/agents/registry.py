from __future__ import annotations

from collections.abc import Iterable

from appsec_agent.agents.coding import get_agent_spec as get_coding_agent_spec
from appsec_agent.agents.planning import get_agent_spec as get_planning_agent_spec
from appsec_agent.agents.security import get_agent_spec as get_security_agent_spec
from appsec_agent.core.plugins import AgentRegistry, AgentSpec


DEFAULT_AGENT_SPEC_FACTORIES = (
    get_planning_agent_spec,
    get_coding_agent_spec,
    get_security_agent_spec,
)


def iter_default_agent_specs() -> Iterable[AgentSpec]:
    for factory in DEFAULT_AGENT_SPEC_FACTORIES:
        yield factory()


def register_default_agents(registry: AgentRegistry) -> AgentRegistry:
    for spec in iter_default_agent_specs():
        registry.register_agent(spec)
    return registry
