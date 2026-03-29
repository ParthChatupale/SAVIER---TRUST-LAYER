from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

from ollama import Client

from appsec_agent.core.config import AppConfig
from appsec_agent.providers.base import ModelOutputError, ModelProvider, ProviderUnavailableError


class OllamaProvider(ModelProvider):
    def __init__(self, config: AppConfig):
        self._client = Client(
            host=config.ollama_host,
            timeout=config.ollama_timeout_seconds,
        )

    def generate_json(self, *, model: str, prompt: str, stage: str) -> dict[str, Any]:
        try:
            response = self._client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
        except Exception as exc:  # pragma: no cover - exercised via service tests
            raise ProviderUnavailableError(
                f"{stage} stage could not reach Ollama: {exc}"
            ) from exc

        content = response.message.content.strip()
        try:
            payload = json.loads(content)
        except JSONDecodeError as exc:
            raise ModelOutputError(
                f"{stage} stage returned invalid JSON: {content[:200]}"
            ) from exc

        if not isinstance(payload, dict):
            raise ModelOutputError(f"{stage} stage returned non-object JSON.")

        return payload
