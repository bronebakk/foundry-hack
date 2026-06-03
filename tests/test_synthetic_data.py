"""Tests for the synthetic-data tooling: the validation gate, the generator, and the
governance guarantee that every persona we ship is visibly synthetic and traceable.

The gate is load-bearing for Invariant 3 (synthetic only) and Invariant 7 (no unexplained
risk flag), so it is tested adversarially — bad data must FAIL, good data must PASS.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models import Persona
from scripts.validate_personas import has_errors, validate_persona_dict
from scripts import generate_personas as gen

REPO = Path(__file__).resolve().parent.parent


def _good() -> dict:
    return {
        "id": "gen-test-good-000",
        "name": "Test Good",
        "age": 18,
        "synthetic": True,
        "demo_note": "fictional synthetic test persona",
        "summary_line": "valid persona",
        "records": [
            {"id": "r1", "date": "2026-02-01", "source": "S", "author": "A",
             "type": "note", "text": "A record.", "risk_indicator": False},
        ],
    }


# --- The gate rejects bad data (Invariant 3 + 7) ---

def test_gate_passes_clean_persona():
    assert not has_errors(validate_persona_dict(_good()))


def test_gate_rejects_non_synthetic():
    bad = _good() | {"synthetic": False}
    issues = validate_persona_dict(bad)
    assert has_errors(issues)
    assert any("synthetic" in i.where for i in issues if i.level == "error")


def test_gate_rejects_risk_flag_without_rationale():
    bad = _good()
    bad["records"][0].update(risk_indicator=True, risk_category="Some risk")  # no rationale
    issues = validate_persona_dict(bad)
    assert has_errors(issues)
    assert any("risk_rationale" in i.where for i in issues if i.level == "error")


def test_gate_rejects_duplicate_record_ids():
    bad = _good()
    bad["records"].append(dict(bad["records"][0]))  # same id 'r1'
    assert has_errors(validate_persona_dict(bad))


def test_gate_rejects_unsafe_ids_and_bad_dates():
    bad = _good()
    bad["id"] = "Has Spaces"  # breaks URL path
    bad["records"][0]["id"] = "bad id#"  # breaks href="#anchor"
    bad["records"][0]["date"] = "not-a-date"
    issues = validate_persona_dict(bad)
    wheres = {i.where for i in issues if i.level == "error"}
    assert "id" in wheres and "records[0].id" in wheres and "records[0].date" in wheres


def test_gate_rejects_empty_record_text():
    bad = _good()
    bad["records"][0]["text"] = "   "
    assert has_errors(validate_persona_dict(bad))


# --- Every shipped persona (live + staged hero) passes the gate ---

@pytest.mark.parametrize("folder", ["app/data/personas", "app/data/personas_staged"])
def test_all_curated_personas_pass_the_gate(folder):
    files = sorted((REPO / folder).glob("*.json"))
    assert files, f"no personas found in {folder}"
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        issues = validate_persona_dict(d)
        assert not has_errors(issues), f"{f.name} failed gate: {[str(i) for i in issues if i.level=='error']}"
        # ...and is visibly synthetic (the governance hard line).
        assert d["synthetic"] is True


# --- The generator produces valid, reproducible, model-loadable data ---

def test_generator_output_is_valid_and_loads_via_frozen_model():
    for i in range(12):
        p = gen.make_persona(i, gen.random.Random(42))
        assert not has_errors(validate_persona_dict(p))
        # Loads through the FROZEN data model the whole app reads through.
        persona = Persona.from_dict(p)
        assert persona.synthetic is True
        # Anchor-safety: every record id is usable as an HTML #anchor for CTX source-linking.
        for r in persona.records:
            assert r.id and " " not in r.id


def test_generator_is_deterministic_for_a_seed():
    a = [gen.make_persona(i, gen.random.Random(7)) for i in range(8)]
    b = [gen.make_persona(i, gen.random.Random(7)) for i in range(8)]
    assert a == b  # same seed/index -> identical data (reproducible fixtures)


def test_edge_cases_are_valid_and_cover_the_hard_inputs():
    edges = {e["id"]: e for e in gen.edge_cases()}
    for e in edges.values():
        assert not has_errors(validate_persona_dict(e))
        Persona.from_dict(e)  # must load without error
    # The renderer-stressing cases we care about are present.
    assert "gen-edge-zero-records" in edges
    assert "gen-edge-multi-risk" in edges
    assert any(len(Persona.from_dict(e).records) == 1 for e in edges.values())
    # Multi-risk edge actually carries >1 explained flag.
    mr = Persona.from_dict(edges["gen-edge-multi-risk"])
    flagged = [r for r in mr.records if r.risk_indicator]
    assert len(flagged) >= 2 and all(r.risk_rationale for r in flagged)


def test_committed_fixtures_exist_and_pass_the_gate():
    fixtures = sorted((REPO / "tests/fixtures/personas").glob("*.json"))
    assert len(fixtures) >= 12, "expected a committed deterministic fixture set"
    for f in fixtures:
        assert not has_errors(validate_persona_dict(json.loads(f.read_text(encoding="utf-8"))))


# --- Staged hero personas cover the demo's surface gaps ---

def test_staged_personas_cover_draft_deny_and_risk_variety():
    staged = {f.stem: json.loads(f.read_text(encoding="utf-8"))
              for f in (REPO / "app/data/personas_staged").glob("*.json")}
    # DRAFT: a 'meeting just held' capture to write up.
    assert any(r["type"] == "meeting_capture"
               for p in staged.values() for r in p["records"]), "no DRAFT meeting-capture scenario"
    # ESCALATE variety: a risk category distinct from the existing CSE/CCE example.
    risk_cats = {r.get("risk_category") for p in staged.values() for r in p["records"] if r.get("risk_indicator")}
    assert any("self-harm" in (c or "").lower() for c in risk_cats), "no distinct risk-category persona"
    # DENY: the marcus persona sets up an 'option unavailable, route to human' scenario.
    assert "marcus-fielding" in staged
