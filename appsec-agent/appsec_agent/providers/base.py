from __future__ import annotations

from typing import Any, Protocol


class ProviderError(RuntimeError):
    """Base error for model provider failures."""


class ProviderUnavailableError(ProviderError):
    """Raised when the underlying model provider cannot be reached."""


class ModelOutputError(ProviderError):
    """Raised when a model response cannot be parsed or validated."""


class ModelProvider(Protocol):
    def generate_json(self, *, model: str, prompt: str, stage: str) -> dict[str, Any]:
        """Return a validated JSON object for the requested model/stage."""
