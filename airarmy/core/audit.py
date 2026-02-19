import sqlite3
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .config import config


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.AUDIT_LOG_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            session_id  TEXT NOT NULL,
            agent       TEXT NOT NULL,
            action_type TEXT NOT NULL,
            action      TEXT NOT NULL,
            approved    INTEGER,
            result      TEXT,
            tokens_used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn


def log_action(
    session_id: str,
    agent: str,
    action_type: str,
    action: str,
    approved: bool | None = None,
    result: str | None = None,
    tokens_used: int = 0,
) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO audit_log "
        "(ts, session_id, agent, action_type, action, approved, result, tokens_used) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.now(UTC).isoformat(),
            session_id,
            agent,
            action_type,
            action,
            int(approved) if approved is not None else None,
            result,
            tokens_used,
        ),
    )
    conn.commit()
    conn.close()


def get_session_logs(session_id: str) -> list[dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM audit_log WHERE session_id = ? ORDER BY ts",
        (session_id,),
    ).fetchall()
    conn.close()
    cols = [
        "id",
        "ts",
        "session_id",
        "agent",
        "action_type",
        "action",
        "approved",
        "result",
        "tokens_used",
    ]
    return [dict(zip(cols, row)) for row in rows]
