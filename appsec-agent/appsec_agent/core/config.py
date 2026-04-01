from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_db_path() -> Path:
    return _default_repo_root() / "appsec_memory.db"


def _default_env_path() -> Path:
    return _default_repo_root() / ".env"


load_dotenv(_default_env_path())


@dataclass(frozen=True)
class AppConfig:
    db_path: Path = field(default_factory=_default_db_path)
    provider_name: str = "ollama"
    ollama_host: str | None = None
    ollama_timeout_seconds: float = 60.0
    ollama_max_retries: int = 1
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    model_planning: str = "llama3.2"
    model_coding: str = "llama3.1:8b"
    model_security: str = "llama3.1:8b"
    model_security_review: str = "llama3.1:8b"
    model_quality_review: str = "llama3.1:8b"
    model_performance_review: str = "llama3.1:8b"
    model_aggregation: str = "llama3.1:8b"
    model_fallback_planning: tuple[str, ...] = ()
    model_fallback_coding: tuple[str, ...] = ()
    model_fallback_security: tuple[str, ...] = ()
    model_fallback_security_review: tuple[str, ...] = ()
    model_fallback_quality_review: tuple[str, ...] = ()
    model_fallback_performance_review: tuple[str, ...] = ()
    model_fallback_aggregation: tuple[str, ...] = ()
    enabled_agents: tuple[str, ...] = (
        "planning",
        "security_review",
        "quality_review",
        "performance_review",
        "aggregation",
    )


def load_config() -> AppConfig:
    db_path = Path(os.getenv("APPSEC_AGENT_DB_PATH", str(_default_db_path()))).expanduser()
    provider_name = (os.getenv("APPSEC_AGENT_PROVIDER", "ollama") or "ollama").strip().lower()
    ollama_host = os.getenv("OLLAMA_HOST") or None
    timeout = float(os.getenv("APPSEC_AGENT_OLLAMA_TIMEOUT", "60"))
    max_retries = int(os.getenv("APPSEC_AGENT_OLLAMA_MAX_RETRIES", "1"))
    nvidia_api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("GEM29b_api_key") or os.getenv("openai_api_key") or None
    nvidia_base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    pipeline = _normalize_pipeline(
        tuple(
        item.strip()
        for item in os.getenv(
            "APPSEC_AGENT_PIPELINE",
            "planning,security_review,quality_review,performance_review,aggregation",
        ).split(",")
        if item.strip()
        )
    )
    default_models = _default_models_for_provider(provider_name)
    model_planning = os.getenv("APPSEC_AGENT_MODEL_PLANNING", default_models["planning"])
    model_coding = os.getenv("APPSEC_AGENT_MODEL_CODING", default_models["coding"])
    model_security = os.getenv("APPSEC_AGENT_MODEL_SECURITY", default_models["security"])
    model_security_review = os.getenv(
        "APPSEC_AGENT_MODEL_SECURITY_REVIEW",
        os.getenv("APPSEC_AGENT_MODEL_CODING", default_models["security_review"]),
    )
    model_quality_review = os.getenv(
        "APPSEC_AGENT_MODEL_QUALITY_REVIEW",
        os.getenv("APPSEC_AGENT_MODEL_CODING", default_models["quality_review"]),
    )
    model_performance_review = os.getenv(
        "APPSEC_AGENT_MODEL_PERFORMANCE_REVIEW",
        os.getenv("APPSEC_AGENT_MODEL_CODING", default_models["performance_review"]),
    )
    model_aggregation = os.getenv(
        "APPSEC_AGENT_MODEL_AGGREGATION",
        os.getenv("APPSEC_AGENT_MODEL_SECURITY", default_models["aggregation"]),
    )
    fallback_planning = _parse_model_list(
        os.getenv("APPSEC_AGENT_MODEL_FALLBACK_PLANNING", ",".join(default_models["fallback_planning"]))
    )
    fallback_coding = _parse_model_list(
        os.getenv("APPSEC_AGENT_MODEL_FALLBACK_CODING", ",".join(default_models["fallback_coding"]))
    )
    fallback_security = _parse_model_list(
        os.getenv("APPSEC_AGENT_MODEL_FALLBACK_SECURITY", ",".join(default_models["fallback_security"]))
    )
    fallback_security_review = _parse_model_list(
        os.getenv(
            "APPSEC_AGENT_MODEL_FALLBACK_SECURITY_REVIEW",
            os.getenv("APPSEC_AGENT_MODEL_FALLBACK_CODING", ",".join(default_models["fallback_security_review"])),
        )
    )
    fallback_quality_review = _parse_model_list(
        os.getenv(
            "APPSEC_AGENT_MODEL_FALLBACK_QUALITY_REVIEW",
            os.getenv("APPSEC_AGENT_MODEL_FALLBACK_CODING", ",".join(default_models["fallback_quality_review"])),
        )
    )
    fallback_performance_review = _parse_model_list(
        os.getenv(
            "APPSEC_AGENT_MODEL_FALLBACK_PERFORMANCE_REVIEW",
            os.getenv("APPSEC_AGENT_MODEL_FALLBACK_CODING", ",".join(default_models["fallback_performance_review"])),
        )
    )
    fallback_aggregation = _parse_model_list(
        os.getenv(
            "APPSEC_AGENT_MODEL_FALLBACK_AGGREGATION",
            os.getenv("APPSEC_AGENT_MODEL_FALLBACK_SECURITY", ",".join(default_models["fallback_aggregation"])),
        )
    )

    return AppConfig(
        db_path=db_path,
        provider_name=provider_name,
        ollama_host=ollama_host,
        ollama_timeout_seconds=timeout,
        ollama_max_retries=max_retries,
        nvidia_api_key=nvidia_api_key,
        nvidia_base_url=nvidia_base_url,
        model_planning=model_planning,
        model_coding=model_coding,
        model_security=model_security,
        model_security_review=model_security_review,
        model_quality_review=model_quality_review,
        model_performance_review=model_performance_review,
        model_aggregation=model_aggregation,
        model_fallback_planning=fallback_planning,
        model_fallback_coding=fallback_coding,
        model_fallback_security=fallback_security,
        model_fallback_security_review=fallback_security_review,
        model_fallback_quality_review=fallback_quality_review,
        model_fallback_performance_review=fallback_performance_review,
        model_fallback_aggregation=fallback_aggregation,
        enabled_agents=pipeline,
    )


def _default_models_for_provider(provider_name: str) -> dict[str, str]:
    if provider_name == "nvidia":
        return {
            "planning": "google/gemma-2-9b-it",
            "coding": "google/gemma-2-9b-it",
            "security": "openai/gpt-oss-120b",
            "security_review": "google/gemma-2-9b-it",
            "quality_review": "google/gemma-2-9b-it",
            "performance_review": "google/gemma-2-9b-it",
            "aggregation": "openai/gpt-oss-120b",
            "fallback_planning": ("openai/gpt-oss-120b",),
            "fallback_coding": ("openai/gpt-oss-120b",),
            "fallback_security": ("google/gemma-2-9b-it",),
            "fallback_security_review": ("openai/gpt-oss-120b",),
            "fallback_quality_review": ("openai/gpt-oss-120b",),
            "fallback_performance_review": ("openai/gpt-oss-120b",),
            "fallback_aggregation": ("google/gemma-2-9b-it",),
        }
    return {
        "planning": "llama3.2",
        "coding": "llama3.1:8b",
        "security": "llama3.1:8b",
        "security_review": "llama3.1:8b",
        "quality_review": "llama3.1:8b",
        "performance_review": "llama3.1:8b",
        "aggregation": "llama3.1:8b",
        "fallback_planning": (),
        "fallback_coding": (),
        "fallback_security": (),
        "fallback_security_review": (),
        "fallback_quality_review": (),
        "fallback_performance_review": (),
        "fallback_aggregation": (),
    }


def _parse_model_list(raw_value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


def _normalize_pipeline(items: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for item in items:
        if item == "coding":
            normalized.extend(["security_review", "quality_review", "performance_review"])
            continue
        if item == "security":
            normalized.append("aggregation")
            continue
        normalized.append(item)
    seen: set[str] = set()
    result: list[str] = []
    for item in normalized:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)
