"""Security-hardening tests (from the security audit, PR #7).

Covers the fixes that protect the running demo and the governance claim:
  * A08 — the decision log will not accept a forged AI-proposal text or model attribution;
  * A01/A02 — security response headers + cross-origin write protection;
  * A05/LLM01 — denial-language output guard on outbound drafts;
  * A07 — constant-time auth for unknown usernames.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import config, db as dbmod
from app.main import app
from app.services import data, decision_log, integrity, safety
from app.services.inference import Completion

PERSONA = "leah-sumner"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    from app import ratelimit
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "test.db")
    dbmod.init_db()
    ratelimit.reset()
    yield
    ratelimit.reset()


@pytest.fixture
def client():
    return TestClient(app)


def _count() -> int:
    with dbmod.get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM decision_log").fetchone()["c"]


def _drafting_dispose(client, *, proposal_text, model, sig, disposition="commit", final_text="my note"):
    return client.post(f"/drafting/{PERSONA}/dispose", data={
        "persona_id": PERSONA, "surface": "drafting", "proposal_type": "case_note",
        "proposal_text": proposal_text, "model": model, "disposition": disposition,
        "final_text": final_text, "proposal_sig": sig,
    })


# --- A08: the governance log rejects forged provenance --------------------------------------

def test_a08_genuine_signed_proposal_is_recorded_with_server_values(client):
    text, model = "AI-generated note exactly as produced.", config.PRIMARY_MODEL
    sig = integrity.sign(integrity.provenance(PERSONA, "drafting", "case_note", model, text))
    r = _drafting_dispose(client, proposal_text=text, model=model, sig=sig)
    assert r.status_code == 200
    assert _count() == 1
    e = decision_log.list_entries(PERSONA)[0]
    assert e.proposal_text == text and e.model == model   # the trusted, signed provenance


def test_a08_forged_proposal_text_is_rejected(client):
    text, model = "AI-generated note.", config.PRIMARY_MODEL
    sig = integrity.sign(integrity.provenance(PERSONA, "drafting", "case_note", model, text))
    # keep the (valid-for-original) signature but tamper the proposal text
    r = _drafting_dispose(client, proposal_text="FORGED proposal the model never wrote", model=model, sig=sig)
    assert r.status_code == 200          # handled gracefully...
    assert _count() == 0                 # ...but nothing entered the append-only log
    assert "couldn't be verified" in r.text.lower()


def test_a08_forged_model_attribution_is_rejected(client):
    """The headline finding: a client must not be able to claim a different — or a CLOSED,
    non-allowlisted — model produced a proposal (undercuts VAL-GOV-002)."""
    text, model = "AI-generated note.", config.PRIMARY_MODEL
    sig = integrity.sign(integrity.provenance(PERSONA, "drafting", "case_note", model, text))
    r = _drafting_dispose(client, proposal_text=text, model="openai/gpt-4o", sig=sig)  # forged closed model
    assert _count() == 0
    assert "couldn't be verified" in r.text.lower()


def test_a08_unsigned_disposition_is_rejected(client):
    r = _drafting_dispose(client, proposal_text="anything", model=config.PRIMARY_MODEL, sig="")
    assert _count() == 0


# --- A02: security response headers --------------------------------------------------------

def test_security_headers_present_on_every_response(client):
    r = client.get("/")
    csp = r.headers.get("content-security-policy", "")
    assert csp.startswith("default-src 'self'")
    assert "script-src 'self'" in csp                 # no off-origin script can be injected
    assert "frame-ancestors 'none'" in csp            # clickjacking the dispose buttons
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("referrer-policy") == "no-referrer"   # persona_id never leaks via Referer
    assert r.headers.get("x-frame-options") == "DENY"


# --- A01: cross-origin write protection (CSRF) ---------------------------------------------

def test_cross_origin_write_is_refused(client):
    r = client.post(
        f"/drafting/{PERSONA}/dispose",
        data={"disposition": "commit"},
        headers={"origin": "http://evil.example"},
    )
    assert r.status_code == 403
    assert _count() == 0                # the malicious cross-site write never reached the log


def test_same_origin_write_is_not_csrf_blocked(client):
    text = "AI note"
    sig = integrity.sign(integrity.provenance(PERSONA, "drafting", "case_note", "", text))
    r = _drafting_dispose(client, proposal_text=text, model="", sig=sig)
    # (TestClient sends no Origin → treated as a non-browser client → allowed)
    assert r.status_code == 200 and _count() == 1
    # an explicit same-origin Origin header is likewise allowed
    r2 = client.post(
        f"/drafting/{PERSONA}/dispose",
        data={"persona_id": PERSONA, "surface": "drafting", "proposal_type": "case_note",
              "proposal_text": text, "model": "", "disposition": "discard", "final_text": "",
              "proposal_sig": sig},
        headers={"origin": "http://testserver"},
    )
    assert r2.status_code != 403


def test_a08_escalation_forgery_is_rejected(client):
    # valid sig for an innocuous text, then forge the escalation proposal text
    sig = integrity.sign(integrity.provenance(PERSONA, "escalation", "risk_flag", "", "real concern"))
    r = client.post(f"/escalation/{PERSONA}/escalate", data={
        "disposition": "escalate", "proposal_text": "FORGED", "model": "", "final_text": "x",
        "proposal_sig": sig,
    })
    assert _count() == 0
    assert "nothing was recorded" in r.text.lower()


# --- A05 / LLM01 / LLM02: prompt-injection fencing + denial-language guard ------------------

def test_denial_phrases_detects_refusal_but_not_warm_text():
    assert safety.denial_phrases("Unfortunately you are not eligible for this funding.")
    assert safety.denial_phrases("Your application was refused.")
    assert not safety.denial_phrases("Great to see you Tuesday — I'll sort out the bus pass.")


def test_untrusted_record_text_is_fenced_in_the_prompt():
    from app.routers.drafting import _persona_context
    ctx = _persona_context(data.get_persona(PERSONA))
    assert "UNTRUSTED_RECORD_DATA" in ctx           # the instruction/data fence is present
    assert "said he is 24" in ctx                   # record text is inside it


def test_denial_guard_flags_an_outbound_draft(client, monkeypatch):
    """If the model is steered into writing a refusal, the worker is warned before sending
    (Invariant 2). The guard flags; it never blocks."""
    class _Denier:
        configured = True
        def complete(self, prompt, *, system=None, **kw):
            return Completion(text="I'm sorry, you are not eligible and your funding is refused.",
                              model=config.PRIMARY_MODEL)
    monkeypatch.setattr("app.routers.drafting.provider", _Denier())
    r = client.post(f"/drafting/{PERSONA}/generate", data={"proposal_type": "follow_up"})
    assert "reads like a refusal" in r.text.lower()


# --- A07: constant-time auth for unknown usernames -----------------------------------------

def test_unknown_username_does_equal_pbkdf2_work(monkeypatch):
    from app import auth
    monkeypatch.setattr(auth, "_users", lambda: {})        # no users → unknown-user path
    calls = []
    real = auth.hash_password
    monkeypatch.setattr(auth, "hash_password", lambda pw, salt: (calls.append(1), real(pw, salt))[1])
    assert auth.verify_credentials("ghost", "pw") is False
    assert calls, "PBKDF2 work must run for unknown users too (timing equalisation)"


def test_auth_failure_is_logged(monkeypatch, caplog):
    import secrets
    from app import auth
    salt = secrets.token_bytes(16)
    monkeypatch.setattr(auth, "_users",
                        lambda: {"u": {"salt": salt.hex(), "hash": auth.hash_password("right", salt)}})
    monkeypatch.setenv("DEMO_AUTH", "1")
    c = TestClient(app)
    with caplog.at_level("WARNING", logger="app.security"):
        c.get("/", auth=("u", "wrong"))
    assert any("failed login" in r.getMessage() for r in caplog.records)


# --- A06 / LLM10: generation rate limiting --------------------------------------------------

def test_rate_limiter_blocks_after_limit():
    from app import ratelimit
    ratelimit.reset()
    assert all(ratelimit.allow("k", limit=3, window=60) for _ in range(3))
    assert not ratelimit.allow("k", limit=3, window=60)   # 4th is blocked
    ratelimit.reset()


def test_generate_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr("app.routers.drafting.ratelimit.allow", lambda *a, **k: False)
    r = client.post(f"/drafting/{PERSONA}/generate", data={"proposal_type": "case_note"})
    assert r.status_code == 429
    assert _count() == 0   # a throttled generation writes nothing
