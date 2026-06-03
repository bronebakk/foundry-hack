"""Shared Jinja2 templates instance + render helper. Frozen shared resource (M1):
streams render through this so the synthetic-data banner and worker-of-record are
injected consistently everywhere."""
from __future__ import annotations

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import APP_DIR, DEMO_WORKER

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def render(request: Request, name: str, **ctx):
    ctx.setdefault("worker", DEMO_WORKER)
    return templates.TemplateResponse(request, name, ctx)
