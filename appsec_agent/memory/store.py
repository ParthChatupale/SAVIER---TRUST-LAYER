from __future__ import annotations

import sqlite3
from pathlib import Path

from appsec_agent.core.config import AppConfig, load_config
from appsec_agent.core.models import DeveloperFinding


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
