"""Chat endpoint tests — LLM calls are mocked so no API key needed."""

import pytest


MOCK_AGENT_RESPONSE = {
    "response": "A business rule is a server-side script that runs when a record is inserted, updated, deleted, or displayed.",
    "conversation_id": 1,
    "is_cached": False,
    "judge_result": None,
    "current_agent": "consultant",
    "handoff_count": 0,
}


@pytest.fixture(autouse=True)
def mock_agent(monkeypatch):
    """Patch both agent services so no real LLM calls are made in this module."""
    async def fake_send(*args, **kwargs):
        return MOCK_AGENT_RESPONSE

    monkeypatch.setattr("api.services.agent_service.send_message", fake_send)
    monkeypatch.setattr("api.services.multi_agent_service.send_multi_agent_message", fake_send)


class TestSendMessage:
    def test_message_returns_response(self, funded_client):
        r = funded_client.post(
            "/api/chat/message",
            json={"message": "What is a business rule?"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert len(data["response"]) > 0

    def test_response_includes_credit_fields(self, funded_client):
        r = funded_client.post(
            "/api/chat/message",
            json={"message": "What is a business rule?"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "credits_used" in data
        assert "credits_remaining" in data
        assert data["credits_used"] >= 1
        assert data["credits_remaining"] >= 0

    def test_credits_decrease_after_message(self, funded_client, regular_client):
        before = regular_client.get("/api/credits/balance").json()["balance"]
        funded_client.post(
            "/api/chat/message",
            json={"message": "What is a business rule?"},
        )
        after = regular_client.get("/api/credits/balance").json()["balance"]
        assert after < before

    def test_conversation_id_returned(self, funded_client):
        r = funded_client.post(
            "/api/chat/message",
            json={"message": "What is a business rule?"},
        )
        assert r.status_code == 200
        assert r.json().get("conversation_id") is not None

    def test_zero_credits_returns_402(self, api_app):
        """A brand-new user with zero credits must get HTTP 402."""
        from tests.integration.conftest import _make_client
        with _make_client(api_app) as c:
            c.post("/api/auth/register", json={
                "username": "brokeusr",
                "password": "Testpass123!",
                "email": "broke@example.com",
            })
            c.post("/api/auth/login", json={
                "username": "brokeusr",
                "password": "Testpass123!",
            })
            r = c.post("/api/chat/message", json={"message": "Will this work?"})
        assert r.status_code == 402

    def test_message_without_auth_rejected(self, anon_client):
        r = anon_client.post(
            "/api/chat/message",
            json={"message": "What is a business rule?"},
        )
        assert r.status_code in (401, 403)

    def test_empty_message_rejected(self, funded_client):
        r = funded_client.post(
            "/api/chat/message",
            json={"message": ""},
        )
        assert r.status_code in (400, 422)


class TestConversationHistory:
    def test_list_conversations(self, regular_client):
        r = regular_client.get("/api/chat/conversations")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_conversation_detail(self, funded_client):
        r = funded_client.post(
            "/api/chat/message",
            json={"message": "Test conversation detail"},
        )
        conv_id = r.json().get("conversation_id")
        if conv_id:
            r2 = funded_client.get(f"/api/chat/conversations/{conv_id}")
            assert r2.status_code == 200

    def test_other_users_conversation_inaccessible(self, superadmin_client):
        """Conversations are user-scoped; superadmin cannot read testuser's conv."""
        r = superadmin_client.get("/api/chat/conversations/1")
        assert r.status_code in (403, 404)
