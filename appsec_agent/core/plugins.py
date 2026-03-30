from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import AnalysisMode

if TYPE_CHECKING:
    from appsec_agent.services.analysis import AnalysisService


AllowedPluginType = str
AgentRunner = Callable[["ExecutionContext"], None]
ShouldRunPredicate = Callable[["ExecutionContext"], bool]
ToolHandler = Callable[["ToolExecutionContext", dict[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class AgentSpec:
    name: str
    stage: str
    order: int
    description: str
    input_type: type[Any]
    output_type: type[Any]
    model_config_key: str
    runner: AgentRunner
    artifact_key: str | None = None
    should_run: ShouldRunPredicate | None = None
    required: bool = True
    enabled: bool = True
    plugin_type: AllowedPluginType = "agent"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Agent spec name must be non-empty.")
        if not self.stage.strip():
            raise ValueError(f"Agent '{self.name}' must declare a non-empty stage.")
        if self.order < 0:
            raise ValueError(f"Agent '{self.name}' must declare a non-negative order.")
        if self.plugin_type != "agent":
            raise ValueError(f"Agent '{self.name}' must have plugin_type='agent'.")


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    implementation_ref: str = ""
    enabled: bool = True
    plugin_type: AllowedPluginType = "tool"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Tool spec name must be non-empty.")
        if not self.description.strip():
            raise ValueError(f"Tool '{self.name}' must declare a description.")
        if not isinstance(self.input_schema, dict) or not self.input_schema:
            raise ValueError(f"Tool '{self.name}' must declare a non-empty input schema.")
        if not self.implementation_ref:
            object.__setattr__(self, "implementation_ref", self.name)
        if self.plugin_type != "tool":
            raise ValueError(f"Tool '{self.name}' must have plugin_type='tool'.")


@dataclass(slots=True)
class AgentRegistry:
    agents: dict[str, AgentSpec] = field(default_factory=dict)
    tools: dict[str, ToolSpec] = field(default_factory=dict)

    def register_agent(self, spec: AgentSpec) -> None:
        if spec.name in self.agents:
            raise ValueError(f"Duplicate agent registration: {spec.name}")
        self.agents[spec.name] = spec

    def register_tool(self, spec: ToolSpec) -> None:
        if spec.name in self.tools:
            raise ValueError(f"Duplicate tool registration: {spec.name}")
        self.tools[spec.name] = spec

    def get_enabled_agents(self, config: AppConfig) -> list[AgentSpec]:
        if not config.enabled_agents:
            return sorted(
                [spec for spec in self.agents.values() if spec.enabled],
                key=lambda spec: (spec.order, spec.name),
            )

        resolved: list[AgentSpec] = []
        for name in config.enabled_agents:
            spec = self.agents.get(name)
            if spec is None:
                raise ValueError(f"Unknown agent configured in pipeline: {name}")
            if spec.enabled:
                resolved.append(spec)
        return resolved

    def get_enabled_tools(self) -> list[ToolSpec]:
        return sorted(
            [spec for spec in self.tools.values() if spec.enabled],
            key=lambda spec: spec.name,
        )


@dataclass(slots=True)
class ExecutionContext:
    config: AppConfig
    request: "AnalysisRequest"
    response: "AnalysisResponse"
    provider: "ModelProvider"
    repository: "SQLiteFindingsRepository"
    history: list["DeveloperFinding"]
    artifacts: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mode(self) -> AnalysisMode:
        return self.request.mode

    def history_payload(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self.history]

    def model_for(self, spec: AgentSpec) -> str:
        return getattr(self.config, spec.model_config_key)

    def set_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value

    def get_artifact(self, key: str, default: Any = None) -> Any:
        return self.artifacts.get(key, default)

    @property
    def planning(self) -> "PlanningResult | None":
        return self.get_artifact("planning")

    @planning.setter
    def planning(self, value: "PlanningResult | None") -> None:
        if value is None:
            self.artifacts.pop("planning", None)
            return
        self.set_artifact("planning", value)

    @property
    def finding(self) -> "FindingCandidate | None":
        return self.get_artifact("coding")

    @finding.setter
    def finding(self, value: "FindingCandidate | None") -> None:
        if value is None:
            self.artifacts.pop("coding", None)
            return
        self.set_artifact("coding", value)

    @property
    def security(self) -> "SecurityAssessment | None":
        return self.get_artifact("security")

    @security.setter
    def security(self, value: "SecurityAssessment | None") -> None:
        if value is None:
            self.artifacts.pop("security", None)
            return
        self.set_artifact("security", value)


@dataclass(slots=True)
class ToolExecutionContext:
    config: AppConfig
    analysis_service: "AnalysisService"
    repository: "SQLiteFindingsRepository"


from appsec_agent.core.models import (  # noqa: E402
    AnalysisRequest,
    AnalysisResponse,
    DeveloperFinding,
    FindingCandidate,
    PlanningResult,
    SecurityAssessment,
)
from appsec_agent.memory.store import SQLiteFindingsRepository  # noqa: E402
from appsec_agent.providers.base import ModelProvider  # noqa: E402
