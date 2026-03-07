"""
FastAPI integration test fixtures — isolated SQLite DB, one client per role.

Why separate clients?
  Starlette TestClient is a requests.Session — it accumulates Set-Cookie headers
  from every response. Per-request cookies= is deprecated and unreliable for
  overriding the jar. Using one client per role keeps cookies clean and explicit.
"""

import pytest
from fastapi.testclient import TestClient


# ── Shared app (single temp DB for whole session) ─────────────────────────────

@pytest.fixture(scope="session")
def api_app(tmp_path_factory):
    """FastAPI app backed by an isolated temp SQLite database."""
    db_dir = tmp_path_factory.mktemp("api_test_db")

    import database
    database.DB_PATH = db_dir / "test.db"
    database.DB_DIR = db_dir
    database.init_database()

    from api.main import create_app
    return create_app()


def _make_client(api_app):
    return TestClient(api_app, raise_server_exceptions=True)


# ── Role-specific clients ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def anon_client(api_app):
    """Fresh client with NO auth cookies — for testing unauthenticated access."""
    with _make_client(api_app) as c:
        yield c


@pytest.fixture(scope="session")
def regular_client(api_app, superadmin_client):
    """Client logged in as a regular (non-admin) user with no credits.

    Depends on superadmin_client so superadmin is always the FIRST user
    registered — auth_service.py auto-grants admin to the first user,
    so testuser (second) stays a plain user.
    """
    with _make_client(api_app) as c:
        c.post("/api/auth/register", json={
            "username": "testuser",
            "password": "Testpass123!",
            "email": "testuser@example.com",
        })
        r = c.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Testpass123!",
        })
        assert r.status_code == 200, f"Regular login failed: {r.text}"
        yield c


@pytest.fixture(scope="session")
def superadmin_client(api_app):
    """Client logged in as superadmin."""
    with _make_client(api_app) as c:
        c.post("/api/auth/register", json={
            "username": "superadmin",
            "password": "Adminpass123!",
            "email": "superadmin@example.com",
        })
        import database
        with database.get_db_connection() as conn:
            conn.execute(
                "UPDATE users SET is_admin=1, is_superadmin=1 WHERE username='superadmin'"
            )
        r = c.post("/api/auth/login", json={
            "username": "superadmin",
            "password": "Adminpass123!",
        })
        assert r.status_code == 200, f"Superadmin login failed: {r.text}"
        yield c


@pytest.fixture(scope="session")
def funded_client(api_app, superadmin_client):
    """Client logged in as testuser WITH 500 credits pre-loaded."""
    import database

    # Ensure testuser exists
    with _make_client(api_app) as setup:
        setup.post("/api/auth/register", json={
            "username": "testuser",
            "password": "Testpass123!",
            "email": "testuser@example.com",
        })

    # Get user_id and grant credits directly via service (avoids HTTP auth dance)
    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='testuser'"
        ).fetchone()
    user_id = row["user_id"]

    from api.services.credit_service import grant_credits
    grant_credits(user_id, 500, "Test grant", granted_by="system")

    with _make_client(api_app) as c:
        r = c.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Testpass123!",
        })
        assert r.status_code == 200, f"Funded user login failed: {r.text}"
        yield c


# ── Convenience ID helpers ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def regular_user_id():
    import database
    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='testuser'"
        ).fetchone()
    return row["user_id"]


@pytest.fixture(scope="session")
def superadmin_user_id():
    import database
    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='superadmin'"
        ).fetchone()
    return row["user_id"]
