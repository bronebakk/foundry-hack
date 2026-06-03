"""GOV surface — the human-facing immutable decision-log viewer. OWNED BY MISSION M6.
M1 ships a registered stub so nav + routing work."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import render

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/", response_class=HTMLResponse)
def governance_home(request: Request):
    return render(
        request,
        "governance/index.html",
        heading="Decision log",
        milestone="M6",
        blurb="Every AI proposal a worker acted on — proposal, human disposition, and author — "
        "in an append-only log that cannot be silently altered.",
    )
