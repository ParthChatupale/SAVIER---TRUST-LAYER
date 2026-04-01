"""Provider abstractions for model access."""

from appsec_agent.providers.nvidia import NvidiaProvider
from appsec_agent.providers.ollama import OllamaProvider

__all__ = ["NvidiaProvider", "OllamaProvider"]
