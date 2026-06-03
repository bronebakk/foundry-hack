"""FastAPI app entrypoint. Frozen after M1 for the parallel streams; the M6 integration
step (the sanctioned place for frozen-file edits) added the import-time ``init_db()`` below.

Registers all routers. Once the streams landed, several surfaces read the decision log in
GET handlers (escalation overview/inbox, the M6 governance viewer). The append-only table
must therefore exist before any request — not only after the ASGI ``lifespan`` startup, which
e.g. a module-level ``TestClient(app)`` never triggers. See decisions.md D-005."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.auth import require_user
from app.db import init_db
from app.services import data
from app.services.inference import provider
from app.routers import context, drafting, escalation, governance
from app.templating import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # idempotent: creates the append-only decision_log + triggers
    yield


# Defence in depth: the decision_log table must exist before the first request, since GET
# handlers now read it. init_db() is idempotent (CREATE TABLE IF NOT EXISTS), so calling it
# here as well as in lifespan is safe; per-test temp DBs re-init their own via fixtures.
init_db()

# Global demo-access gate (HTTP Basic). No-op unless DEMO_AUTH is enabled in the environment,
# so tests and local runs are unaffected; the public demo deployment sets DEMO_AUTH=1. See app/auth.py.
app = FastAPI(
    title="Keyworker Force-Multiplier",
    lifespan=lifespan,
    dependencies=[Depends(require_user)],
)
app.mount("/static", StaticFiles(directory=str(config.APP_DIR / "static")), name="static")

# All stream routers registered here in M1 — pre-wired stubs for M3/M4/M5/M6.
app.include_router(context.router)
app.include_router(drafting.router)
app.include_router(escalation.router)
app.include_router(governance.router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "index.html", personas=data.list_personas())


@app.get("/healthz")
def healthz():
    """Liveness + inference configuration status (does NOT make a model call)."""
    return JSONResponse(
        {
            "status": "ok",
            "inference_base_url": config.INFERENCE_BASE_URL,
            "inference_configured": provider.configured,
            "allowed_models": sorted(config.ALLOWED_MODELS),
            "personas": len(data.list_personas()),
        }
    )
