from __future__ import annotations

from functools import lru_cache

from appsec_agent.core.config import AppConfig, load_config
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.ollama import OllamaProvider
from appsec_agent.services.analysis import AnalysisService


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
def get_analysis_service() -> AnalysisService:
    config = get_app_config()
    repository = get_repository()
    provider = OllamaProvider(config)
    return AnalysisService(config=config, provider=provider, repository=repository)
