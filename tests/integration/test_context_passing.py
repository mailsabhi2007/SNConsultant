"""
Context-passing tests — verifies that conversation history is loaded into
the LLM's context on every subsequent turn.

Reproduces the bug found in superadmin's change management conversation:
  Turn 1: "help me fix issue with my change management system..."
  Turn 2: "there is insufficient planning and conflicts causing major blockade"
  Turn 3: "we are dealing with technical conflicts"
  → The assistant gave identical generic clarifying questions on turns 2 and 3
    because it received no prior conversation history and treated each message
    as a brand-new conversation.

Fix: MultiAgentOrchestrator.invoke() and ServiceNowAgent.invoke() now load the
last 20 stored messages from the DB before building the initial graph state.
"""

import asyncio
import pytest
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_reply(conversation_id, text="Agent reply."):
    return {
        "response": text,
        "conversation_id": conversation_id,
        "is_cached": False,
        "judge_result": None,
        "current_agent": "consultant",
        "handoff_count": 0,
    }


def _patch_agents(monkeypatch, fake_fn):
    monkeypatch.setattr("api.routes.chat.send_message", fake_fn)
    monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake_fn)


# ── Module-scoped client ───────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ctx_client(api_app, superadmin_client):
    """User 'contextbot' with 2000 credits for context-passing tests."""
    from tests.integration.conftest import _make_client
    import database
    from api.services.credit_service import grant_credits

    with _make_client(api_app) as setup:
        setup.post("/api/auth/register", json={
            "username": "contextbot",
            "password": "Contextpass123!",
            "email": "contextbot@example.com",
        })

    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='contextbot'"
        ).fetchone()
    user_id = row["user_id"]
    grant_credits(user_id, 2000, "Context test grant", granted_by="system")

    with _make_client(api_app) as c:
        r = c.post("/api/auth/login", json={
            "username": "contextbot",
            "password": "Contextpass123!",
        })
        assert r.status_code == 200
        yield c, user_id


# ── Unit: MultiAgentOrchestrator state building ────────────────────────────────

class TestMultiAgentOrchestratorContextLoading:
    """
    Tests that MultiAgentOrchestrator.invoke() correctly loads prior
    conversation messages from the DB into the graph's initial state.

    These tests patch graph.ainvoke to capture the state passed to the graph
    rather than running the full LangGraph pipeline.
    """

    @pytest.fixture
    def change_mgmt_conv(self, ctx_client):
        """
        Seed the exact 4-message history from superadmin's conversation
        (turns 1 and 2 already completed, about to send turn 3).
        """
        _, user_id = ctx_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="Change mgmt context test")
        add_message(conv_id, "user",
            "help me fix issue with my change management system, "
            "I want to make the change process to be more proactive than reactive")
        add_message(conv_id, "assistant",
            "I can help optimize your change management process. "
            "What specific reactive patterns are you seeing? "
            "For example: changes submitted too late, conflicts between overlapping "
            "changes, or insufficient risk assessment upfront?")
        add_message(conv_id, "user",
            "there is insufficient planning and conflicts causing major blockade")
        add_message(conv_id, "assistant",
            "Got it — insufficient planning and change conflicts are blocking your team. "
            "Key ServiceNow tools: CAB Workbench for scheduling conflict detection, "
            "Risk Calculator for automated risk scoring, and change windows enforcement. "
            "Are you using the standard change process or a customized workflow?")
        return conv_id, user_id

    def test_prior_messages_present_in_graph_state(self, change_mgmt_conv):
        """
        On turn 3, graph state must contain turns 1 and 2 as prior messages —
        not just the current 'we are dealing with technical conflicts' message.
        """
        conv_id, user_id = change_mgmt_conv
        captured = {}

        async def fake_ainvoke(state, **kwargs):
            captured["messages"] = list(state["messages"])
            return {
                "messages": state["messages"] + [
                    AIMessage(content="For technical conflicts use CAB Workbench.")
                ],
                "current_agent": "consultant",
                "handoff_history": [],
            }

        from multi_agent.graph import MultiAgentOrchestrator
        orchestrator = MultiAgentOrchestrator(user_id=user_id)

        with patch.object(orchestrator.graph, "ainvoke", side_effect=fake_ainvoke):
            asyncio.run(orchestrator.invoke(
                message="we are dealing with technical conflicts",
                conversation_id=conv_id,
            ))

        messages = captured["messages"]
        human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        ai_msgs = [m for m in messages if isinstance(m, AIMessage)]

        # Must have 3 HumanMessages: turn-1 user, turn-2 user, current (turn-3)
        assert len(human_msgs) == 3, (
            f"Expected 3 HumanMessages (2 prior + 1 current), got {len(human_msgs)}. "
            "Prior conversation history was not loaded from the DB."
        )
        assert len(ai_msgs) == 2, (
            f"Expected 2 AIMessages (2 prior assistant turns), got {len(ai_msgs)}. "
            "Prior conversation history was not loaded from the DB."
        )

        # The LAST HumanMessage must be the current turn
        assert human_msgs[-1].content == "we are dealing with technical conflicts"

        # The FIRST HumanMessage must be the original change management query
        assert "change management" in human_msgs[0].content.lower(), (
            "First HumanMessage should be the original change management query"
        )

        # Prior assistant context must mention change management topics
        prior_ai_content = " ".join(m.content for m in ai_msgs).lower()
        assert any(kw in prior_ai_content for kw in ["change", "planning", "conflict"]), (
            "Prior AIMessages should contain change-management context"
        )

    def test_new_conversation_has_only_current_message(self):
        """
        First message in a brand-new conversation (no conversation_id) must
        have exactly 1 HumanMessage in state — no history to load.
        """
        captured = {}

        async def fake_ainvoke(state, **kwargs):
            captured["messages"] = list(state["messages"])
            return {
                "messages": state["messages"] + [AIMessage(content="Happy to help.")],
                "current_agent": "consultant",
                "handoff_history": [],
            }

        from multi_agent.graph import MultiAgentOrchestrator
        orchestrator = MultiAgentOrchestrator(user_id=None)

        with patch.object(orchestrator.graph, "ainvoke", side_effect=fake_ainvoke):
            asyncio.run(orchestrator.invoke(
                message="Hello, can you help with ServiceNow?",
                conversation_id=None,
            ))

        messages = captured["messages"]
        human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        assert len(human_msgs) == 1
        assert human_msgs[0].content == "Hello, can you help with ServiceNow?"

    def test_history_capped_at_20_messages(self, ctx_client):
        """
        When a conversation has more than 20 prior messages, only the most
        recent 20 are loaded to avoid blowing the context window.
        """
        _, user_id = ctx_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="Long history cap test")
        # Seed 30 stored messages (15 full turns) — well over the 20-message cap
        for i in range(15):
            add_message(conv_id, "user", f"Turn {i+1} user message")
            add_message(conv_id, "assistant", f"Turn {i+1} assistant reply")

        captured = {}

        async def fake_ainvoke(state, **kwargs):
            captured["messages"] = list(state["messages"])
            return {
                "messages": state["messages"] + [AIMessage(content="Reply.")],
                "current_agent": "consultant",
                "handoff_history": [],
            }

        from multi_agent.graph import MultiAgentOrchestrator
        orchestrator = MultiAgentOrchestrator(user_id=user_id)

        with patch.object(orchestrator.graph, "ainvoke", side_effect=fake_ainvoke):
            asyncio.run(orchestrator.invoke(
                message="Turn 16 user message",
                conversation_id=conv_id,
            ))

        messages = captured["messages"]
        # 20 prior + 1 current = 21 max
        assert len(messages) <= 21, (
            f"History not capped — got {len(messages)} messages in state. "
            "Long conversations could exceed the context window."
        )

        # Current message must always be the last HumanMessage
        human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
        assert human_msgs[-1].content == "Turn 16 user message"

    def test_context_order_is_chronological(self, ctx_client):
        """
        Prior messages must appear in chronological order so the LLM sees the
        conversation unfold naturally (not reversed or scrambled).
        """
        _, user_id = ctx_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="Order test")
        add_message(conv_id, "user", "First question")
        add_message(conv_id, "assistant", "First answer")
        add_message(conv_id, "user", "Second question")
        add_message(conv_id, "assistant", "Second answer")

        captured = {}

        async def fake_ainvoke(state, **kwargs):
            captured["messages"] = list(state["messages"])
            return {
                "messages": state["messages"] + [AIMessage(content="Third answer.")],
                "current_agent": "consultant",
                "handoff_history": [],
            }

        from multi_agent.graph import MultiAgentOrchestrator
        orchestrator = MultiAgentOrchestrator(user_id=user_id)

        with patch.object(orchestrator.graph, "ainvoke", side_effect=fake_ainvoke):
            asyncio.run(orchestrator.invoke(
                message="Third question",
                conversation_id=conv_id,
            ))

        messages = captured["messages"]
        # Roles should alternate: user, assistant, user, assistant, user
        expected_roles = ["user", "assistant", "user", "assistant", "user"]
        actual_roles = [
            "user" if isinstance(m, HumanMessage) else "assistant"
            for m in messages
        ]
        assert actual_roles == expected_roles, (
            f"Messages not in chronological order. Expected {expected_roles}, "
            f"got {actual_roles}"
        )


# ── HTTP: 3-turn change management scenario ───────────────────────────────────

class TestChangeManagementHTTP:
    """
    End-to-end HTTP tests reproducing the exact 3-turn scenario from
    superadmin's conversation. Verifies the API route correctly:
    - Returns a conversation_id on the first turn
    - Accepts and preserves that conversation_id on subsequent turns
    - Stores all 6 messages (3 user + 3 assistant) in the DB
    """

    def test_conversation_id_preserved_across_all_three_turns(self, ctx_client, monkeypatch):
        """conversation_id from turn 1 must be echoed back in turns 2 and 3."""
        client, _ = ctx_client
        cid_holder = [None]

        async def fake_t1(*args, **kwargs):
            cid_holder[0] = 5001
            return _make_reply(5001, "What reactive patterns are you seeing?")

        async def fake_t2(*args, **kwargs):
            return _make_reply(cid_holder[0], "Got it — CAB Workbench helps with conflict detection.")

        async def fake_t3(*args, **kwargs):
            return _make_reply(cid_holder[0], "For technical conflicts, use change collision detection.")

        _patch_agents(monkeypatch, fake_t1)
        r1 = client.post("/api/chat/message", json={
            "message": "help me fix issue with my change management system, "
                       "I want to make the change process more proactive"
        })
        assert r1.status_code == 200
        cid = r1.json()["conversation_id"]
        assert cid is not None, "Turn 1 must return a conversation_id"

        _patch_agents(monkeypatch, fake_t2)
        r2 = client.post("/api/chat/message", json={
            "message": "there is insufficient planning and conflicts causing major blockade",
            "conversation_id": cid,
        })
        assert r2.status_code == 200
        assert r2.json()["conversation_id"] == cid, "Turn 2 must preserve conversation_id"

        _patch_agents(monkeypatch, fake_t3)
        r3 = client.post("/api/chat/message", json={
            "message": "we are dealing with technical conflicts",
            "conversation_id": cid,
        })
        assert r3.status_code == 200
        assert r3.json()["conversation_id"] == cid, "Turn 3 must preserve conversation_id"

    def test_all_six_messages_stored_in_db(self, ctx_client):
        """
        A 3-turn change management conversation seeded directly into the DB
        must have exactly 6 messages in the correct role order when fetched
        via the conversation detail endpoint.
        """
        client, user_id = ctx_client
        from history_manager import create_conversation, add_message

        conv_id = create_conversation(user_id, title="CM 3-turn DB check")
        add_message(conv_id, "user",
            "help me fix issue with my change management system")
        add_message(conv_id, "assistant",
            "What reactive patterns are you seeing?")
        add_message(conv_id, "user",
            "there is insufficient planning and conflicts causing major blockade")
        add_message(conv_id, "assistant",
            "Got it — insufficient planning. Key tool: CAB Workbench.")
        add_message(conv_id, "user",
            "we are dealing with technical conflicts")
        add_message(conv_id, "assistant",
            "For technical conflicts, use change collision detection in CAB Workbench.")

        history = client.get(f"/api/chat/conversations/{conv_id}").json()
        messages = history["messages"]

        assert len(messages) == 6, (
            f"Expected 6 messages (3 user + 3 assistant), got {len(messages)}"
        )

        # Roles must alternate user/assistant
        roles = [m["role"] for m in messages]
        assert roles == ["user", "assistant", "user", "assistant", "user", "assistant"], (
            f"Unexpected role order: {roles}"
        )

    def test_credits_debited_on_all_three_turns(self, ctx_client, monkeypatch):
        """Credits must decrease after each of the 3 turns independently."""
        client, _ = ctx_client
        cid_holder = [5003]

        async def fake(*args, **kwargs):
            return _make_reply(cid_holder[0], "Reply.")

        _patch_agents(monkeypatch, fake)

        bal0 = client.get("/api/credits/balance").json()["balance"]

        r1 = client.post("/api/chat/message", json={"message": "CM turn 1"})
        assert r1.status_code == 200
        cid = r1.json()["conversation_id"]
        cid_holder[0] = cid
        bal1 = client.get("/api/credits/balance").json()["balance"]

        client.post("/api/chat/message", json={"message": "CM turn 2", "conversation_id": cid})
        bal2 = client.get("/api/credits/balance").json()["balance"]

        client.post("/api/chat/message", json={"message": "CM turn 3", "conversation_id": cid})
        bal3 = client.get("/api/credits/balance").json()["balance"]

        assert bal1 < bal0, "Turn 1 must debit credits"
        assert bal2 < bal1, "Turn 2 must debit additional credits"
        assert bal3 < bal2, "Turn 3 must debit additional credits"

    def test_each_turn_reports_credits_used(self, ctx_client, monkeypatch):
        """All 3 turns must include credits_used >= 1 in the HTTP response."""
        client, _ = ctx_client
        cid_holder = [5004]

        async def fake(*args, **kwargs):
            return _make_reply(cid_holder[0], "Reply.")

        _patch_agents(monkeypatch, fake)

        r1 = client.post("/api/chat/message", json={"message": "CM credits turn 1"})
        cid = r1.json()["conversation_id"]
        cid_holder[0] = cid

        r2 = client.post("/api/chat/message", json={"message": "CM credits turn 2", "conversation_id": cid})
        r3 = client.post("/api/chat/message", json={"message": "CM credits turn 3", "conversation_id": cid})

        assert r1.json().get("credits_used", 0) >= 1, "Turn 1 must report credits_used >= 1"
        assert r2.json().get("credits_used", 0) >= 1, "Turn 2 must report credits_used >= 1"
        assert r3.json().get("credits_used", 0) >= 1, "Turn 3 must report credits_used >= 1"
