"""SQLite storage. The load-bearing structure here is the append-only ``decision_log``
table — the immutable governance spine (Invariant 1, VAL-GOV-003). Append-only is
enforced at the DB layer by triggers that ABORT any UPDATE or DELETE, so there is no
edit/delete path even in principle. M2 builds the service API over this; M4 adds the
worker-authored records table.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from collections.abc import Iterator

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    persona_id   TEXT,
    surface      TEXT NOT NULL,   -- 'context' | 'drafting' | 'escalation'
    proposal_type TEXT,           -- 'brief' | 'case_note' | 'follow_up' | 'risk_flag'
    proposal_text TEXT,           -- the AI proposal exactly as generated
    disposition  TEXT NOT NULL,   -- human action: 'commit' | 'discard' | 'send' | 'escalate'
    final_text   TEXT,            -- human-edited committed text (NULL if discarded)
    author       TEXT NOT NULL,   -- the human worker of record (never the AI)
    model        TEXT             -- which open-weight model produced the proposal
);

-- Append-only enforcement: the decision log can be added to but never silently altered.
CREATE TRIGGER IF NOT EXISTS decision_log_no_update
BEFORE UPDATE ON decision_log
BEGIN
    SELECT RAISE(ABORT, 'decision_log is append-only: UPDATE blocked');
END;

CREATE TRIGGER IF NOT EXISTS decision_log_no_delete
BEFORE DELETE ON decision_log
BEGIN
    SELECT RAISE(ABORT, 'decision_log is append-only: DELETE blocked');
END;
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Idempotent — safe to call on every startup."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
