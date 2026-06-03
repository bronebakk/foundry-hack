"""Read API for the synthetic personas and their fragmented, multi-source records.

M1 provides this minimal loader so the shell can list personas and the validator can see
the synthetic markers (VAL-GOV-001). M2 formalises the typed models over it and freezes
the interface; M3 (context) consumes it to synthesise the pre-meeting brief.

All data here is ENTIRELY FICTIONAL (Invariant 3). Every persona carries ``synthetic: true``.
"""
from __future__ import annotations

import json
from functools import lru_cache

from app.config import PERSONA_DIR


@lru_cache(maxsize=1)
def _load_all() -> dict[str, dict]:
    personas: dict[str, dict] = {}
    for path in sorted(PERSONA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        personas[data["id"]] = data
    return personas


def list_personas() -> list[dict]:
    """Lightweight summaries for the persona list (no record bodies)."""
    out = []
    for p in _load_all().values():
        out.append(
            {
                "id": p["id"],
                "name": p["name"],
                "age": p.get("age"),
                "synthetic": p.get("synthetic", False),
                "summary_line": p.get("summary_line", ""),
                "record_count": len(p.get("records", [])),
                "has_risk_indicator": any(r.get("risk_indicator") for r in p.get("records", [])),
            }
        )
    return out


def get_persona(persona_id: str) -> dict | None:
    """Full persona incl. all source records. Returns None if unknown."""
    return _load_all().get(persona_id)
