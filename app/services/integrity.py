"""Tamper-evident signing for AI-proposal provenance — security hardening for A08.

The decision log's credibility (VAL-GOV-002 / VAL-GOV-003) rests on two fields being *exactly
what the server generated*, not what the browser later POSTs back: the AI ``proposal_text``
("the AI proposal exactly as generated") and the ``model`` attribution (open-weight provenance).

Before this control, ``/dispose`` / ``/escalate`` / ``/refer`` rebuilt those fields from form
input, so a client could forge the recorded AI proposal or claim a different — even a closed,
non-allowlisted — model produced it. That quietly breaks the exact assertions the governance
viewer exists to prove.

Fix: at generation the server signs the provenance-critical fields with an HMAC; at disposition
it re-verifies the signature against the posted fields. A client cannot alter ``proposal_text``
or ``model`` without invalidating the signature (it has no key), so a tampered disposition is
rejected and never reaches the append-only log. The human still supplies only ``final_text`` and
the chosen disposition; the author of record stays server-side (D-004).

Stateless by design (no per-request server storage, no GET side effects). Multi-worker-safe when
``PROPOSAL_SIGNING_KEY`` is set; otherwise a per-process random key is used (fine for the
single-worker demo — a server restart simply invalidates in-flight drafts, which fail closed).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

# Provenance-critical fields, in a fixed order. ``final_text`` is deliberately NOT signed — it is
# the human's editable words and is legitimately client-supplied.
_SIGNED_FIELDS = ("persona_id", "surface", "proposal_type", "model", "proposal_text")

_KEY = (os.environ.get("PROPOSAL_SIGNING_KEY") or secrets.token_hex(32)).encode("utf-8")


def provenance(persona_id, surface, proposal_type, model, proposal_text) -> dict:
    """Build the signed-field dict from a proposal's parts. ``model``/``proposal_text`` may be
    empty. Used identically at signing (generation) and verification (disposition)."""
    return {
        "persona_id": persona_id or "",
        "surface": surface or "",
        "proposal_type": proposal_type or "",
        "model": model or "",
        "proposal_text": proposal_text or "",
    }


def _canonical(values: dict) -> bytes:
    """Length-prefixed join so no combination of field values can be made to collide by shifting
    a delimiter (e.g. a value containing '|')."""
    parts = []
    for field in _SIGNED_FIELDS:
        v = values.get(field) or ""
        parts.append(f"{len(v)}:{v}")
    return "\x1f".join(parts).encode("utf-8")


def sign(values: dict) -> str:
    """HMAC-SHA256 over the provenance fields. ``values`` keys are the strings as they appear in
    the form (``model``/``proposal_text`` may be empty)."""
    return hmac.new(_KEY, _canonical(values), hashlib.sha256).hexdigest()


def verify(values: dict, signature: str | None) -> bool:
    """Constant-time check that ``signature`` was produced by ``sign(values)`` with our key."""
    if not signature:
        return False
    return hmac.compare_digest(sign(values), signature)
