from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from appsec_agent.core.config import AppConfig, load_config
from appsec_agent.core.models import (
    AnalysisEvent,
    DashboardSummary,
    DeveloperFinding,
    DimensionScores,
    FileState,
    FindingRecord,
    ScoreDelta,
)


class SQLiteFindingsRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    developer TEXT NOT NULL,
                    vuln_type TEXT NOT NULL,
                    code_snippet TEXT,
                    explanation TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    developer_id TEXT NOT NULL,
                    file_uri TEXT NOT NULL,
                    source TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    project_id TEXT,
                    overall_score INTEGER NOT NULL,
                    security_score INTEGER NOT NULL,
                    quality_score INTEGER NOT NULL,
                    performance_score INTEGER NOT NULL,
                    fixed_count INTEGER NOT NULL,
                    new_issue_count INTEGER NOT NULL,
                    unchanged_count INTEGER NOT NULL,
                    findings_json TEXT NOT NULL,
                    summary_json TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_states (
                    developer_id TEXT NOT NULL,
                    file_uri TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    last_event_id TEXT,
                    source TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    project_id TEXT,
                    overall_score INTEGER NOT NULL,
                    security_score INTEGER NOT NULL,
                    quality_score INTEGER NOT NULL,
                    performance_score INTEGER NOT NULL,
                    findings_json TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (developer_id, file_uri)
                )
                """
            )
            conn.commit()

    def save_finding(self, developer: str, vuln_type: str, code_snippet: str, explanation: str) -> None:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO findings (developer, vuln_type, code_snippet, explanation)
                VALUES (?, ?, ?, ?)
                """,
                (developer, vuln_type, code_snippet, explanation),
            )
            conn.commit()

    def get_developer_history(self, developer: str, limit: int = 5) -> list[DeveloperFinding]:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT vuln_type, code_snippet, explanation, timestamp
                FROM findings
                WHERE developer = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (developer, limit),
            )
            return [
                DeveloperFinding(
                    vuln_type=row[0],
                    code_snippet=row[1] or "",
                    explanation=row[2] or "",
                    timestamp=row[3] or "",
                )
                for row in cursor.fetchall()
            ]

    def clear_developer_history(self, developer: str) -> None:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM findings WHERE developer = ?", (developer,))
            conn.execute("DELETE FROM analysis_events WHERE developer_id = ?", (developer,))
            conn.execute("DELETE FROM file_states WHERE developer_id = ?", (developer,))
            conn.commit()

    def clear_analysis_history(self, developer: str) -> None:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM analysis_events WHERE developer_id = ?", (developer,))
            conn.execute("DELETE FROM file_states WHERE developer_id = ?", (developer,))
            conn.commit()

    def get_repeated_vulns(self, developer: str) -> list[str]:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT vuln_type, COUNT(*) as cnt
                FROM findings
                WHERE developer = ?
                GROUP BY vuln_type
                HAVING cnt > 1
                ORDER BY cnt DESC
                """,
                (developer,),
            )
            return [row[0] for row in cursor.fetchall()]

    def get_file_state(self, developer_id: str, file_uri: str) -> FileState | None:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT *
                FROM file_states
                WHERE developer_id = ? AND file_uri = ?
                """,
                (developer_id, file_uri),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_file_state(row)

    def upsert_file_state(self, file_state: FileState) -> None:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO file_states (
                    developer_id,
                    file_uri,
                    content_hash,
                    last_event_id,
                    source,
                    mode,
                    status,
                    project_id,
                    overall_score,
                    security_score,
                    quality_score,
                    performance_score,
                    findings_json,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(developer_id, file_uri) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    last_event_id = excluded.last_event_id,
                    source = excluded.source,
                    mode = excluded.mode,
                    status = excluded.status,
                    project_id = excluded.project_id,
                    overall_score = excluded.overall_score,
                    security_score = excluded.security_score,
                    quality_score = excluded.quality_score,
                    performance_score = excluded.performance_score,
                    findings_json = excluded.findings_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    file_state.developer_id,
                    file_state.file_uri,
                    file_state.content_hash,
                    file_state.last_event_id,
                    file_state.source,
                    file_state.mode,
                    file_state.status,
                    file_state.project_id,
                    file_state.scores.overall,
                    file_state.scores.security,
                    file_state.scores.quality,
                    file_state.scores.performance,
                    json.dumps([finding.to_dict() for finding in file_state.findings]),
                ),
            )
            conn.commit()

    def insert_analysis_event(self, event: AnalysisEvent) -> AnalysisEvent:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_events (
                    developer_id,
                    file_uri,
                    source,
                    mode,
                    content_hash,
                    status,
                    project_id,
                    overall_score,
                    security_score,
                    quality_score,
                    performance_score,
                    fixed_count,
                    new_issue_count,
                    unchanged_count,
                    findings_json,
                    summary_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.developer_id,
                    event.file_uri,
                    event.source,
                    event.mode,
                    event.content_hash,
                    event.status,
                    event.project_id,
                    event.scores.overall,
                    event.scores.security,
                    event.scores.quality,
                    event.scores.performance,
                    event.diff.fixed_count,
                    event.diff.new_issue_count,
                    event.diff.unchanged_count,
                    json.dumps([finding.to_dict() for finding in event.findings]),
                    json.dumps(
                        {
                            "diff": event.diff.to_dict(),
                            "summary": event.summary,
                        }
                    ),
                ),
            )
            event_id = str(cursor.lastrowid)
            timestamp_row = conn.execute(
                "SELECT timestamp FROM analysis_events WHERE id = ?",
                (event_id,),
            ).fetchone()
            conn.commit()
        return AnalysisEvent(
            event_id=event_id,
            developer_id=event.developer_id,
            file_uri=event.file_uri,
            source=event.source,
            mode=event.mode,
            content_hash=event.content_hash,
            status=event.status,
            timestamp=str(timestamp_row[0]) if timestamp_row else event.timestamp,
            project_id=event.project_id,
            scores=event.scores,
            findings=event.findings,
            diff=event.diff,
            summary=event.summary,
        )

    def list_analysis_events(self, developer_id: str, file_uri: str | None = None, limit: int = 20) -> list[AnalysisEvent]:
        self.initialize()
        query = """
            SELECT *
            FROM analysis_events
            WHERE developer_id = ?
        """
        params: list[object] = [developer_id]
        if file_uri:
            query += " AND file_uri = ?"
            params.append(file_uri)
        query += " ORDER BY timestamp DESC, id DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_analysis_event(row) for row in rows]

    def get_dashboard_summary(self, developer_id: str) -> DashboardSummary:
        self.initialize()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            state_rows = conn.execute(
                """
                SELECT *
                FROM file_states
                WHERE developer_id = ?
                ORDER BY updated_at DESC
                """,
                (developer_id,),
            ).fetchall()
            event_rows = conn.execute(
                """
                SELECT *
                FROM analysis_events
                WHERE developer_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT 25
                """,
                (developer_id,),
            ).fetchall()

        current_files = [self._row_to_file_state(row) for row in state_rows]
        recent_events = [self._row_to_analysis_event(row) for row in event_rows]
        total_files = len(current_files)
        total_events = len(recent_events)
        files_with_findings = sum(1 for item in current_files if item.findings)
        open_findings = sum(len(item.findings) for item in current_files)
        if total_files:
            average_scores = DimensionScores(
                security=round(sum(item.scores.security for item in current_files) / total_files),
                quality=round(sum(item.scores.quality for item in current_files) / total_files),
                performance=round(sum(item.scores.performance for item in current_files) / total_files),
                overall=round(sum(item.scores.overall for item in current_files) / total_files),
            )
        else:
            average_scores = DimensionScores()

        score_trend = [
            {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "file_uri": event.file_uri,
                "overall_score": event.scores.overall,
            }
            for event in recent_events
        ]

        return DashboardSummary(
            developer_id=developer_id,
            total_files=total_files,
            total_events=total_events,
            files_with_findings=files_with_findings,
            open_findings=open_findings,
            average_scores=average_scores,
            score_trend=score_trend,
            current_files=current_files,
            recent_events=recent_events,
        )

    def _row_to_file_state(self, row: sqlite3.Row) -> FileState:
        findings = [FindingRecord(**item) for item in json.loads(row["findings_json"] or "[]")]
        return FileState(
            developer_id=str(row["developer_id"]),
            file_uri=str(row["file_uri"]),
            content_hash=str(row["content_hash"]),
            last_event_id=str(row["last_event_id"] or ""),
            source=str(row["source"] or ""),
            mode=str(row["mode"] or "security"),
            status=str(row["status"] or "success"),
            updated_at=str(row["updated_at"] or ""),
            project_id=str(row["project_id"] or ""),
            scores=DimensionScores(
                security=int(row["security_score"] or 100),
                quality=int(row["quality_score"] or 100),
                performance=int(row["performance_score"] or 100),
                overall=int(row["overall_score"] or 100),
            ),
            findings=findings,
        )

    def _row_to_analysis_event(self, row: sqlite3.Row) -> AnalysisEvent:
        findings = [FindingRecord(**item) for item in json.loads(row["findings_json"] or "[]")]
        summary_payload = json.loads(row["summary_json"] or "{}")
        diff_payload = summary_payload.get("diff", {})
        return AnalysisEvent(
            event_id=str(row["id"]),
            developer_id=str(row["developer_id"]),
            file_uri=str(row["file_uri"]),
            source=str(row["source"] or ""),
            mode=str(row["mode"] or "security"),
            content_hash=str(row["content_hash"]),
            status=str(row["status"] or "success"),
            timestamp=str(row["timestamp"] or ""),
            project_id=str(row["project_id"] or ""),
            scores=DimensionScores(
                security=int(row["security_score"] or 100),
                quality=int(row["quality_score"] or 100),
                performance=int(row["performance_score"] or 100),
                overall=int(row["overall_score"] or 100),
            ),
            findings=findings,
            diff=ScoreDelta(
                score_delta=int(diff_payload.get("score_delta", 0)),
                fixed_findings=list(diff_payload.get("fixed_findings", [])),
                new_findings=list(diff_payload.get("new_findings", [])),
                unchanged_findings=list(diff_payload.get("unchanged_findings", [])),
            ),
            summary=dict(summary_payload.get("summary", {})),
        )


def get_repository(config: AppConfig | None = None) -> SQLiteFindingsRepository:
    config = config or load_config()
    return SQLiteFindingsRepository(config.db_path)


def get_developer_history(developer: str) -> list[dict]:
    return [finding.to_dict() for finding in get_repository().get_developer_history(developer)]


def save_finding(developer: str, vuln_type: str, code_snippet: str, explanation: str) -> None:
    get_repository().save_finding(developer, vuln_type, code_snippet, explanation)


def clear_developer_history(developer: str) -> None:
    get_repository().clear_developer_history(developer)


def get_repeated_vulns(developer: str) -> list[str]:
    return get_repository().get_repeated_vulns(developer)


DB_PATH = load_config().db_path
