"""
Multi-turn conversation tests.

Strategy:
  - POST /message tests: agent is mocked; we verify HTTP contract, credit deduction,
    and that the conversation_id flows correctly across turns.
  - GET/DELETE tests: conversations are seeded directly via history_manager so we
    can inspect real stored messages without needing a live LLM.
"""

import pytest


# ── Shared mock ───────────────────────────────────────────────────────────────

def _make_reply(conversation_id: int, is_cached: bool = False):
    return {
        "response": "This is the agent reply.",
        "conversation_id": conversation_id,
        "is_cached": is_cached,
        "judge_result": None,
        "current_agent": "consultant",
        "handoff_count": 0,
    }


@pytest.fixture(autouse=True)
def mock_agent(monkeypatch):
    """Default mock: returns conversation_id=1. Individual tests override as needed.

    Patched at the route's local binding (api.routes.chat.*) because the route
    uses `from X import Y`, making the source module patch ineffective.
    """
    async def fake_send(*args, **kwargs):
        return _make_reply(conversation_id=1)

    monkeypatch.setattr("api.routes.chat.send_message", fake_send)
    monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake_send)


# ── Module-scoped client for multi-turn tests ─────────────────────────────────

@pytest.fixture(scope="module")
def mt_client(api_app, superadmin_client):
    """A fresh user 'mtuser' with 1000 credits for multi-turn testing."""
    from tests.integration.conftest import _make_client
    import database
    from api.services.credit_service import grant_credits

    with _make_client(api_app) as setup:
        setup.post("/api/auth/register", json={
            "username": "mtuser",
            "password": "Mtpass123!",
            "email": "mtuser@example.com",
        })

    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='mtuser'"
        ).fetchone()
    user_id = row["user_id"]
    grant_credits(user_id, 1000, "Multi-turn test grant", granted_by="system")

    with _make_client(api_app) as c:
        r = c.post("/api/auth/login", json={
            "username": "mtuser",
            "password": "Mtpass123!",
        })
        assert r.status_code == 200, f"mtuser login failed: {r.text}"
        yield c, user_id


# ── Sending messages ──────────────────────────────────────────────────────────

class TestMultiTurnSend:
    def test_first_message_returns_conversation_id(self, mt_client, monkeypatch):
        client, _ = mt_client
        async def fake(*args, **kwargs):
            return _make_reply(conversation_id=101)
        monkeypatch.setattr("api.routes.chat.send_message", fake)
        monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake)

        r = client.post("/api/chat/message", json={"message": "First message"})
        assert r.status_code == 200
        assert r.json()["conversation_id"] is not None

    def test_second_message_with_same_conv_id_accepted(self, mt_client, monkeypatch):
        """Sending conversation_id from the first response must return 200."""
        client, _ = mt_client
        conv_id = 202

        async def fake(*args, **kwargs):
            return _make_reply(conversation_id=conv_id)
        monkeypatch.setattr("api.routes.chat.send_message", fake)
        monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake)

        r1 = client.post("/api/chat/message", json={"message": "Turn one"})
        assert r1.status_code == 200

        r2 = client.post(
            "/api/chat/message",
            json={"message": "Turn two", "conversation_id": conv_id},
        )
        assert r2.status_code == 200
        assert r2.json()["conversation_id"] == conv_id

    def test_conversation_id_preserved_across_turns(self, mt_client, monkeypatch):
        """The conversation_id returned in turn 1 is echoed back in turn 2."""
        client, _ = mt_client
        conv_id = 303

        async def fake(*args, **kwargs):
            return _make_reply(conversation_id=conv_id)
        monkeypatch.setattr("api.routes.chat.send_message", fake)
        monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake)

        r1 = client.post("/api/chat/message", json={"message": "Hello"})
        returned_id = r1.json()["conversation_id"]

        r2 = client.post(
            "/api/chat/message",
            json={"message": "Follow-up", "conversation_id": returned_id},
        )
        assert r2.json()["conversation_id"] == returned_id

    def test_each_turn_debits_credits(self, mt_client, monkeypatch):
        """Credits decrease after each message turn independently."""
        client, _ = mt_client
        conv_id = 404

        async def fake(*args, **kwargs):
            return _make_reply(conversation_id=conv_id)
        monkeypatch.setattr("api.routes.chat.send_message", fake)
        monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake)

        bal0 = client.get("/api/credits/balance").json()["balance"]

        client.post("/api/chat/message", json={"message": "Turn 1"})
        bal1 = client.get("/api/credits/balance").json()["balance"]

        client.post(
            "/api/chat/message",
            json={"message": "Turn 2", "conversation_id": conv_id},
        )
        bal2 = client.get("/api/credits/balance").json()["balance"]

        assert bal1 < bal0, "Turn 1 should have debited credits"
        assert bal2 < bal1, "Turn 2 should have debited additional credits"

    def test_new_conversation_gets_different_id(self, mt_client, monkeypatch):
        """Two messages with no conversation_id should each start a new conversation."""
        client, _ = mt_client
        counter = {"n": 1000}

        async def fake(*args, conversation_id=None, **kwargs):
            # Simulate: if no conversation_id passed, assign a new incremented one
            cid = conversation_id if conversation_id else counter["n"]
            counter["n"] += 1
            return _make_reply(conversation_id=cid)
        monkeypatch.setattr("api.routes.chat.send_message", fake)
        monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake)

        r1 = client.post("/api/chat/message", json={"message": "New convo A"})
        r2 = client.post("/api/chat/message", json={"message": "New convo B"})

        assert r1.json()["conversation_id"] != r2.json()["conversation_id"]

    def test_credits_used_reported_each_turn(self, mt_client, monkeypatch):
        """Both turns must include credits_used > 0 in the response."""
        client, _ = mt_client
        conv_id = 505

        async def fake(*args, **kwargs):
            return _make_reply(conversation_id=conv_id)
        monkeypatch.setattr("api.routes.chat.send_message", fake)
        monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake)

        r1 = client.post("/api/chat/message", json={"message": "Credits turn 1"})
        r2 = client.post(
            "/api/chat/message",
            json={"message": "Credits turn 2", "conversation_id": conv_id},
        )

        assert r1.json().get("credits_used", 0) >= 1
        assert r2.json().get("credits_used", 0) >= 1


# ── Stored conversation history ───────────────────────────────────────────────

class TestConversationHistory:
    """
    Test GET/DELETE endpoints against conversations seeded directly in the DB
    via history_manager — no LLM calls, no mocking of storage.
    """

    @pytest.fixture
    def seeded_conversation(self, mt_client):
        """Create a real conversation with 2 turns (4 messages) in the DB."""
        _, user_id = mt_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="Test Multi-Turn")
        add_message(conv_id, "user", "What is a business rule?")
        add_message(conv_id, "assistant", "A business rule runs on record events.")
        add_message(conv_id, "user", "When does it run exactly?")
        add_message(conv_id, "assistant", "It runs on insert, update, delete, or display.")
        return conv_id

    def test_list_includes_seeded_conversation(self, mt_client, seeded_conversation):
        client, _ = mt_client
        r = client.get("/api/chat/conversations")
        assert r.status_code == 200
        ids = [c["conversation_id"] for c in r.json()]
        assert seeded_conversation in ids

    def test_get_detail_returns_all_messages(self, mt_client, seeded_conversation):
        client, _ = mt_client
        r = client.get(f"/api/chat/conversations/{seeded_conversation}")
        assert r.status_code == 200
        data = r.json()
        assert data["conversation_id"] == seeded_conversation
        assert len(data["messages"]) == 4

    def test_messages_preserve_roles(self, mt_client, seeded_conversation):
        client, _ = mt_client
        messages = client.get(
            f"/api/chat/conversations/{seeded_conversation}"
        ).json()["messages"]

        roles = [m["role"] for m in messages]
        assert roles == ["user", "assistant", "user", "assistant"]

    def test_messages_preserve_content(self, mt_client, seeded_conversation):
        client, _ = mt_client
        messages = client.get(
            f"/api/chat/conversations/{seeded_conversation}"
        ).json()["messages"]

        assert messages[0]["content"] == "What is a business rule?"
        assert messages[2]["content"] == "When does it run exactly?"

    def test_conversation_title_stored(self, mt_client, seeded_conversation):
        client, _ = mt_client
        data = client.get(f"/api/chat/conversations/{seeded_conversation}").json()
        assert data["title"] == "Test Multi-Turn"

    def test_message_count_reflects_turns(self, mt_client, seeded_conversation):
        client, _ = mt_client
        convs = client.get("/api/chat/conversations").json()
        match = next((c for c in convs if c["conversation_id"] == seeded_conversation), None)
        assert match is not None
        assert match["message_count"] == 4

    def test_other_user_cannot_read_conversation(self, mt_client, seeded_conversation, superadmin_client):
        """A different user gets 403 or 404 on a conversation they don't own."""
        r = superadmin_client.get(f"/api/chat/conversations/{seeded_conversation}")
        assert r.status_code in (403, 404)

    def test_nonexistent_conversation_returns_404(self, mt_client):
        client, _ = mt_client
        r = client.get("/api/chat/conversations/999999")
        assert r.status_code == 404


# ── Delete conversation ───────────────────────────────────────────────────────

class TestDeleteConversation:
    @pytest.fixture
    def deletable_conversation(self, mt_client):
        _, user_id = mt_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="To Be Deleted")
        add_message(conv_id, "user", "Delete me.")
        add_message(conv_id, "assistant", "Okay, goodbye.")
        return conv_id

    def test_delete_own_conversation(self, mt_client, deletable_conversation):
        client, _ = mt_client
        r = client.delete(f"/api/chat/conversations/{deletable_conversation}")
        assert r.status_code == 200

    def test_deleted_conversation_returns_404(self, mt_client, deletable_conversation):
        client, _ = mt_client
        client.delete(f"/api/chat/conversations/{deletable_conversation}")
        r = client.get(f"/api/chat/conversations/{deletable_conversation}")
        assert r.status_code == 404

    def test_deleted_conversation_absent_from_list(self, mt_client, deletable_conversation):
        client, _ = mt_client
        client.delete(f"/api/chat/conversations/{deletable_conversation}")
        ids = [c["conversation_id"] for c in client.get("/api/chat/conversations").json()]
        assert deletable_conversation not in ids

    def test_delete_nonexistent_conversation_returns_404(self, mt_client):
        client, _ = mt_client
        r = client.delete("/api/chat/conversations/999999")
        assert r.status_code == 404

    def test_cannot_delete_other_users_conversation(self, mt_client, superadmin_client):
        """Seed a conversation for mt_client; superadmin cannot delete it."""
        _, user_id = mt_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="Private")
        add_message(conv_id, "user", "This is mine.")

        r = superadmin_client.delete(f"/api/chat/conversations/{conv_id}")
        assert r.status_code == 404  # scoped by user_id
