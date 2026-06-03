"""M2 — the propose → log → dispose spine. Test-first on the load-bearing boundary:
nothing is committed or sent on generation; the only write is an explicit human
disposition; the log cannot be mutated; and the inference layer has no persistence path
at all (the automated form of VAL-PROPOSE-001's supplementary code check).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app import db as dbmod
from app.models import Proposal, Surface, ProposalType, Disposition
from app.services import decision_log


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Isolated DB per test so we never touch the real foundry.db."""
    monkeypatch.setattr(dbmod, "DB_PATH", tmp_path / "test.db")
    dbmod.init_db()
    yield


def _proposal(text="Drafted note v1", persona="amara-okafor", ptype=ProposalType.CASE_NOTE):
    return Proposal(
        persona_id=persona,
        surface=Surface.DRAFTING,
        proposal_type=ptype,
        proposal_text=text,
        model="openai/gpt-oss-120b",
    )


def _count() -> int:
    with dbmod.get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM decision_log").fetchone()["c"]


# --- The boundary: generation persists nothing ---

def test_constructing_a_proposal_persists_nothing():
    before = _count()
    _ = _proposal()  # the AI "proposed" — built an in-memory Proposal
    assert _count() == before == 0  # ...and nothing was written


def test_inference_layer_has_no_persistence_path():
    """VAL-PROPOSE-001 supplementary code check, automated: the module that generates
    text must contain no *code path* that writes to the record/log. We parse the AST
    (so docstring mentions don't count) and assert it imports no persistence module and
    contains no write-SQL string literal."""
    import ast
    import app.services.inference as inf

    tree = ast.parse(Path(inf.__file__).read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(n.name for n in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            imported.add(base)
            imported.update(f"{base}.{n.name}" for n in node.names)
    forbidden_imports = {"sqlite3", "app.db", "app.services.decision_log"}
    leaked = imported & forbidden_imports
    assert not leaked, f"inference.py imports a persistence path: {leaked}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            upper = node.value.upper()
            assert not any(
                f"{verb} " in upper for verb in ("INSERT", "UPDATE", "DELETE")
            ), "inference.py contains write-SQL — it must only generate text"


# --- The only write is an explicit human disposition ---

def test_commit_appends_entry_attributed_to_the_worker():
    p = _proposal()
    entry = decision_log.record(
        p, Disposition.COMMIT, author="Sam Ellison (keyworker)", final_text="Worker-edited note"
    )
    assert _count() == 1
    assert entry.author == "Sam Ellison (keyworker)"  # never the AI (Invariant 5)
    assert entry.disposition == "commit"
    assert entry.final_text == "Worker-edited note"
    assert entry.proposal_text == "Drafted note v1"  # original AI proposal preserved verbatim
    assert entry.model == "openai/gpt-oss-120b"


def test_discard_is_logged_but_keeps_no_committed_text():
    entry = decision_log.record(_proposal(), Disposition.DISCARD, author="Sam Ellison (keyworker)")
    assert entry.disposition == "discard"
    assert entry.final_text is None
    assert _count() == 1


# --- The log cannot be altered ---

def test_decision_log_service_exposes_no_mutation_api():
    for forbidden in ("update", "delete", "edit", "remove", "alter"):
        assert not hasattr(decision_log, forbidden), (
            f"decision_log must be append-only; found a {forbidden!r} function"
        )


def test_decision_log_db_blocks_update_and_delete():
    entry = decision_log.record(_proposal(), Disposition.COMMIT, "Sam", final_text="x")
    with pytest.raises(sqlite3.IntegrityError):
        with dbmod.get_conn() as conn:
            conn.execute("UPDATE decision_log SET author='tamper' WHERE id=?", (entry.id,))
    with pytest.raises(sqlite3.IntegrityError):
        with dbmod.get_conn() as conn:
            conn.execute("DELETE FROM decision_log WHERE id=?", (entry.id,))


# --- Read API for the M6 viewer ---

def test_list_entries_newest_first_and_filterable_by_persona():
    decision_log.record(_proposal(text="a", persona="amara-okafor"), Disposition.DISCARD, "Sam")
    decision_log.record(
        _proposal(text="b", persona="kofi-mensah", ptype=ProposalType.FOLLOW_UP),
        Disposition.COMMIT, "Sam", final_text="b-final",
    )
    everything = decision_log.list_entries()
    assert [e.id for e in everything] == sorted((e.id for e in everything), reverse=True)
    amara_only = decision_log.list_entries(persona_id="amara-okafor")
    assert amara_only and all(e.persona_id == "amara-okafor" for e in amara_only)
