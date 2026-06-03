"""ESCALATE surface — risk surfacing, human-owned escalation, no 'computer says no'.
OWNED BY MISSION M5. M1 ships a registered stub so nav + routing work."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import render

router = APIRouter(prefix="/escalation", tags=["escalation"])


@router.get("/", response_class=HTMLResponse)
def escalation_home(request: Request):
    return render(
        request,
        "escalation/index.html",
        heading="Safeguarding",
        milestone="M5",
        blurb="Risk indicators are surfaced to the worker and never acted on automatically. "
        "Escalation is human-initiated and routes to a human-owned surface.",
    )
