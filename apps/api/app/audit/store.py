"""Decision persistence (SQLite). Ephemeral on Render Free -- the audit
store is a session cache, not durable storage; `export_json` is what the
evaluation runner reads instead of depending on the live database file.

A fresh sqlite3 connection is opened per call rather than held open, which
is simple and avoids any cross-thread-safety questions in FastAPI's
threadpool-backed sync endpoints. Phase 1's traffic volume does not need
anything more sophisticated than this.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    interaction_id TEXT,
    customer_id TEXT,
    tier TEXT,
    questions_snapshot TEXT NOT NULL,
    answers TEXT NOT NULL,
    confidence_map TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    action TEXT NOT NULL,
    task_type TEXT,
    task_status TEXT,
    latency_ms REAL NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    mode TEXT NOT NULL,
    route TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class AuditStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save_decision(
        self,
        *,
        interaction_id: str | None,
        customer_id: str | None,
        tier: str,
        questions_snapshot: dict,
        answers: dict,
        confidence_map: dict,
        policy_version: str,
        action: str,
        task: dict | None,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        mode: str,
        route: str,
    ) -> str:
        decision_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO decisions (
                    id, interaction_id, customer_id, tier, questions_snapshot, answers,
                    confidence_map, policy_version, action, task_type, task_status,
                    latency_ms, input_tokens, output_tokens, mode, route, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    decision_id, interaction_id, customer_id, tier,
                    json.dumps(questions_snapshot), json.dumps(answers), json.dumps(confidence_map),
                    policy_version, action,
                    task.get("type") if task else None,
                    task.get("status") if task else None,
                    latency_ms, input_tokens, output_tokens, mode, route,
                    datetime.now(UTC).isoformat(),
                ),
            )
        return decision_id

    def daily_tokens_used(self) -> int:
        today = datetime.now(UTC).date().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(input_tokens), 0) FROM decisions WHERE created_at >= ? AND mode = 'live'",
                (today,),
            ).fetchone()
        return int(row[0])

    def list_confirmed_tasks(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, interaction_id, customer_id, task_type, task_status, created_at "
                "FROM decisions WHERE action = 'confirmed' ORDER BY created_at DESC"
            ).fetchall()
        return [
            {
                "decisionId": r["id"],
                "interactionId": r["interaction_id"],
                "customerId": r["customer_id"],
                "type": r["task_type"],
                "status": r["task_status"],
                "createdAt": r["created_at"],
            }
            for r in rows
        ]

    def export_json(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM decisions ORDER BY created_at").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["questions_snapshot"] = json.loads(d["questions_snapshot"])
            d["answers"] = json.loads(d["answers"])
            d["confidence_map"] = json.loads(d["confidence_map"])
            out.append(d)
        return out
