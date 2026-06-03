"""Demo-access gate — HTTP Basic auth in front of the whole app.

NOT a production identity system (the product has no auth in scope — see missions.md). This
exists only to password-protect the *public demo deployment* so it isn't open to the world.
The app still handles synthetic data only (Invariant 3), so this is access control for the
demo, not protection of real personal data.

Credentials are loaded from a gitignored ``demo_auth.json`` storing PBKDF2-SHA256 hashes (never
plaintext, never committed). Verification is constant-time. Fails closed: if the file is missing
or unreadable, every protected request is rejected.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
from functools import lru_cache

from fastapi import Request, HTTPException, status

from app.config import APP_DIR

AUTH_FILE = APP_DIR.parent / "demo_auth.json"
_PBKDF2_ROUNDS = 200_000
_REALM = "Keyworker Force-Multiplier demo"  # ASCII only — goes in a latin-1 HTTP header
_DUMMY_SALT = b"\x00" * 16  # constant salt for unknown-user timing equalisation (A07)

# Structured security event log, distinct from the governance decision log (A09). Records auth
# outcomes for alerting; never logs the password or special-category content.
_seclog = logging.getLogger("app.security")

# Paths that stay open (liveness probe + static assets so CSS loads on the login challenge page).
_EXEMPT_PREFIXES = ("/static",)
_EXEMPT_EXACT = {"/healthz"}


def auth_enabled() -> bool:
    """Off by default (so tests/dev and the local demo run unchanged); enabled explicitly for
    the public deployment via ``DEMO_AUTH=1``. Checked per-request so the launch env controls it."""
    return os.environ.get("DEMO_AUTH", "").strip().lower() in ("1", "true", "yes", "on")


def hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS).hex()


@lru_cache(maxsize=1)
def _users() -> dict[str, dict[str, str]]:
    """{username: {"salt": hex, "hash": hex}}. Empty dict if the file is absent (fail closed)."""
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def verify_credentials(username: str, password: str) -> bool:
    rec = _users().get(username)
    if not rec:
        # Equalise timing (A07): do the same PBKDF2 work for an unknown username as for a known
        # one, so a valid username is not measurably faster (username enumeration via timing).
        hash_password(password, _DUMMY_SALT)
        return False
    try:
        salt = bytes.fromhex(rec["salt"])
        expected = rec["hash"]
    except (KeyError, ValueError):
        return False
    candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, expected)


def _challenge() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": f'Basic realm="{_REALM}"'},
    )


async def require_user(request: Request) -> None:
    """Global dependency: enforce HTTP Basic on every route except the exempt liveness/static paths.
    No-op unless ``DEMO_AUTH`` is enabled, so the test suite and local runs are unaffected."""
    if not auth_enabled():
        return
    path = request.url.path
    if path in _EXEMPT_EXACT or path.startswith(_EXEMPT_PREFIXES):
        return

    client = request.client.host if request.client else "?"
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        _seclog.warning("auth: missing credentials for %s from %s", path, client)
        raise _challenge()
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        _seclog.warning("auth: malformed Basic header from %s", client)
        raise _challenge()
    username, sep, password = decoded.partition(":")
    if not sep or not verify_credentials(username, password):
        # Log the attempted username (never the password) for alerting on brute-force.
        _seclog.warning("auth: failed login for username=%r from %s", username, client)
        raise _challenge()
