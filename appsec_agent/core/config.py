from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_db_path() -> Path:
    return _default_repo_root() / "appsec_memory.db"


@dataclass(frozen=True)
class AppConfig:
    db_path: Path = field(default_factory=_default_db_path)
    ollama_host: str | None = None
    ollama_timeout_seconds: float = 30.0
    model_planning: str = "llama3.2"
    model_coding: str = "llama3.1:8b"
    model_security: str = "llama3.1:8b"


def load_config() -> AppConfig:
    db_path = Path(os.getenv("APPSEC_AGENT_DB_PATH", str(_default_db_path()))).expanduser()
    ollama_host = os.getenv("OLLAMA_HOST") or None
    timeout = float(os.getenv("APPSEC_AGENT_OLLAMA_TIMEOUT", "30"))

    return AppConfig(
        db_path=db_path,
        ollama_host=ollama_host,
        ollama_timeout_seconds=timeout,
    )
