"""Credit system endpoint tests."""

import pytest


class TestCreditBalance:
    def test_balance_readable_when_authed(self, regular_client):
        r = regular_client.get("/api/credits/balance")
        assert r.status_code == 200
        assert r.json()["balance"] >= 0

    def test_balance_requires_auth(self, anon_client):
        r = anon_client.get("/api/credits/balance")
        assert r.status_code in (401, 403)


class TestGrantCredits:
    def test_superadmin_can_grant(self, superadmin_client, regular_user_id):
        r = superadmin_client.post(
            "/api/admin/credits/assign",
            json={"user_id": regular_user_id, "amount": 100, "description": "Test"},
        )
        assert r.status_code == 200

    def test_regular_user_cannot_grant(self, regular_client, regular_user_id):
        r = regular_client.post(
            "/api/admin/credits/assign",
            json={"user_id": regular_user_id, "amount": 100, "description": "Test"},
        )
        assert r.status_code in (401, 403)

    def test_zero_amount_rejected(self, superadmin_client, regular_user_id):
        r = superadmin_client.post(
            "/api/admin/credits/assign",
            json={"user_id": regular_user_id, "amount": 0, "description": "Test"},
        )
        assert r.status_code == 422

    def test_negative_amount_rejected(self, superadmin_client, regular_user_id):
        r = superadmin_client.post(
            "/api/admin/credits/assign",
            json={"user_id": regular_user_id, "amount": -50, "description": "Test"},
        )
        assert r.status_code == 422

    def test_balance_increases_after_grant(self, regular_client, superadmin_client, regular_user_id):
        before = regular_client.get("/api/credits/balance").json()["balance"]
        superadmin_client.post(
            "/api/admin/credits/assign",
            json={"user_id": regular_user_id, "amount": 250, "description": "Test top-up"},
        )
        after = regular_client.get("/api/credits/balance").json()["balance"]
        assert after == before + 250


class TestCreditHistory:
    def test_history_returns_list(self, regular_client):
        r = regular_client.get("/api/credits/history")
        assert r.status_code == 200
        assert "transactions" in r.json()

    def test_admin_can_view_user_history(self, superadmin_client, regular_user_id):
        r = superadmin_client.get(f"/api/admin/credits/history/{regular_user_id}")
        assert r.status_code == 200

    def test_regular_user_cannot_view_admin_history(self, regular_client, superadmin_user_id):
        r = regular_client.get(f"/api/admin/credits/history/{superadmin_user_id}")
        assert r.status_code in (401, 403)


class TestRateConfig:
    def test_admin_can_read_rates(self, superadmin_client):
        r = superadmin_client.get("/api/admin/credits/rates")
        assert r.status_code == 200
        data = r.json()
        assert "rates" in data
        assert len(data["rates"]) > 0

    def test_cost_estimate_returns_blended(self, superadmin_client):
        r = superadmin_client.get(
            "/api/admin/credits/cost-estimate",
            params={"credits": 1000},
        )
        assert r.status_code == 200
        data = r.json()
        assert "blended_cost_usd" in data
        assert data["blended_cost_usd"] > 0
        assert data["min_cost_usd"] <= data["blended_cost_usd"] <= data["max_cost_usd"]
