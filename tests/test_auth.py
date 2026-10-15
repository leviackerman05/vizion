import time

from conftest import register
from sqlalchemy import select
from vizion.db import LoginSession, User, transaction
from vizion.settings import settings


def test_session_persists_and_logout_revokes_it(client):
    result = register(client)
    token = client.cookies.get(settings.cookie_name)
    assert token and result["recovery_code"]
    assert client.get("/api/auth/me").json()["user"]["email"] == "teacher@example.com"
    with transaction() as db:
        assert token != db.scalar(select(LoginSession)).token_hash
        assert not db.scalar(select(User)).password_hash.startswith("a-long")
    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.set(settings.cookie_name, token)
    assert client.get("/api/auth/me").status_code == 401


def test_login_handles_normalized_email_and_wrong_password(client):
    register(client)
    client.post("/api/auth/logout")
    bad = client.post("/api/auth/login", json={"email": "teacher@example.com", "password": "wrong-password"})
    assert bad.status_code == 401
    result = client.post(
        "/api/auth/login", json={"email": "TEACHER@example.com", "password": "a-long-test-password"}
    )
    assert result.status_code == 200
    assert client.get("/api/auth/me").status_code == 200
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=lax" in result.headers["set-cookie"]


def test_expired_session_is_rejected_and_active_session_renews(client):
    register(client)
    with transaction() as db:
        session = db.scalar(select(LoginSession))
        session.expires_at = time.time() + 60
    result = client.get("/api/auth/me")
    assert result.status_code == 200 and "set-cookie" in result.headers
    with transaction() as db:
        session = db.scalar(select(LoginSession))
        assert session.expires_at > time.time() + 29 * 86400
        session.expires_at = time.time() - 1
    assert client.get("/api/auth/me").status_code == 401


def test_recovery_revokes_sessions_and_rotates_recovery_code(client):
    result = register(client)
    old_token = client.cookies.get(settings.cookie_name)
    recovered = client.post(
        "/api/auth/recover",
        json={
            "email": "teacher@example.com",
            "password": "a-new-test-password",
            "recovery_code": result["recovery_code"],
        },
    )
    assert recovered.status_code == 200
    assert recovered.json()["recovery_code"] != result["recovery_code"]
    client.cookies.set(settings.cookie_name, old_token)
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/recover",
            json={
                "email": "teacher@example.com",
                "password": "another-password",
                "recovery_code": result["recovery_code"],
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={"email": "teacher@example.com", "password": "a-new-test-password"}
        ).status_code
        == 200
    )


def test_cross_site_and_missing_verification_header_are_rejected(client):
    credentials = {"email": "teacher@example.com", "password": "a-long-test-password"}
    assert (
        client.post(
            "/api/auth/register", json=credentials, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post("/api/auth/register", json=credentials, headers={"X-Vizion-Client": ""}).status_code
        == 403
    )


def test_login_is_rate_limited(client):
    for _ in range(12):
        assert (
            client.post(
                "/api/auth/login", json={"email": "nobody@example.com", "password": "bad-password"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login", json={"email": "nobody@example.com", "password": "bad-password"}
        ).status_code
        == 429
    )


def test_production_cookie_cannot_be_read_by_scripts_or_sent_over_http(client, monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    response = client.post(
        "/api/auth/register", json={"email": "production@example.com", "password": "a-long-test-password"}
    )
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("__Host-vizion_session=")
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    assert "Domain=" not in cookie
    assert client.get("/api/auth/me").status_code == 401  # HTTP client cannot send the Secure cookie.
