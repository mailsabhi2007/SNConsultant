"""Admin endpoint access-control tests."""

import pytest


class TestAdminAccess:
    def test_regular_user_cannot_access_admin(self, regular_client):
        r = regular_client.get("/api/admin/credits/overview")
        assert r.status_code in (401, 403)

    def test_unauthenticated_cannot_access_admin(self, anon_client):
        r = anon_client.get("/api/admin/credits/overview")
        assert r.status_code in (401, 403)

    def test_superadmin_can_list_users(self, superadmin_client):
        r = superadmin_client.get("/api/admin/credits/overview")
        assert r.status_code == 200
        users = r.json()
        assert isinstance(users, list)
        assert len(users) >= 2  # at least testuser + superadmin

    def test_superadmin_user_balances_have_required_fields(self, superadmin_client):
        r = superadmin_client.get("/api/admin/credits/overview")
        assert r.status_code == 200
        for user in r.json():
            assert "user_id" in user
            assert "username" in user
            assert "balance" in user
            assert "total_debits" in user


class TestRateConfigAccess:
    def test_superadmin_can_read_rate_config(self, superadmin_client):
        r = superadmin_client.get("/api/admin/credits/rates")
        assert r.status_code == 200

    def test_superadmin_can_update_rate_config(self, superadmin_client):
        rates = superadmin_client.get("/api/admin/credits/rates").json()["rates"]
        r = superadmin_client.put(
            "/api/admin/credits/rates",
            json={"rates": rates},
        )
        assert r.status_code == 200

    def test_regular_user_cannot_update_rates(self, superadmin_client, regular_client):
        rates = superadmin_client.get("/api/admin/credits/rates").json()["rates"]
        r = regular_client.put(
            "/api/admin/credits/rates",
            json={"rates": rates},
        )
        assert r.status_code in (401, 403)


class TestCostEstimate:
    def test_estimate_structure(self, superadmin_client):
        r = superadmin_client.get(
            "/api/admin/credits/cost-estimate",
            params={"credits": 5000},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["credits"] == 5000
        assert len(data["models"]) > 0
        assert data["blended_cost_usd"] > 0
        assert data["min_cost_usd"] <= data["max_cost_usd"]

    def test_haiku_model_in_config(self, superadmin_client):
        """Verify the correct haiku model ID is active (not the old wrong one)."""
        rates = superadmin_client.get("/api/admin/credits/rates").json()["rates"]
        model_ids = [r["model"] for r in rates if r["is_active"]]
        assert "claude-3-5-haiku-20241022" in model_ids, (
            "claude-3-5-haiku-20241022 not found in active rate config — model name mismatch"
        )
        assert "claude-haiku-4-5-20251001" not in model_ids, (
            "Old wrong haiku model ID is still active"
        )
