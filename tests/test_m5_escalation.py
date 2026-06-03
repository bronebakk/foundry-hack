"""M5 — ESCALATE surface. The load-bearing guarantees (Invariants 2 & 6):

  * A risk indicator is SURFACED, never ACTED ON — viewing it writes nothing and triggers
    nothing. The only writes are explicit human dispositions (escalate / refer / review).
  * Escalation is human-initiated and lands in a human-owned inbox attributed to the worker
    (server-side author, D-004). The machine resolves nothing.
  * No "computer says no": the deny surface shows options + an alternative + a human-delivered
    path, never a machine-authored refusal.

These run offline (no OPENROUTER_API_KEY) — the escalation draft falls back to record-derived
text, so the tests are deterministic and make no network call.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import config, db as dbmod
from app.main import app
from app.models import Disposition, ProposalType
from app.services import decision_log, integrity

PERSONA = "leah-sumner"
RISK_RECORD = "leah-r2"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Isolated DB per test so we never touch the real foundry.db (mirrors M2)."""
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "test.db")
    dbmod.init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _count() -> int:
    with dbmod.get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM decision_log").fetchone()["c"]


def _escalate(client, persona=PERSONA, sign=True, **fields):
    """POST an escalation with a valid provenance signature (A08) unless sign=False."""
    data = {"disposition": "escalate", "proposal_text": "", "final_text": "", "model": ""}
    data.update(fields)
    if sign:
        data["proposal_sig"] = integrity.sign(integrity.provenance(
            persona, "escalation", "risk_flag", data["model"], data["proposal_text"]))
    return client.post(f"/escalation/{persona}/escalate", data=data)


def _refer(client, persona=PERSONA, sign=True, **fields):
    data = {"context_text": "", "final_text": ""}
    data.update(fields)
    if sign:
        data["proposal_sig"] = integrity.sign(integrity.provenance(
            persona, "escalation", "follow_up", "", data["context_text"]))
    return client.post(f"/escalation/{persona}/refer", data=data)


# --- The bright line: surfacing acts on nothing ---------------------------------------------

def test_viewing_the_risk_surface_records_nothing(client):
    """Loading the overview, the persona flag, and the inbox must create no decision-log
    entry and trigger no notification/referral (VAL-ESCALATE-001)."""
    assert _count() == 0
    assert client.get("/escalation/").status_code == 200
    assert client.get(f"/escalation/{PERSONA}").status_code == 200
    assert client.get("/escalation/inbox").status_code == 200
    assert _count() == 0  # nothing was written merely by looking


def test_inbox_is_empty_until_a_human_sends(client):
    body = client.get("/escalation/inbox").text
    assert "inbox is empty" in body.lower()


# --- Explainability: the flag traces to its source (Invariant 7) ----------------------------

def test_persona_page_surfaces_flag_with_source_and_rationale(client):
    body = client.get(f"/escalation/{PERSONA}").text
    # the source record id and its text are shown
    assert RISK_RECORD in body
    assert "said he is 24" in body  # verbatim from the source record
    # the category and the "why flagged" rationale are shown
    assert "CSE/CCE" in body
    assert "recognised indicators of exploitation" in body


def test_persona_page_states_no_automatic_action(client):
    body = client.get(f"/escalation/{PERSONA}").text
    assert "No automatic action has been or will be taken" in body


# --- Human-initiated escalation, human-owned routing (VAL-ESCALATE-002) ---------------------

def test_human_escalate_creates_entry_attributed_to_the_worker(client):
    assert _count() == 0
    resp = _escalate(client, proposal_text="Record-derived concern summary.",
                     final_text="I'm escalating this to the safeguarding lead today.")
    assert resp.status_code == 200
    assert _count() == 1
    entry = decision_log.list_entries(persona_id=PERSONA)[0]
    assert entry.disposition == Disposition.ESCALATE.value
    assert entry.proposal_type == ProposalType.RISK_FLAG.value
    assert entry.author == config.DEMO_WORKER          # human, server-side
    assert entry.author not in config.ALLOWED_MODELS   # never the AI (Invariant 5)
    assert entry.final_text == "I'm escalating this to the safeguarding lead today."


def test_escalate_ignores_any_client_supplied_author(client):
    """D-004: author is set server-side. A spoofed author field must be ignored."""
    _escalate(client, proposal_text="x", final_text="y",
              author="Mallory (spoofed)",        # must be ignored
              model=config.PRIMARY_MODEL)         # even a model id must never become author
    entry = decision_log.list_entries(persona_id=PERSONA)[0]
    assert entry.author == config.DEMO_WORKER


def test_escalation_arrives_in_the_human_owned_inbox(client):
    _escalate(client, proposal_text="ctx", final_text="Escalating for review.")
    body = client.get("/escalation/inbox").text
    assert "Leah Sumner" in body
    assert config.DEMO_WORKER in body          # attributed to the worker who sent it
    assert "Escalating for review." in body
    assert "Arrived because" in body           # framed as human-sent, not automatic


def test_machine_marks_nothing_resolved(client):
    """The inbox is human-owned: the system never sets a 'resolved' state."""
    _escalate(client, proposal_text="c", final_text="f")
    body = client.get("/escalation/inbox").text.lower()
    assert "awaiting human review" in body
    assert "resolved" not in body or "marks nothing" in body  # no machine-set resolution


# --- "Not now" is a logged human review, not an escalation ----------------------------------

def test_discard_records_a_review_and_does_not_reach_the_inbox(client):
    _escalate(client, disposition="discard", proposal_text="c", final_text="ignored")
    entry = decision_log.list_entries(persona_id=PERSONA)[0]
    assert entry.disposition == Disposition.DISCARD.value
    assert entry.final_text is None
    # a non-escalation must not appear in the escalation inbox
    assert "Leah Sumner" not in client.get("/escalation/inbox").text


# --- No "computer says no" (Invariant 2 / VAL-DENY-001) -------------------------------------

def test_deny_surface_has_no_machine_refusal_and_offers_alternative_and_human_path(client):
    body = client.get(f"/escalation/{PERSONA}").text
    low = body.lower()
    # no machine-authored refusal anywhere
    for refusal in ("application denied", "not eligible", "request rejected", "access denied"):
        assert refusal not in low
    # it surfaces the no-machine-"no" framing and a human-delivered path (alternatives are
    # data-driven from the records / delivered by the keyworker — see M6 test for Marcus).
    assert "isn't telling" in body  # explicit "the system isn't telling <name> 'no'"
    assert "Send to a keyworker to decide" in body


def test_refer_routes_the_decision_to_a_human(client):
    resp = _refer(client, context_text="course full; alternatives exist",
                  final_text="Please review Leah's options and get back to her.")
    assert resp.status_code == 200
    entry = decision_log.list_entries(persona_id=PERSONA)[0]
    assert entry.disposition == Disposition.ESCALATE.value      # routed to a human
    assert entry.proposal_type == ProposalType.FOLLOW_UP.value  # a decision a human must make
    assert entry.author == config.DEMO_WORKER
    # and it shows up in the human-owned queue as a decision needed
    inbox = client.get("/escalation/inbox").text
    assert "decision needed (human)" in inbox.lower()


# --- Unknown persona is harmless ------------------------------------------------------------

def test_unknown_persona_writes_nothing(client):
    resp = client.get("/escalation/ghost-persona")
    assert resp.status_code == 200
    assert _count() == 0
