from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from appsec_agent.agents.registry import register_default_agents
from appsec_agent.core.config import AppConfig
from appsec_agent.core.models import (
    AnalysisEvent,
    AnalysisRequest,
    DimensionScores,
    FileState,
    FindingCandidate,
    FindingRecord,
    PlanningResult,
    ScoreDelta,
    SecurityAssessment,
    diff_findings,
    merge_dimension_scores,
)
from appsec_agent.core.plugins import AgentRegistry, AgentSpec, ToolExecutionContext, ToolSpec
from appsec_agent.core.taxonomy import (
    normalize_owasp_category,
    normalize_severity,
    normalize_suggested_fix,
    normalize_vulnerability_type,
)
from appsec_agent.http_server import create_app
from appsec_agent.memory.store import SQLiteFindingsRepository
from appsec_agent.providers.base import ModelOutputError, ProviderUnavailableError
from appsec_agent.server import call_tool, list_tools
from appsec_agent.services.analysis import AnalysisService
from appsec_agent.tools.registry import register_default_tools


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

    def test_repository_tracks_file_state_and_analysis_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = SQLiteFindingsRepository(Path(tmpdir) / "memory.db")
            repo.initialize()
            event = repo.insert_analysis_event(
                AnalysisEvent(
                    event_id="",
                    developer_id="alice",
                    file_uri="file:///demo.py",
                    source="ide_extension",
                    mode="security",
                    content_hash="hash-1",
                    status="success",
                    scores=DimensionScores(security=60, quality=100, performance=100, overall=87),
                    findings=[
                        FindingRecord(
                            key="security:SQL Injection:query",
                            dimension="security",
                            issue_type="SQL Injection",
                            severity="CRITICAL",
                            line='query = "SELECT *" + user_id',
                            explanation="Unsafe SQL concatenation.",
                        )
                    ],
                    diff=ScoreDelta(
                        score_delta=-13,
                        new_findings=["security:SQL Injection:query"],
                    ),
                    summary={"vuln_type": "SQL Injection"},
                )
            )
            repo.upsert_file_state(
                FileState(
                    developer_id="alice",
                    file_uri="file:///demo.py",
                    content_hash="hash-1",
                    last_event_id=event.event_id,
                    source="ide_extension",
                    mode="security",
                    status="success",
                    scores=event.scores,
                    findings=event.findings,
                )
            )

            state = repo.get_file_state("alice", "file:///demo.py")
            self.assertIsNotNone(state)
            self.assertEqual("hash-1", state.content_hash)
            self.assertEqual(event.event_id, state.last_event_id)

            events = repo.list_analysis_events("alice", file_uri="file:///demo.py")
            self.assertEqual(1, len(events))
            self.assertEqual("ide_extension", events[0].source)

            summary = repo.get_dashboard_summary("alice")
            self.assertEqual(1, summary.total_files)
            self.assertEqual(1, summary.total_events)
            self.assertEqual(1, summary.open_findings)

            repo.clear_analysis_history("alice")
            self.assertIsNone(repo.get_file_state("alice", "file:///demo.py"))
            self.assertEqual([], repo.list_analysis_events("alice"))


class ModelValidationTests(unittest.TestCase):
    def test_finding_candidate_requires_type_when_vuln_found(self):
        with self.assertRaises(ValueError):
            FindingCandidate.from_payload({"vuln_found": True, "confidence": 0.9})

    def test_unknown_alias_is_normalized(self):
        self.assertEqual(
            "SQL Injection",
            normalize_vulnerability_type("SQL injection vulnerability"),
        )

    def test_parenthetical_issue_suffix_is_normalized(self):
        self.assertEqual(
            "SQL Injection",
            normalize_vulnerability_type("SQL injection (potential)"),
        )

    def test_severity_is_normalized_to_canonical_uppercase(self):
        self.assertEqual("HIGH", normalize_severity("High", vuln_type="Hardcoded Secret"))

    def test_owasp_category_prefers_canonical_mapping_for_issue_type(self):
        self.assertEqual(
            "A03:2021 - Injection",
            normalize_owasp_category("A05:2017 - Injection", vuln_type="SQL Injection"),
        )

    def test_planning_result_rejects_generic_mode_as_intent(self):
        planning = PlanningResult.from_payload(
            {
                "intent": "security",
                "entry_points": [],
                "sensitive_operations": [],
                "security_focus": [],
            },
            "security",
            code="def get_user(user_id):\n    return db.execute(user_id)\n",
        )
        self.assertNotEqual("security", planning.intent)
        self.assertIn("get_user", planning.intent)

    def test_planning_result_derives_entry_points_and_operations_from_code(self):
        planning = PlanningResult.from_payload(
            {
                "intent": "security review",
                "entry_points": ["function definitions"],
                "sensitive_operations": ["SQL injection (potentially vulnerable)"],
                "security_focus": ["SQL Injection"],
            },
            "security",
            code=(
                "def get_user(user_id, tenant_id):\n"
                "    query = 'SELECT * FROM users WHERE id=' + user_id\n"
                "    return db.execute(query)\n"
            ),
        )
        self.assertEqual(["user_id", "tenant_id"], planning.entry_points)
        self.assertEqual(["db.execute(...)"], planning.sensitive_operations)

    def test_security_assessment_normalizes_severity_and_owasp(self):
        assessment = SecurityAssessment.from_payload(
            {
                "severity": "High",
                "owasp_category": "A05:2017 - Injection",
                "cve_reference": "GENERIC",
                "data_flow": "user input reaches SQL",
                "developer_note": "Use parameters",
                "full_explanation": "SQL is injectable",
            },
            vuln_type="SQL Injection",
        )
        self.assertEqual("CRITICAL", assessment.severity)
        self.assertEqual("A03:2021 - Injection", assessment.owasp_category)

    def test_suggested_fix_is_canonicalized_for_known_issue_type(self):
        fix = normalize_suggested_fix(
            "Use parameterized queries or prepared statements to separate user input from SQL code.",
            vuln_type="SQL Injection",
            vulnerable_line='query = "SELECT * FROM users WHERE id=" + user_id',
        )
        self.assertIn("parameterized query", fix.lower())
        self.assertIn("db.execute(query, (user_id,))", fix)

    def test_finding_candidate_rewrites_weak_sql_fix(self):
        finding = FindingCandidate.from_payload(
            {
                "vuln_found": True,
                "vuln_type": "SQL injection (potential)",
                "vulnerable_line": 'query = "SELECT * FROM users WHERE id=" + user_id',
                "pattern": "User input is concatenated into SQL.",
                "attack_scenario": "Attacker can inject SQL.",
                "suggested_fix": "Use parameterized queries or prepared statements to separate user input from SQL code.",
                "confidence": 0.8,
            }
        )
        self.assertEqual("SQL Injection", finding.vuln_type)
        self.assertIn("db.execute(query, (user_id,))", finding.suggested_fix)

    def test_score_penalties_and_diffs_are_deterministic(self):
        findings = [
            FindingRecord(
                key="security:SQL Injection:query",
                dimension="security",
                issue_type="SQL Injection",
                severity="CRITICAL",
                line="query = raw_sql",
                explanation="unsafe",
            )
        ]
        scores = merge_dimension_scores(previous=None, findings=findings, evaluated_dimensions=["security"])
        self.assertEqual(60, scores.security)
        self.assertEqual(100, scores.quality)
        self.assertEqual(87, scores.overall)

        improved_scores = merge_dimension_scores(previous=scores, findings=[], evaluated_dimensions=["security"])
        delta = diff_findings(
            previous=findings,
            current=[],
            previous_scores=scores,
            current_scores=improved_scores,
        )
        self.assertEqual(13, delta.score_delta)
        self.assertEqual(["security:SQL Injection:query"], delta.fixed_findings)
        self.assertEqual([], delta.new_findings)


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

    def test_registry_rejects_duplicate_tools(self):
        registry = AgentRegistry()
        spec = ToolSpec(
            name="analyze_code",
            description="Analyze code",
            input_schema={"type": "object", "properties": {}, "required": []},
            handler=lambda context, arguments: {"ok": True},
        )
        registry.register_tool(spec)
        with self.assertRaises(ValueError):
            registry.register_tool(spec)


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
                        "intent": "security",
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
                        "severity": "High",
                        "owasp_category": "A05:2017 - Injection",
                        "cve_reference": "GENERIC",
                        "data_flow": "user input flows into db.execute",
                        "developer_note": "Use bound parameters.",
                        "full_explanation": "String concatenation turns data into executable SQL.",
                    },
                },
            )
            result = service.analyze(AnalysisRequest(code="query = ...", developer_id="alice"))
            self.assertEqual("success", result.status)
            self.assertEqual("CRITICAL", result.severity)
            self.assertEqual("A03:2021 - Injection", result.owasp_category)
            self.assertNotEqual("security", result.planning["intent"])
            self.assertEqual(1, len(repo.get_developer_history("alice")))

    def test_security_agent_is_skipped_when_no_finding_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, _ = build_service(
                Path(tmpdir),
                responses={
                    "planning": {
                        "intent": "Add numbers.",
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
            result = service.analyze(AnalysisRequest(code="return a + b", developer_id="alice"))
            self.assertEqual("success", result.status)
            self.assertEqual(
                "skipped",
                next(entry.status for entry in result.agent_trace if entry.name == "security"),
            )

    def test_file_analysis_creates_event_and_file_state_with_scores(self):
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
            request = AnalysisRequest(
                code='query = "SELECT * FROM users WHERE id=" + user_id',
                developer_id="alice",
                file_uri="file:///demo.py",
                source="ide_extension",
            )
            result = service.analyze(request)
            self.assertEqual("success", result.status)
            self.assertTrue(result.event_id)
            self.assertEqual("file:///demo.py", result.file_uri)
            self.assertEqual(60, result.scores["security"])
            self.assertEqual(0, result.diff["score_delta"])
            self.assertEqual(1, result.diff["new_issue_count"])

            state = repo.get_file_state("alice", "file:///demo.py")
            self.assertIsNotNone(state)
            self.assertEqual(result.event_id, state.last_event_id)

    def test_reanalysis_tracks_improvement_and_skips_duplicate_hashes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AppConfig(db_path=Path(tmpdir) / "memory.db")
            repository = SQLiteFindingsRepository(config.db_path)
            repository.initialize()
            registry = register_default_agents(AgentRegistry())

            insecure_provider = FakeProvider(
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
                }
            )
            insecure_service = AnalysisService(
                config=config,
                provider=insecure_provider,
                repository=repository,
                registry=registry,
            )
            insecure_code = 'query = "SELECT * FROM users WHERE id=" + user_id'
            insecure_result = insecure_service.analyze(
                AnalysisRequest(code=insecure_code, developer_id="alice", file_uri="file:///demo.py")
            )
            self.assertEqual(1, len(repository.list_analysis_events("alice", "file:///demo.py")))

            clean_provider = FakeProvider(
                responses={
                    "planning": {
                        "intent": "Query user data safely.",
                        "entry_points": ["user_id"],
                        "sensitive_operations": ["db.execute"],
                        "security_focus": ["SQL Injection"],
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
                }
            )
            clean_service = AnalysisService(
                config=config,
                provider=clean_provider,
                repository=repository,
                registry=registry,
            )
            clean_code = 'query = "SELECT * FROM users WHERE id = ?"\nreturn db.execute(query, (user_id,))'
            clean_result = clean_service.analyze(
                AnalysisRequest(code=clean_code, developer_id="alice", file_uri="file:///demo.py")
            )
            self.assertEqual("success", clean_result.status)
            self.assertEqual(100, clean_result.scores["security"])
            self.assertGreater(clean_result.diff["score_delta"], 0)
            self.assertEqual(1, clean_result.diff["fixed_count"])
            self.assertEqual(2, len(repository.list_analysis_events("alice", "file:///demo.py")))

            repeat_result = clean_service.analyze(
                AnalysisRequest(code=clean_code, developer_id="alice", file_uri="file:///demo.py")
            )
            self.assertEqual(clean_result.event_id, repeat_result.event_id)
            self.assertEqual(2, len(repository.list_analysis_events("alice", "file:///demo.py")))
            self.assertNotEqual(insecure_result.event_id, clean_result.event_id)

    def test_missing_file_uri_skips_event_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service, repo = build_service(
                Path(tmpdir),
                responses={
                    "planning": {
                        "intent": "Print a value.",
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
            result = service.analyze(AnalysisRequest(code="print('hi')", developer_id="alice"))
            self.assertEqual("", result.event_id)
            self.assertEqual([], repo.list_analysis_events("alice"))

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
                    artifact_key="annotate",
                    runner=lambda context: (
                        context.set_artifact("annotate", {"note": "annotated"}),
                        context.response.warnings.append("annotated"),
                    ),
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
    def test_http_invalid_mode_returns_normalized_failure_response(self):
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        response = client.post(
            "/analyze",
            json={"code": "print(1)", "developer_id": "alice", "mode": "banana"},
        )
        payload = response.get_json()
        self.assertEqual(400, response.status_code)
        self.assertEqual("failed", payload["status"])
        self.assertIn("Unsupported analysis mode", payload["errors"][0])

    def test_http_and_mcp_share_failed_response_shape_for_invalid_mode(self):
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()
        http_payload = client.post(
            "/analyze",
            json={"code": "print(1)", "developer_id": "alice", "mode": "banana"},
        ).get_json()

        async def invoke():
            result = await call_tool(
                "analyze_code",
                {"code": "print(1)", "developer_id": "alice", "mode": "banana"},
            )
            return json.loads(result[0].text)

        mcp_payload = __import__("asyncio").run(invoke())
        self.assertEqual(http_payload, mcp_payload)

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

    def test_mcp_unknown_tool_returns_registry_error_payload(self):
        async def invoke():
            result = await call_tool("does_not_exist", {})
            return json.loads(result[0].text)

        payload = __import__("asyncio").run(invoke())
        self.assertEqual({"error": "Unknown tool: does_not_exist"}, payload)

    def test_mcp_list_tools_reads_from_registered_tool_specs(self):
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
            import appsec_agent.server as mcp_server

            registry = register_default_tools(register_default_agents(AgentRegistry()))
            registry.register_tool(
                ToolSpec(
                    name="ping",
                    description="Return a pong payload.",
                    input_schema={"type": "object", "properties": {}, "required": []},
                    handler=lambda context, arguments: {"pong": True},
                    implementation_ref="tests.ping",
                )
            )

            mcp_server.get_analysis_service = lambda: service
            mcp_server.get_repository = lambda: repo
            mcp_server.get_plugin_registry = lambda: registry

            async def list_registered():
                tools = await list_tools()
                return sorted(tool.name for tool in tools)

            names = __import__("asyncio").run(list_registered())
            self.assertIn("ping", names)
            self.assertIn("analyze_code", names)

    def test_http_dashboard_timeline_and_file_state_endpoints(self):
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
            service.analyze(
                AnalysisRequest(
                    code='query = "SELECT * FROM users WHERE id=" + user_id',
                    developer_id="alice",
                    file_uri="file:///demo.py",
                )
            )
            app = create_app()
            app.config["TESTING"] = True
            client = app.test_client()
            import appsec_agent.http_server as http_server

            http_server.get_analysis_service = lambda: service
            http_server.get_repository = lambda: repo

            dashboard = client.get("/dashboard", query_string={"developer_id": "alice"}).get_json()
            timeline = client.get("/timeline", query_string={"developer_id": "alice", "file_uri": "file:///demo.py"}).get_json()
            file_state = client.get(
                "/file-state",
                query_string={"developer_id": "alice", "file_uri": "file:///demo.py"},
            ).get_json()

            self.assertEqual(1, dashboard["total_files"])
            self.assertEqual(1, len(timeline))
            self.assertEqual("file:///demo.py", file_state["file_uri"])
            self.assertEqual("CRITICAL", file_state["findings"][0]["severity"])

    def test_mcp_dashboard_tools_share_backend_state(self):
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
            service.analyze(
                AnalysisRequest(
                    code='query = "SELECT * FROM users WHERE id=" + user_id',
                    developer_id="alice",
                    file_uri="file:///demo.py",
                    source="mcp_agent",
                )
            )
            import appsec_agent.server as mcp_server

            mcp_server.get_analysis_service = lambda: service
            mcp_server.get_repository = lambda: repo

            async def invoke_dashboard():
                dashboard = await call_tool("get_dashboard", {"developer_id": "alice"})
                timeline = await call_tool(
                    "get_analysis_timeline",
                    {"developer_id": "alice", "file_uri": "file:///demo.py"},
                )
                file_state = await call_tool(
                    "get_file_state",
                    {"developer_id": "alice", "file_uri": "file:///demo.py"},
                )
                return (
                    json.loads(dashboard[0].text),
                    json.loads(timeline[0].text),
                    json.loads(file_state[0].text),
                )

            dashboard_payload, timeline_payload, file_state_payload = __import__("asyncio").run(invoke_dashboard())
            self.assertEqual(1, dashboard_payload["total_files"])
            self.assertEqual("mcp_agent", timeline_payload[0]["source"])
            self.assertEqual("file:///demo.py", file_state_payload["file_uri"])


if __name__ == "__main__":
    unittest.main()
