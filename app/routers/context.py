"""CTX surface — pre-meeting context synthesis. OWNED BY MISSION M3.

M1 ships a scaffold: list personas, and show a persona's raw source records with a
placeholder where the AI-synthesised brief (VAL-CTX-001) and its source-tracing
(VAL-CTX-002) will go. No inference yet. M3 fills in the synthesis.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.services import data
from app.templating import render

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/", response_class=HTMLResponse)
def context_home(request: Request):
    return render(request, "context/index.html", personas=data.list_personas())


@router.get("/{persona_id}", response_class=HTMLResponse)
def context_persona(request: Request, persona_id: str):
    persona = data.get_persona(persona_id)
    if persona is None:
        return render(request, "context/not_found.html", persona_id=persona_id)
    return render(request, "context/persona.html", persona=persona)
