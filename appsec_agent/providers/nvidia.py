from __future__ import annotations

import json
from json import JSONDecodeError
from threading import Lock
from typing import Any

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from appsec_agent.core.config import AppConfig
from appsec_agent.providers.base import ModelOutputError, ModelProvider, ProviderUnavailableError


class NvidiaProvider(ModelProvider):
    def __init__(self, config: AppConfig):
        if not config.nvidia_api_key:
            raise ProviderUnavailableError(
                "nvidia provider requires NVIDIA_API_KEY, GEM29b_api_key, or openai_api_key."
            )
        self._api_key = config.nvidia_api_key
        self._clients: dict[str, ChatNVIDIA] = {}
        self._client_lock = Lock()

    def generate_json(self, *, model: str, prompt: str, stage: str) -> dict[str, Any]:
        client = self._client_for(model)
        try:
            message = client.invoke([{"role": "user", "content": prompt}])
        except Exception as exc:
            raise ProviderUnavailableError(
                f"{stage} stage could not reach NVIDIA endpoint: {exc}"
            ) from exc

        content = _strip_json_fences(str(message.content).strip())
        try:
            payload = json.loads(content)
        except JSONDecodeError as exc:
            raise ModelOutputError(
                f"{stage} stage returned invalid JSON: {content[:200]}"
            ) from exc

        if not isinstance(payload, dict):
            raise ModelOutputError(f"{stage} stage returned non-object JSON.")
        return payload

    def _client_for(self, model: str) -> ChatNVIDIA:
        client = self._clients.get(model)
        if client is None:
            with self._client_lock:
                client = self._clients.get(model)
                if client is None:
                    client = ChatNVIDIA(
                        model=model,
                        api_key=self._api_key,
                        temperature=0.2,
                        top_p=0.7,
                        max_completion_tokens=2048,
                    )
                    self._clients[model] = client
        return client


def _strip_json_fences(content: str) -> str:
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return content
