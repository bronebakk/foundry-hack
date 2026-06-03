"""FastAPI app entrypoint. Frozen after M1: registers all routers (including the M3–M5
stream stubs) so parallel streams fill in their own files and never edit this one."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.db import init_db
from app.services import data
from app.services.inference import provider
from app.routers import context, drafting, escalation, governance
from app.templating import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # idempotent: creates the append-only decision_log + triggers
    yield


app = FastAPI(title="Keyworker Force-Multiplier", lifespan=lifespan)
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
