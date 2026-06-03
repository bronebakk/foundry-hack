"""Read API for the synthetic personas and their fragmented, multi-source records.
FROZEN after M2. Consumed by M3 (context synthesis) and M5 (risk surfacing).

All data here is ENTIRELY FICTIONAL (Invariant 3). Every persona carries ``synthetic: true``.
This module is read-only: it never writes anything.
"""
from __future__ import annotations

import json
from functools import lru_cache

from app.config import PERSONA_DIR
from app.models import Persona


@lru_cache(maxsize=1)
def _load_all() -> dict[str, Persona]:
    personas: dict[str, Persona] = {}
    for path in sorted(PERSONA_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        persona = Persona.from_dict(raw)
        personas[persona.id] = persona
    return personas


def list_personas() -> list[Persona]:
    """All personas as typed objects (templates read .name/.summary_line/.record_count/etc.)."""
    return list(_load_all().values())


def get_persona(persona_id: str) -> Persona | None:
    """Full persona incl. all source records. Returns None if unknown."""
    return _load_all().get(persona_id)
