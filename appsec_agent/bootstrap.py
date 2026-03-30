from __future__ import annotations

from functools import lru_cache

from appsec_agent.agents.registry import register_default_agents
from appsec_agent.core.config import AppConfig, load_config
from appsec_agent.core.plugins import AgentRegistry
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.ollama import OllamaProvider
from appsec_agent.services.analysis import AnalysisService
from appsec_agent.tools.registry import register_default_tools


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    return load_config()


@lru_cache(maxsize=1)
def get_repository() -> SQLiteFindingsRepository:
    config = get_app_config()
    repository = SQLiteFindingsRepository(config.db_path)
    repository.initialize()
    return repository


@lru_cache(maxsize=1)
def get_plugin_registry() -> AgentRegistry:
    registry = AgentRegistry()
    register_default_agents(registry)
    register_default_tools(registry)
    return registry


@lru_cache(maxsize=1)
def get_agent_registry() -> AgentRegistry:
    return get_plugin_registry()


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    config = get_app_config()
    repository = get_repository()
    provider = OllamaProvider(config)
    registry = get_plugin_registry()
    return AnalysisService(config=config, provider=provider, repository=repository, registry=registry)
