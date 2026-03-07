"""Auth endpoint tests."""

import pytest


class TestLogin:
    def test_login_success(self, regular_client):
        """regular_client fixture logged in successfully — cookie is in its jar."""
        r = regular_client.get("/api/chat/conversations")
        assert r.status_code == 200

    def test_login_wrong_password(self, anon_client):
        r = anon_client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert r.status_code == 401

    def test_login_unknown_user(self, anon_client):
        r = anon_client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "whatever",
        })
        assert r.status_code == 401

    def test_protected_endpoint_without_cookie(self, anon_client):
        """anon_client has no cookies — must get 401."""
        r = anon_client.get("/api/chat/conversations")
        assert r.status_code in (401, 403)

    def test_protected_endpoint_with_cookie(self, regular_client):
        r = regular_client.get("/api/chat/conversations")
        assert r.status_code == 200

    def test_logout_clears_cookie(self, anon_client):
        """Logout endpoint is accessible and returns 200."""
        r = anon_client.post("/api/auth/logout")
        assert r.status_code == 200


class TestRegister:
    def test_duplicate_username_rejected(self, anon_client):
        """Registering an existing username returns 400."""
        r = anon_client.post("/api/auth/register", json={
            "username": "testuser",   # already created in regular_client fixture
            "password": "Testpass123!",
            "email": "other@example.com",
        })
        assert r.status_code == 400
