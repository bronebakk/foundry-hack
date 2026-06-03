"""M4 — DRAFT surface: drafting, authorship & the propose-not-act boundary.

Test-first on the load-bearing guarantees (CLAUDE.md selective test-first policy):
  * generation persists nothing — only an explicit human disposition writes (VAL-PROPOSE-001);
  * a follow-up is only "sent" on an explicit send (VAL-PROPOSE-002);
  * the committed record is the worker's edited text, attributed to the worker, not the AI,
    and authorship cannot be spoofed from a client form field (VAL-DRAFT-002 / D-004).

These exercise the HTTP layer (the surface a judge actually drives), with inference stubbed
so the tests are hermetic — no network, no API key required.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import config
from app import db as dbmod
from app.main import app
from app.services import decision_log, integrity
from app.services.inference import Completion

client = TestClient(app)

PERSONA = "leah-sumner"


class _FakeProvider:
    """Deterministic stand-in for the open-weight provider — no network."""

    def __init__(self, configured: bool = True, model: str = config.PRIMARY_MODEL):
        self._configured = configured
        self._model = model

    @property
    def configured(self) -> bool:
        return self._configured

    def complete(self, prompt, *, system=None, model=None, **kw) -> Completion:
        return Completion(text="AI-DRAFTED-TEXT", model=self._model)


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Isolated DB per test so we never touch the real foundry.db."""
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "test.db")
    dbmod.init_db()
    yield


@pytest.fixture
def live_provider(monkeypatch):
    fake = _FakeProvider(configured=True)
    monkeypatch.setattr("app.routers.drafting.provider", fake)
    return fake


def _count() -> int:
    with dbmod.get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM decision_log").fetchone()["c"]


def _dispose(sign=True, **fields):
    base = {
        "persona_id": PERSONA,
        "surface": "drafting",
        "proposal_type": "case_note",
        "proposal_text": "AI proposal v1",
        "model": config.PRIMARY_MODEL,
    }
    base.update(fields)
    if sign:  # a legitimate disposition carries the server's provenance signature (A08)
        base["proposal_sig"] = integrity.sign(integrity.provenance(
            PERSONA, base["surface"], base["proposal_type"], base["model"], base["proposal_text"]))
    return client.post(f"/drafting/{PERSONA}/dispose", data=base)


# --- Reachability ---

def test_drafting_home_lists_personas():
    r = client.get("/drafting/")
    assert r.status_code == 200
    assert "Leah Sumner" in r.text


def test_workbench_renders_with_two_draft_actions():
    r = client.get(f"/drafting/{PERSONA}")
    assert r.status_code == 200
    assert "case note" in r.text.lower()
    assert "follow-up" in r.text.lower()


# --- VAL-PROPOSE-001: generation persists nothing ---

def test_generation_persists_nothing(live_provider):
    assert _count() == 0
    client.get(f"/drafting/{PERSONA}")                     # viewing writes nothing
    assert _count() == 0
    r = client.post(
        f"/drafting/{PERSONA}/generate",
        data={"proposal_type": "case_note", "meeting_notes": "Met at the cafe."},
    )
    assert r.status_code == 200
    assert "AI-DRAFTED-TEXT" in r.text
    # The draft is framed as an uncommitted proposal, not a record of truth.
    assert "not committed" in r.text.lower()
    assert _count() == 0                                   # ...and STILL nothing written


def test_generation_works_without_inference_key(monkeypatch):
    """If the provider is unconfigured, we still demonstrate the boundary with a clearly
    marked canned draft — no 500, and still no write."""
    monkeypatch.setattr("app.routers.drafting.provider", _FakeProvider(configured=False))
    r = client.post(f"/drafting/{PERSONA}/generate", data={"proposal_type": "follow_up"})
    assert r.status_code == 200
    assert "not configured" in r.text.lower()             # clearly marked
    assert _count() == 0


# --- VAL-DRAFT-002 / Invariant 5: worker authorship, no spoofing ---

def test_commit_records_worker_edited_text_attributed_to_worker():
    r = _dispose(
        disposition="commit",
        proposal_text="AI proposal v1",
        final_text="Worker's own edited words.",
        author="HACKER (spoofed)",          # must be ignored — author is server-side (D-004)
    )
    assert r.status_code == 200
    entries = decision_log.list_entries(PERSONA)
    assert len(entries) == 1
    e = entries[0]
    assert e.disposition == "commit"
    assert e.final_text == "Worker's own edited words."   # the worker's version is the truth
    assert e.proposal_text == "AI proposal v1"            # original AI proposal preserved
    assert e.author == config.DEMO_WORKER                 # NEVER the spoofed value, never the AI
    # The committed view attributes to the worker, not the AI.
    assert config.DEMO_WORKER in r.text
    assert "generated by ai" not in r.text.lower()


# --- VAL-PROPOSE-002: nothing sent until an explicit send ---

def test_no_send_entry_until_explicit_send():
    # No send has happened yet.
    assert not any(e.disposition == "send" for e in decision_log.list_entries(PERSONA))
    r = _dispose(
        proposal_type="follow_up",
        disposition="send",
        proposal_text="Hi Leah, ...",
        final_text="Hi Leah, see you Thursday.",
    )
    assert r.status_code == 200
    sends = [e for e in decision_log.list_entries(PERSONA) if e.disposition == "send"]
    assert len(sends) == 1
    assert sends[0].proposal_type == "follow_up"
    assert sends[0].author == config.DEMO_WORKER


# --- Discard keeps nothing ---

def test_discard_is_logged_but_keeps_no_text():
    r = _dispose(disposition="discard", final_text="should be ignored")
    assert r.status_code == 200
    entries = decision_log.list_entries(PERSONA)
    assert len(entries) == 1
    assert entries[0].disposition == "discard"
    assert entries[0].final_text is None
