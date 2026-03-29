from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from appsec_agent.agents.registry import register_default_agents
from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import AnalysisRequest, FindingCandidate
from appsec_agent.core.plugins import AgentRegistry, AgentSpec
from appsec_agent.core.taxonomy import normalize_vulnerability_type
from appsec_agent.http_server import create_app
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.base import ModelOutputError, ProviderUnavailableError
from appsec_agent.server import call_tool
from appsec_agent.services.analysis import AnalysisService


class FakeProvider:
    def __init__(self, responses: dict[str, dict] | None = None, errors: dict[str, Exception] | None = None):
        self.responses = responses or {}
        self.errors = errors or {}

    def generate_json(self, *, model: str, prompt: str, stage: str) -> dict:
        if stage in self.errors:
            raise self.errors[stage]
        return self.responses[stage]


def build_service(
    tmp_path: Path,
    responses: dict[str, dict] | None = None,
    errors: dict[str, Exception] | None = None,
) -> tuple[AnalysisService, SQLiteFindingsRepository]:
    config = AppConfig(db_path=tmp_path / "memory.db")
    repository = SQLiteFindingsRepository(config.db_path)
    repository.initialize()
    provider = FakeProvider(responses=responses, errors=errors)
    registry = register_default_agents(AgentRegistry())
    return AnalysisService(config=config, provider=provider, repository=repository, registry=registry), repository


class RepositoryTests(unittest.TestCase):
    def test_repository_save_get_clear_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = SQLiteFindingsRepository(Path(tmpdir) / "memory.db")
            repo.save_finding("alice", "SQL Injection", "query = ...", "Dangerous query building.")

            history = repo.get_developer_history("alice")
            self.assertEqual(1, len(history))
            self.assertEqual("SQL Injection", history[0].vuln_type)

            repo.clear_developer_history("alice")
            self.assertEqual([], repo.get_developer_history("alice"))


class ModelValidationTests(unittest.TestCase):
    def test_finding_candidate_requires_type_when_vuln_found(self):
        with self.assertRaises(ValueError):
            FindingCandidate.from_payload({"vuln_found": True, "confidence": 0.9})

    def test_unknown_alias_is_normalized(self):
        self.assertEqual(
            "SQL Injection",
            normalize_vulnerability_type("SQL injection vulnerability"),
        )


class RegistryTests(unittest.TestCase):
    def test_registry_rejects_duplicate_agents(self):
        registry = AgentRegistry()
        spec = AgentSpec(
            name="planning",
            stage="planning",
            order=10,
            description="test",
            input_type=str,
            output_type=dict,
            model_config_key="model_planning",
            runner=lambda context: None,
        )
        registry.register_agent(spec)
        with self.assertRaises(ValueError):
            registry.register_agent(spec)

    def test_registry_rejects_invalid_stage_or_order(self):
        with self.assertRaises(ValueError):
            AgentSpec(
                name="bad-stage",
                stage="",
                order=10,
                description="test",
                input_type=str,
                output_type=dict,
                model_config_key="model_planning",
                runner=lambda context: None,
            )
        with self.assertRaises(ValueError):
            AgentSpec(
                name="bad-order",
                stage="planning",
                order=-1,
                description="test",
                input_type=str,
                output_type=dict,
                model_config_key="model_planning",
                runner=lambda context: None,
            )

    def test_registry_skips_disabled_agents(self):
        registry = AgentRegistry()
        registry.register_agent(
            AgentSpec(
                name="planning",
                stage="planning",
                order=10,
                description="test",
                input_type=str,
                output_type=dict,
                model_config_key="model_planning",
                runner=lambda context: None,
            )
        )
        registry.register_agent(
            AgentSpec(
                name="security",
                stage="security",
                order=30,
                description="test",
                input_type=dict,
                output_type=dict,
                model_config_key="model_security",
                runner=lambda context: None,
                enabled=False,
            )
        )
        config = AppConfig(db_path=Path("memory.db"), enabled_agents=("planning", "security"))
        enabled = registry.get_enabled_agents(config)
        self.assertEqual(["planning"], [spec.name for spec in enabled])


class AnalysisServiceTests(unittest.TestCase):
    def test_provider_unavailable_marks_analysis_failed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, _ = build_service(
                Path(tmpdir),
                errors={"planning": ProviderUnavailableError("planning stage could not reach Ollama")},
            )
            result = service.analyze(AnalysisRequest(code="print('hi')", developer_id="alice"))
            self.assertEqual("failed", result.status)
            self.assertFalse(result.vuln_found)
            self.assertTrue(result.errors)

    def test_security_failure_returns_partial_with_fallback_severity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, _ = build_service(
                Path(tmpdir),
                responses={
                    "planning": {
                        "intent": "Query user data.",
                        "entry_points": ["user_id"],
                        "sensitive_operations": ["db.execute"],
                        "security_focus": ["SQL Injection"],
                    },
                    "coding": {
                        "vuln_found": True,
                        "vuln_type": "SQL injection vulnerability",
                        "vulnerable_line": 'query = "SELECT * FROM users WHERE id=" + user_id',
                        "pattern": "User input is concatenated into SQL.",
                        "attack_scenario": "Attacker can inject SQL.",
                        "suggested_fix": "Use parameterized queries.",
                        "confidence": 0.92,
                    },
                },
                errors={"security": ModelOutputError("security stage returned invalid JSON")},
            )
            result = service.analyze(AnalysisRequest(code="query = ...", developer_id="alice"))
            self.assertEqual("partial", result.status)
            self.assertTrue(result.vuln_found)
            self.assertEqual("SQL Injection", result.vuln_type)
            self.assertEqual("CRITICAL", result.severity)

    def test_successful_analysis_is_saved_to_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, repo = build_service(
                Path(tmpdir),
                responses={
                    "planning": {
                        "intent": "Query user data.",
                        "entry_points": ["user_id"],
                        "sensitive_operations": ["db.execute"],
                        "security_focus": ["SQL Injection"],
                    },
                    "coding": {
                        "vuln_found": True,
                        "vuln_type": "SQL Injection",
                        "vulnerable_line": 'query = "SELECT * FROM users WHERE id=" + user_id',
                        "pattern": "User input is concatenated into SQL.",
                        "attack_scenario": "Attacker can inject SQL.",
                        "suggested_fix": "Use parameterized queries.",
                        "confidence": 0.92,
                    },
                    "security": {
                        "severity": "CRITICAL",
                        "owasp_category": "A03:2021 - Injection",
                        "cve_reference": "GENERIC",
                        "data_flow": "user input flows into db.execute",
                        "developer_note": "Use bound parameters.",
                        "full_explanation": "String concatenation turns data into executable SQL.",
                    },
                },
            )
            result = service.analyze(AnalysisRequest(code="query = ...", developer_id="alice"))
            self.assertEqual("success", result.status)
            self.assertEqual(1, len(repo.get_developer_history("alice")))

    def test_custom_registered_agent_runs_without_service_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AppConfig(
                db_path=Path(tmpdir) / "memory.db",
                enabled_agents=("planning", "coding", "security", "annotate"),
            )
            repository = SQLiteFindingsRepository(config.db_path)
            repository.initialize()
            provider = FakeProvider(
                responses={
                    "planning": {
                        "intent": "Query user data.",
                        "entry_points": ["user_id"],
                        "sensitive_operations": ["db.execute"],
                        "security_focus": ["SQL Injection"],
                    },
                    "coding": {
                        "vuln_found": True,
                        "vuln_type": "SQL Injection",
                        "vulnerable_line": 'query = "SELECT * FROM users WHERE id=" + user_id',
                        "pattern": "User input is concatenated into SQL.",
                        "attack_scenario": "Attacker can inject SQL.",
                        "suggested_fix": "Use parameterized queries.",
                        "confidence": 0.9,
                    },
                    "security": {
                        "severity": "CRITICAL",
                        "owasp_category": "A03",
                        "cve_reference": "GENERIC",
                        "data_flow": "user input reaches db.execute",
                        "developer_note": "Use bound parameters.",
                        "full_explanation": "Concatenated SQL is injectable.",
                    },
                }
            )
            registry = register_default_agents(AgentRegistry())
            registry.register_agent(
                AgentSpec(
                    name="annotate",
                    stage="postprocess",
                    order=40,
                    description="Add an internal annotation.",
                    input_type=dict,
                    output_type=dict,
                    model_config_key="model_security",
                    runner=lambda context: context.response.warnings.append("annotated"),
                    required=False,
                )
            )
            service = AnalysisService(
                config=config,
                provider=provider,
                repository=repository,
                registry=registry,
            )
            result = service.analyze(AnalysisRequest(code="query = ...", developer_id="alice"))
            self.assertEqual("success", result.status)
            self.assertIn("annotated", result.warnings)


class TransportTests(unittest.TestCase):
    def test_http_clear_route_uses_fixed_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, repo = build_service(
                Path(tmpdir),
                responses={
                    "planning": {
                        "intent": "Clean code.",
                        "entry_points": [],
                        "sensitive_operations": [],
                        "security_focus": [],
                    },
                    "coding": {
                        "vuln_found": False,
                        "vuln_type": "",
                        "vulnerable_line": "",
                        "pattern": "",
                        "attack_scenario": "",
                        "suggested_fix": "",
                        "confidence": 0.0,
                    },
                },
            )
            repo.save_finding("alice", "SQL Injection", "query", "explanation")
            app = create_app()
            app.config["TESTING"] = True
            client = app.test_client()
            # Replace cached singletons by monkeypatching the module globals.
            import appsec_agent.http_server as http_server

            http_server.get_analysis_service = lambda: service
            http_server.get_repository = lambda: repo

            response = client.post("/clear", json={"developer_id": "alice"})
            self.assertEqual(200, response.status_code)
            self.assertEqual({"developer_id": "alice", "status": "cleared"}, response.get_json())

    def test_mcp_analyze_code_accepts_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, repo = build_service(
                Path(tmpdir),
                responses={
                    "planning": {
                        "intent": "Loop over orders.",
                        "entry_points": ["user_ids"],
                        "sensitive_operations": ["db.execute"],
                        "security_focus": ["N+1 Query"],
                    },
                    "coding": {
                        "vuln_found": True,
                        "vuln_type": "N+1 Query",
                        "vulnerable_line": "for user_id in user_ids:",
                        "pattern": "A query runs inside the loop.",
                        "attack_scenario": "Performance degrades with more users.",
                        "suggested_fix": "Batch query by user_ids.",
                        "confidence": 0.88,
                    },
                    "security": {
                        "severity": "HIGH",
                        "owasp_category": "",
                        "cve_reference": "GENERIC",
                        "data_flow": "user_ids drive repeated db.execute calls",
                        "developer_note": "Batch the fetch.",
                        "full_explanation": "Per-user queries create N+1 database work.",
                    },
                },
            )
            import appsec_agent.server as mcp_server

            mcp_server.get_analysis_service = lambda: service
            mcp_server.get_repository = lambda: repo

            response = unittest.IsolatedAsyncioTestCase().run
            del response  # keep lint quiet for stdlib-only tests

            async def invoke():
                result = await call_tool(
                    "analyze_code",
                    {"code": "for user_id in user_ids: db.execute(...)", "developer_id": "alice", "mode": "performance"},
                )
                return json.loads(result[0].text)

            payload = __import__("asyncio").run(invoke())
            self.assertEqual("performance", payload["mode"])
            self.assertEqual("N+1 Query", payload["vuln_type"])


if __name__ == "__main__":
    unittest.main()
