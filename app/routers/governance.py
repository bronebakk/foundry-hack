"""GOV surface — the human-facing immutable decision-log viewer. OWNED BY MISSION M6.

This is the procurement-clearing proof made visible (VAL-GOV-003): every AI suggestion a
worker acted on, shown as **AI proposal → human disposition → worker attribution**, in an
append-only log. The viewer is strictly read-only — there is deliberately no edit/delete
path here, mirroring the service (no mutation API) and DB (UPDATE/DELETE triggers) guarantees.

It also makes the open-weight inference posture inspectable in-app (VAL-GOV-002): the
allowlisted model IDs and the single base-URL swap point, read straight from config.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app import config
from app.services import data, decision_log
from app.services.inference import provider
from app.templating import render

router = APIRouter(prefix="/governance", tags=["governance"])

# Human-readable framing for each disposition. Every one is a thing a *person* chose — there is
# no 'auto' disposition by construction (see app/models.py).
DISPOSITION_LABELS = {
    "commit": "committed as their note",
    "discard": "reviewed, then discarded",
    "send": "sent (their action)",
    "escalate": "escalated to a human",
}


@router.get("/", response_class=HTMLResponse)
def governance_home(request: Request, persona_id: str | None = None):
    """The decision log, newest first. Optionally filtered to one young person. Read-only."""
    entries = decision_log.list_entries(persona_id=persona_id)
    rows = []
    for e in entries:
        persona = data.get_persona(e.persona_id) if e.persona_id else None
        rows.append(
            {
                "e": e,
                "persona_name": persona.name if persona else (e.persona_id or "—"),
                "disposition_label": DISPOSITION_LABELS.get(e.disposition, e.disposition),
            }
        )

    # Inference provenance — open-weight only, swap-by-config (VAL-GOV-002), inspectable here.
    inference = {
        "base_url": config.INFERENCE_BASE_URL,
        "configured": provider.configured,
        "allowed_models": sorted(config.ALLOWED_MODELS),
        "primary_model": config.PRIMARY_MODEL,
    }

    return render(
        request,
        "governance/index.html",
        rows=rows,
        total=len(rows),
        personas=data.list_personas(),
        active_persona=persona_id,
        inference=inference,
    )
