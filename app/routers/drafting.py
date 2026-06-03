"""DRAFT surface — drafting, authorship & the propose-not-act boundary. OWNED BY MISSION M4.
M1 ships a registered stub so nav + routing work and M4 has somewhere to build."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import render

router = APIRouter(prefix="/drafting", tags=["drafting"])


@router.get("/", response_class=HTMLResponse)
def drafting_home(request: Request):
    return render(
        request,
        "drafting/index.html",
        heading="Drafting",
        milestone="M4",
        blurb="Case-note and follow-up drafting in the worker's own voice. Every output an "
        "editable draft the worker authors and commits — nothing sent or committed automatically.",
    )
