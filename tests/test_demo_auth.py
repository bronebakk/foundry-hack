"""Demo-access gate (HTTP Basic). Off by default so the rest of the suite is unaffected;
when DEMO_AUTH is enabled, every surface requires valid credentials except liveness/static.

These tests write a temporary credentials file and point app.auth at it, so no real password
or the real demo_auth.json is involved.
"""
from __future__ import annotations

import json
import secrets

import pytest
from fastapi.testclient import TestClient

from app import auth
from app.main import app

USER, PW = "demo.user", "Correct-Horse-1!"


@pytest.fixture
def auth_on(tmp_path, monkeypatch):
    salt = secrets.token_bytes(16)
    creds = {USER: {"salt": salt.hex(), "hash": auth.hash_password(PW, salt)}}
    f = tmp_path / "demo_auth.json"
    f.write_text(json.dumps(creds), encoding="utf-8")
    monkeypatch.setattr(auth, "AUTH_FILE", f)
    auth._users.cache_clear()
    monkeypatch.setenv("DEMO_AUTH", "1")
    yield
    auth._users.cache_clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_auth_off_by_default_no_credentials_needed(client):
    # No DEMO_AUTH in env → the gate is a no-op (this is what keeps the rest of the suite green).
    assert client.get("/").status_code == 200


def test_protected_when_enabled_without_credentials(auth_on, client):
    r = client.get("/")
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate", "").startswith("Basic")


def test_valid_credentials_pass(auth_on, client):
    assert client.get("/", auth=(USER, PW)).status_code == 200
    assert client.get("/governance/", auth=(USER, PW)).status_code == 200


def test_wrong_password_rejected(auth_on, client):
    assert client.get("/", auth=(USER, "wrong")).status_code == 401


def test_unknown_user_rejected(auth_on, client):
    assert client.get("/", auth=("nobody", PW)).status_code == 401


def test_healthz_is_exempt(auth_on, client):
    # Liveness must stay reachable without credentials even when the gate is on.
    assert client.get("/healthz").status_code == 200


def test_static_is_exempt(auth_on, client):
    # Static assets stay reachable so the browser's auth-challenge page can still style itself.
    assert client.get("/static/base.css").status_code == 200


def test_fails_closed_when_enabled_but_no_user_file(monkeypatch, tmp_path, client):
    """If DEMO_AUTH is on but the credentials file is missing/unreadable, reject everything."""
    monkeypatch.setenv("DEMO_AUTH", "1")
    monkeypatch.setattr(auth, "AUTH_FILE", tmp_path / "nope.json")
    auth._users.cache_clear()
    assert client.get("/", auth=("anyone", "anything")).status_code == 401
    auth._users.cache_clear()


def test_constant_time_verify_helper(auth_on):
    assert auth.verify_credentials(USER, PW) is True
    assert auth.verify_credentials(USER, "nope") is False
    assert auth.verify_credentials("ghost", PW) is False
