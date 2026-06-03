"""HTTP security middleware — response headers + cross-origin write protection (A01/A02).

Two controls, both stateless and proportionate to the demo:

* **Security response headers** on every response — a strict Content-Security-Policy (scripts
  and styles same-origin; everything self-hosted, so no CDN is allowed to inject script into a
  page that renders special-category data and hosts the disposition controls), plus
  ``frame-ancestors 'none'`` / ``X-Frame-Options`` (clickjacking the Commit/Escalate buttons),
  ``nosniff``, ``Referrer-Policy: no-referrer`` (so a ``persona_id`` in the URL never leaks via
  ``Referer``), and HSTS for TLS deployments.

* **Cross-origin write protection (CSRF)** — with HTTP Basic enabled, a browser attaches the
  worker's credentials to cross-site requests automatically, so a malicious page could drive a
  write to the append-only log (a commit/escalate/send) *without the human intending it* — a
  breach of Invariant 1 achieved without the human disposing. We reject state-changing requests
  (POST/PUT/PATCH/DELETE) whose ``Origin``/``Referer`` is present and not same-origin. Requests
  with neither header (non-browser clients: curl, tests, health checks) are allowed — browsers
  always send ``Origin`` on cross-origin writes, so this is not a bypass.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import PlainTextResponse

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)

_SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    # Harmless over plain HTTP (browsers ignore it); active once the demo is behind TLS.
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_same_origin(request: Request) -> bool:
    host = request.headers.get("host", "")
    for header in ("origin", "referer"):
        value = request.headers.get(header)
        if value:  # the first present header is authoritative (Origin preferred)
            return urlsplit(value).netloc == host
    return True  # neither header → not a browser cross-site write → allow


async def security_middleware(request: Request, call_next):
    if request.method in _UNSAFE_METHODS and not _is_same_origin(request):
        return PlainTextResponse(
            "Cross-origin write refused (CSRF protection).", status_code=403
        )
    response = await call_next(request)
    for key, value in _SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    return response
