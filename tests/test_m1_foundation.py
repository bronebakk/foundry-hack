"""M1 foundation checks. The load-bearing append-only guarantee (decision_log) is
tested test-first here because it underpins Invariant 1 / VAL-GOV-003 — M2 builds on it.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db, get_conn
from app.services import data
from app.services.inference import provider, ClosedModelRefused

client = TestClient(app)


def test_home_and_shell_render():
    r = client.get("/")
    assert r.status_code == 200
    assert "SYNTHETIC DEMO DATA" in r.text  # persistent synthetic marker (VAL-GOV-001)
    assert "Amara Okafor" in r.text


def test_all_stream_surfaces_routed():
    for path in ("/context/", "/drafting/", "/escalation/", "/governance/"):
        assert client.get(path).status_code == 200


def test_persona_records_visible_with_markers():
    r = client.get("/context/leah-sumner")
    assert r.status_code == 200
    assert "synthetic" in r.text
    assert "safeguarding signal" in r.text  # risk indicator surfaced, not acted on


def test_personas_loaded_and_one_has_risk_indicator():
    personas = data.list_personas()
    assert len(personas) == 3
    assert any(p.has_risk_indicator for p in personas)
    assert all(p.synthetic for p in personas)


def test_decision_log_is_append_only():
    """Append-only enforced at the DB layer: INSERT works, UPDATE/DELETE are blocked."""
    init_db()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO decision_log (surface, disposition, author) VALUES (?, ?, ?)",
            ("context", "discard", "test-worker"),
        )
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM decision_log ORDER BY id DESC LIMIT 1").fetchone()
        rid = row["id"]
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        with get_conn() as conn:
            conn.execute("UPDATE decision_log SET author = 'tamper' WHERE id = ?", (rid,))
    with pytest.raises(sqlite3.IntegrityError):
        with get_conn() as conn:
            conn.execute("DELETE FROM decision_log WHERE id = ?", (rid,))


def test_inference_refuses_closed_models():
    """Code-level guard for Invariant 4 / VAL-GOV-002: a closed model id is refused
    before any network call (so this passes even with no API key)."""
    with pytest.raises(ClosedModelRefused):
        provider.complete("hello", model="gpt-4o")


def test_healthz_reports_open_weight_allowlist():
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "openai/gpt-oss-120b" in body["allowed_models"]
