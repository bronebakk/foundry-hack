"""M3 — CTX: pre-meeting context synthesis.

The load-bearing guarantee here is EXPLAINABILITY (VAL-CTX-002 / Invariant 7): every
statement the worker sees must trace to a real source record. So the tests focus on the
attribution guard (no dangling/unattributable line survives), the route contract, and
graceful degradation when inference is unavailable (no 500).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import data
from app.services.inference import Completion
from app.routers import context as ctx

client = TestClient(app)

PERSONA_ID = "leah-sumner"  # 3 records: leah-r1, leah-r2 (risk), leah-r3


def _persona():
    return data.get_persona(PERSONA_ID)


# --- The explainability guard: no statement without a real source survives ---

def test_attributable_statements_keeps_only_real_sourced_lines():
    persona = _persona()
    items = [
        {"statement": "Attendance has dropped sharply.", "source_record_ids": ["leah-r1"]},
        {"statement": "Cites two real records.", "source_record_ids": ["leah-r1", "leah-r3"]},
        {"statement": "Dangling — no such record.", "source_record_ids": ["leah-r999"]},
        {"statement": "Unattributed — empty sources.", "source_record_ids": []},
        {"statement": "", "source_record_ids": ["leah-r1"]},  # empty text dropped
    ]
    out = ctx.attributable_statements(persona, items)
    # Only the two genuinely-attributed, non-empty statements survive.
    assert [s.text for s in out] == [
        "Attendance has dropped sharply.",
        "Cites two real records.",
    ]
    # Every surviving statement carries at least one real record, and all are real ids.
    for s in out:
        assert s.sources
        for src in s.sources:
            assert persona.get_record(src.id) is not None


def test_attributable_statements_drops_dangling_ids_but_keeps_valid_ones():
    persona = _persona()
    out = ctx.attributable_statements(
        persona,
        [{"statement": "Mixed ids.", "source_record_ids": ["leah-r2", "ghost", "leah-r2"]}],
    )
    assert len(out) == 1
    assert [src.id for src in out[0].sources] == ["leah-r2"]  # dangling + dup dropped


def test_attributable_statements_accepts_singular_id_field():
    persona = _persona()
    out = ctx.attributable_statements(
        persona, [{"statement": "Singular form.", "source_record_id": "leah-r1"}]
    )
    assert len(out) == 1 and out[0].sources[0].id == "leah-r1"


def test_parse_brief_json_tolerates_fences_and_prose():
    raw = 'Here is the brief:\n```json\n[{"statement": "x", "source_record_ids": ["leah-r1"]}]\n```\nThanks!'
    parsed = ctx.parse_brief_json(raw)
    assert parsed == [{"statement": "x", "source_record_ids": ["leah-r1"]}]
    assert ctx.parse_brief_json("not json at all") == []
    assert ctx.parse_brief_json("") == []


# --- Rendered surface: every brief line links to an existing record anchor ---

class _FakeProvider:
    """Stands in for the open-weight provider so we can exercise the 'ok' render path
    deterministically, without a network call."""

    configured = True

    def __init__(self, text: str):
        self._text = text

    def complete(self, prompt, **kwargs):
        return Completion(text=self._text, model="openai/gpt-oss-120b")


def test_route_renders_each_statement_with_a_link_to_a_real_record(monkeypatch):
    brief_json = (
        '[{"statement": "Attendance is down to 41%.", "source_record_ids": ["leah-r1"]},'
        ' {"statement": "Possible exploitation indicators noted.", "source_record_ids": ["leah-r2"]}]'
    )
    monkeypatch.setattr(ctx, "provider", _FakeProvider(brief_json))
    r = client.get(f"/context/{PERSONA_ID}")
    assert r.status_code == 200
    # Both synthesised statements are present...
    assert "Attendance is down to 41%." in r.text
    assert "Possible exploitation indicators noted." in r.text
    # ...and each carries an anchor link to a record that actually exists on the page.
    persona = _persona()
    for rid in ("leah-r1", "leah-r2"):
        assert f'href="#{rid}"' in r.text          # the source link
        assert f'id="{rid}"' in r.text             # ...and the record it points to
        assert persona.get_record(rid) is not None
    # No dangling anchors: every href="#..." brief link resolves to a rendered record id.
    import re
    linked = set(re.findall(r'href="#(leah-[\w-]+)"', r.text))
    for rid in linked:
        assert f'id="{rid}"' in r.text, f"brief links to #{rid} but no such record is rendered"


def test_route_200_with_synthetic_marker_and_source_records(monkeypatch):
    # Degraded (no key) is fine for this contract check — records must still show.
    monkeypatch.setattr(ctx.provider, "_api_key", "", raising=False)
    r = client.get(f"/context/{PERSONA_ID}")
    assert r.status_code == 200
    assert "synthetic" in r.text                    # synthetic marker (VAL-GOV-001)
    assert "Attendance down to 41%" in r.text       # a verbatim source record passage
    assert "Source records (3)" in r.text


# --- Graceful degradation: inference unavailable never 500s ---

def test_unconfigured_inference_degrades_without_500(monkeypatch):
    monkeypatch.setattr(ctx.provider, "_api_key", "", raising=False)
    r = client.get(f"/context/{PERSONA_ID}")
    assert r.status_code == 200
    assert "OPENROUTER_API_KEY" in r.text           # the clear "set the key" notice
    # Raw records still render so the surface is demoable offline.
    assert "Attendance down to 41%" in r.text


def test_inference_error_degrades_without_500(monkeypatch):
    from app.services.inference import InferenceError

    class _BoomProvider:
        configured = True

        def complete(self, *a, **k):
            raise InferenceError("backend down")

    monkeypatch.setattr(ctx, "provider", _BoomProvider())
    r = client.get(f"/context/{PERSONA_ID}")
    assert r.status_code == 200
    assert "Inference unavailable" in r.text
    assert "Attendance down to 41%" in r.text        # records still rendered


def test_brief_is_framed_as_a_proposal_not_a_record(monkeypatch):
    monkeypatch.setattr(
        ctx,
        "provider",
        _FakeProvider('[{"statement": "x.", "source_record_ids": ["leah-r1"]}]'),
    )
    r = client.get(f"/context/{PERSONA_ID}")
    assert "AI proposal" in r.text                   # visibly an AI draft, not settled fact
    assert "not a record of truth" in r.text


def test_unknown_persona_is_not_found_not_500():
    r = client.get("/context/does-not-exist")
    assert r.status_code == 200  # rendered not_found template, not an error
    assert "does-not-exist" in r.text
