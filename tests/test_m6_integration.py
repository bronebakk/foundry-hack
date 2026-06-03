"""M6 — integration & governance polish. Cross-surface checks that no single stream could make:

  * the governance decision-log viewer renders AI proposal → human disposition → worker
    attribution, is append-only (no edit/delete affordance), and exposes open-weight-only
    inference provenance with no closed model in the path (VAL-GOV-003 / VAL-GOV-002);
  * the hero personas promoted from staging at M6 are live and render across surfaces, with
    the DENY surface now data-driven per persona (Marcus shows his own routes, not Leah's);
  * the synthetic markers hold across every persona (VAL-GOV-001);
  * the app is robust without the ASGI lifespan (import-time init_db, D-007).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import config, db as dbmod
from app.main import app
from app.models import Proposal, Surface, ProposalType, Disposition
from app.services import data, decision_log


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "test.db")
    dbmod.init_db()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _seed_one(disposition, ptype=ProposalType.CASE_NOTE, persona="noah-bennett",
              proposal="AI draft.", final="Worker's edited words.", model="openai/gpt-oss-120b"):
    p = Proposal(persona_id=persona, surface=Surface.DRAFTING, proposal_type=ptype,
                 proposal_text=proposal, model=model)
    return decision_log.record(p, disposition, author=config.DEMO_WORKER, final_text=final)


# --- The hero personas are live (D-005) ---

def test_six_personas_live_and_render_across_surfaces(client):
    personas = data.list_personas()
    assert len(personas) == 6
    assert all(p.synthetic for p in personas)  # VAL-GOV-001
    for pid in ("ivy-castellano", "marcus-fielding", "noah-bennett"):
        for surface in ("context", "drafting", "escalation"):
            assert client.get(f"/{surface}/{pid}").status_code == 200


def test_deny_surface_is_data_driven_not_hardcoded(client):
    """Promoting Marcus exposed a latent coupling: the DENY block hardcoded Leah's course.
    It must now reflect each persona's own records."""
    marcus = client.get("/escalation/marcus-fielding").text
    assert "Hair" not in marcus                      # no Leah leakage
    assert "isn't telling Marcus" in marcus          # no machine "no", named correctly
    assert "Advanced Learner Loan" in marcus         # his own routes, from his records
    # Leah's deny surface still holds (no machine refusal, human handoff present)
    leah = client.get("/escalation/leah-sumner").text
    assert "Northgate College" not in leah           # old hardcode gone
    assert "isn't telling Leah" in leah
    assert "Send to a keyworker to decide" in leah


# --- Governance decision-log viewer (VAL-GOV-003) ---

def test_governance_empty_state(client):
    body = client.get("/governance/").text
    assert "No decisions logged yet" in body
    assert "ppend-only" in body  # the immutability framing is always shown


def test_governance_renders_proposal_disposition_and_attribution(client):
    _seed_one(Disposition.COMMIT, proposal="AI-suggested note text.",
              final="The worker edited this note herself.")
    body = client.get("/governance/").text
    assert "AI-suggested note text." in body            # the original proposal, verbatim
    assert "The worker edited this note herself." in body  # the human's committed text
    assert config.DEMO_WORKER in body                  # worker is the author of record
    assert "committed as their note" in body           # human disposition, human-framed


def test_governance_shows_all_disposition_kinds(client):
    _seed_one(Disposition.COMMIT)
    _seed_one(Disposition.SEND, ptype=ProposalType.FOLLOW_UP)
    _seed_one(Disposition.ESCALATE, ptype=ProposalType.RISK_FLAG, persona="leah-sumner")
    _seed_one(Disposition.DISCARD, final=None)
    body = client.get("/governance/").text
    for badge in ("badge-commit", "badge-send", "badge-escalate", "badge-discard"):
        assert badge in body


def test_governance_filters_by_persona(client):
    _seed_one(Disposition.COMMIT, persona="noah-bennett", final="noah-note")
    _seed_one(Disposition.COMMIT, persona="leah-sumner", final="leah-note")
    only_leah = client.get("/governance/?persona_id=leah-sumner").text
    assert "leah-note" in only_leah
    assert "noah-note" not in only_leah


def test_governance_exposes_open_weight_provenance_only(client):
    body = client.get("/governance/").text
    assert "openai/gpt-oss-120b" in body
    assert "meta-llama/llama-3.3-70b-instruct" in body
    # no closed/proprietary model id may appear anywhere in the governance surface (VAL-GOV-002)
    low = body.lower()
    for closed in ("gpt-4", "gpt-3.5", "claude", "gemini", "mistral-large"):
        assert closed not in low


def test_governance_has_no_mutation_affordance(client):
    """Append-only by construction: the viewer offers no edit/delete control."""
    _seed_one(Disposition.COMMIT)
    body = client.get("/governance/").text.lower()
    # no form that could mutate the log, no delete/edit buttons on this read-only surface
    assert "<form" not in body
    for verb in (">edit<", ">delete<", ">remove<"):
        assert verb not in body


# --- Robustness without lifespan (D-007) ---

def test_app_serves_db_reading_routes_without_lifespan(client):
    """A module-level TestClient never triggers lifespan; import-time init_db must mean the
    decision-log-reading GETs still work (the regression M6 caught and fixed)."""
    for path in ("/escalation/", "/escalation/inbox", "/governance/"):
        assert client.get(path).status_code == 200
