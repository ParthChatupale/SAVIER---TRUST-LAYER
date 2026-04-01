from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

from ollama import Client

from appsec_agent.core.config import AppConfig
from appsec_agent.providers.base import ModelOutputError, ModelProvider, ProviderUnavailableError


class OllamaProvider(ModelProvider):
    def __init__(self, config: AppConfig, client: Client | None = None):
        self._client = client or Client(
            host=config.ollama_host,
            timeout=config.ollama_timeout_seconds,
        )
        self._max_retries = max(0, config.ollama_max_retries)

    def generate_json(self, *, model: str, prompt: str, stage: str) -> dict[str, Any]:
        last_error: Exception | None = None
        attempts = self._max_retries + 1
        response = None

        for attempt in range(1, attempts + 1):
            try:
                response = self._client.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    format="json",
                )
                break
            except Exception as exc:  # pragma: no cover - exercised via provider tests
                last_error = exc
                if attempt >= attempts or not _is_retryable_error(exc):
                    raise ProviderUnavailableError(
                        f"{stage} stage could not reach Ollama: {exc}"
                    ) from exc

        if response is None:
            raise ProviderUnavailableError(
                f"{stage} stage could not reach Ollama after {attempts} attempts: {last_error}"
            )

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


def _is_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "timed out" in message or "timeout" in message
