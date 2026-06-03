"""The decision-log service — the SINGLE write path to the immutable governance spine.
FROZEN after M2. Used by every stream to record what the human did with an AI proposal.

Design guarantees (load-bearing for Invariant 1 / VAL-PROPOSE-001 / VAL-GOV-003):

  * ``record(...)`` is the only function here that writes. There is deliberately NO
    update() and NO delete() — the log can be appended to but never altered through this
    service. (The DB layer also enforces this with triggers; this is defence in depth.)
  * A row is only ever written as the result of an explicit human ``Disposition``. Nothing
    in this module is called during generation — generation (InferenceProvider) and
    disposition (here) are separate steps by construction.
"""
from __future__ import annotations

from app.db import get_conn
from app.models import Proposal, Disposition, DecisionLogEntry


def record(
    proposal: Proposal,
    disposition: Disposition,
    author: str,
    final_text: str | None = None,
) -> DecisionLogEntry:
    """Append one decision-log entry: the AI proposal + the human's disposition of it.

    ``author`` is always the human worker of record — never the AI (Invariant 5).
    ``final_text`` is the human-edited committed text for COMMIT/SEND/ESCALATE; for
    DISCARD it is left None (nothing was kept).
    """
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO decision_log
                (persona_id, surface, proposal_type, proposal_text, disposition, final_text, author, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal.persona_id,
                proposal.surface.value,
                proposal.proposal_type.value,
                proposal.proposal_text,
                disposition.value,
                final_text,
                author,
                proposal.model,
            ),
        )
        new_id = cur.lastrowid
    return get_entry(new_id)


def get_entry(entry_id: int) -> DecisionLogEntry:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM decision_log WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        raise KeyError(f"No decision_log entry {entry_id}")
    return DecisionLogEntry.from_row(row)


def list_entries(persona_id: str | None = None) -> list[DecisionLogEntry]:
    """Newest first. Optionally filtered to one persona. Read-only."""
    sql = "SELECT * FROM decision_log"
    params: tuple = ()
    if persona_id is not None:
        sql += " WHERE persona_id = ?"
        params = (persona_id,)
    sql += " ORDER BY id DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [DecisionLogEntry.from_row(r) for r in rows]
