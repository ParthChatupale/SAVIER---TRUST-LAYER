from __future__ import annotations

import unittest

from appsec_agent.core.config import AppConfig
from appsec_agent.providers.base import ModelOutputError, ProviderUnavailableError
from appsec_agent.providers.ollama import OllamaProvider


class _Message:
    def __init__(self, content: str):
        self.content = content


class _Response:
    def __init__(self, content: str):
        self.message = _Message(content)


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def chat(self, **kwargs):
        self.calls += 1
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class OllamaProviderTests(unittest.TestCase):
    def test_retries_once_on_timeout_and_then_succeeds(self):
        client = _FakeClient(
            [
                RuntimeError("timed out"),
                _Response('{"intent": "Query user data", "entry_points": [], "sensitive_operations": [], "security_focus": []}'),
            ]
        )
        provider = OllamaProvider(AppConfig(ollama_max_retries=1), client=client)

        payload = provider.generate_json(model="llama3.2", prompt="test", stage="planning")

        self.assertEqual(2, client.calls)
        self.assertEqual("Query user data", payload["intent"])

    def test_raises_after_retry_budget_is_exhausted(self):
        client = _FakeClient([RuntimeError("timed out"), RuntimeError("timed out")])
        provider = OllamaProvider(AppConfig(ollama_max_retries=1), client=client)

        with self.assertRaises(ProviderUnavailableError):
            provider.generate_json(model="llama3.2", prompt="test", stage="planning")

        self.assertEqual(2, client.calls)

    def test_invalid_json_still_fails_without_retry_loop(self):
        client = _FakeClient([_Response("not-json")])
        provider = OllamaProvider(AppConfig(ollama_max_retries=1), client=client)

        with self.assertRaises(ModelOutputError):
            provider.generate_json(model="llama3.2", prompt="test", stage="planning")

        self.assertEqual(1, client.calls)


if __name__ == "__main__":
    unittest.main()
