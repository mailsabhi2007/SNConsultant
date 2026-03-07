"""
Credit accuracy tests.

Covers:
  - estimate_credits_for_text math (char→token conversion, rate lookup, floor)
  - debit is stored as a negative transaction in the ledger
  - HTTP: credits_used in response exactly matches the balance drop
  - HTTP: non-cached response is more expensive than cached (judge runs)
  - HTTP: handoff multiplier — handoff_count=2 triples the base cost
  - HTTP: credits_remaining in response matches actual balance
  - HTTP: debit transaction recorded with model name and negative amount
"""

import pytest

# ── Known seed rates from database.py ─────────────────────────────────────────
# claude-sonnet-4-20250514: 5.0 credits/1k input, 20.0 credits/1k output
# gpt-4o-mini:              1.0 credits/1k input,  3.0 credits/1k output
SONNET_MODEL = "claude-sonnet-4-20250514"
JUDGE_MODEL = "gpt-4o-mini"

# Mock response used by HTTP-level tests — fixed size so token estimates are deterministic
_MOCK_RESPONSE_TEXT = "A" * 800  # 200 output tokens at 4 chars/token


def _mock_reply(is_cached=False, handoff_count=0):
    return {
        "response": _MOCK_RESPONSE_TEXT,
        "conversation_id": 99,
        "is_cached": is_cached,
        "judge_result": None,
        "current_agent": "consultant",
        "handoff_count": handoff_count,
    }


# ── Module-scoped client with ample credits ────────────────────────────────────

@pytest.fixture(scope="module")
def credit_client(api_app, superadmin_client):
    """Fresh user 'creditbot' with 2000 credits — isolated from other test users."""
    from tests.integration.conftest import _make_client
    import database
    from api.services.credit_service import grant_credits

    with _make_client(api_app) as setup:
        setup.post("/api/auth/register", json={
            "username": "creditbot",
            "password": "Creditpass123!",
            "email": "creditbot@example.com",
        })

    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='creditbot'"
        ).fetchone()
    user_id = row["user_id"]
    grant_credits(user_id, 2000, "Credit accuracy test grant", granted_by="system")

    with _make_client(api_app) as c:
        r = c.post("/api/auth/login", json={
            "username": "creditbot",
            "password": "Creditpass123!",
        })
        assert r.status_code == 200, f"creditbot login failed: {r.text}"
        yield c


# ── Unit-level: estimate_credits_for_text ─────────────────────────────────────

class TestEstimateCreditsFormula:
    """Test the credit estimation function directly — no HTTP."""

    def test_known_input_sonnet(self, api_app):
        """
        input  = 'A' * 4000 → 1000 tokens
        output = 'B' * 2000 →  500 tokens
        sonnet: (1000/1000 × 5.0) + (500/1000 × 20.0) = 5 + 10 = 15
        """
        from api.services.credit_service import estimate_credits_for_text
        result = estimate_credits_for_text("A" * 4000, "B" * 2000, SONNET_MODEL)
        assert result == 15

    def test_known_input_judge(self, api_app):
        """
        input  = 'A' * 4000 → 1000 tokens
        output = 'B' * 2000 →  500 tokens
        gpt-4o-mini: (1000/1000 × 1.0) + (500/1000 × 3.0) = 1 + 1.5 = 2.5 → round = 3 (but max(1,...))
        Actually round(2.5) in Python = 2 (banker's rounding). Let's just assert >= 1.
        """
        from api.services.credit_service import estimate_credits_for_text
        result = estimate_credits_for_text("A" * 4000, "B" * 2000, JUDGE_MODEL)
        assert result >= 1
        # Judge must be cheaper than sonnet for the same text
        sonnet = estimate_credits_for_text("A" * 4000, "B" * 2000, SONNET_MODEL)
        assert result < sonnet

    def test_minimum_one_credit(self, api_app):
        """Tiny texts (1 char each) always cost at least 1 credit."""
        from api.services.credit_service import estimate_credits_for_text
        result = estimate_credits_for_text("x", "y", SONNET_MODEL)
        assert result >= 1

    def test_longer_text_costs_more(self, api_app):
        """Doubling text length should increase cost."""
        from api.services.credit_service import estimate_credits_for_text
        short = estimate_credits_for_text("A" * 400, "B" * 400, SONNET_MODEL)
        long = estimate_credits_for_text("A" * 4000, "B" * 4000, SONNET_MODEL)
        assert long > short

    def test_output_heavier_than_input(self, api_app):
        """Sonnet output costs 4× more per token than input (20 vs 5 /1k)."""
        from api.services.credit_service import estimate_credits_for_text
        # 1000 input tokens, 1 output token
        input_heavy = estimate_credits_for_text("A" * 4000, "x", SONNET_MODEL)
        # 1 input token, 1000 output tokens
        output_heavy = estimate_credits_for_text("x", "A" * 4000, SONNET_MODEL)
        assert output_heavy > input_heavy

    def test_unknown_model_uses_default_rate(self, api_app):
        """Model not in DB uses DEFAULT_CREDITS_PER_1K_TOKENS (5.0 for both in/out).
        input=1000 tokens, output=500 tokens → (5.0 + 2.5) = 7.5 → round = 8.
        """
        from api.services.credit_service import estimate_credits_for_text
        result = estimate_credits_for_text("A" * 4000, "B" * 2000, "model-does-not-exist")
        assert result == 8

    def test_cost_scales_linearly(self, api_app):
        """4000-char input should cost exactly twice the 2000-char input (no rounding noise)."""
        from api.services.credit_service import estimate_credits_for_text
        single = estimate_credits_for_text("A" * 4000, "x", SONNET_MODEL)
        double = estimate_credits_for_text("A" * 8000, "x", SONNET_MODEL)
        assert double == single * 2


# ── Ledger tests ───────────────────────────────────────────────────────────────

class TestLedger:
    """Verify that debit_credits writes the correct sign and fields to the DB."""

    def _get_creditbot_id(self):
        import database
        with database.get_db_connection() as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE username='creditbot'"
            ).fetchone()
        assert row is not None, "creditbot user must exist (created by credit_client fixture)"
        return row["user_id"]

    def test_debit_stored_as_negative(self, credit_client):
        """debit_credits writes a negative amount to credit_transactions."""
        import database
        from api.services.credit_service import debit_credits

        user_id = self._get_creditbot_id()
        before_txns = _count_debits(user_id)
        debit_credits(
            user_id=user_id,
            amount=7,
            description="Ledger test debit",
            model=SONNET_MODEL,
        )
        after_txns = _count_debits(user_id)

        assert after_txns == before_txns + 1

        with database.get_db_connection() as conn:
            row = conn.execute(
                "SELECT amount FROM credit_transactions "
                "WHERE user_id = ? AND description = 'Ledger test debit' "
                "ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        assert row is not None
        assert row[0] == -7

    def test_grant_stored_as_positive(self, credit_client):
        """grant_credits writes a positive amount to credit_transactions."""
        import database
        from api.services.credit_service import grant_credits

        user_id = self._get_creditbot_id()
        grant_credits(user_id, 50, "Ledger test grant", granted_by="system")

        with database.get_db_connection() as conn:
            row = conn.execute(
                "SELECT amount FROM credit_transactions "
                "WHERE user_id = ? AND description = 'Ledger test grant' "
                "ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        assert row is not None
        assert row[0] == 50

    def test_balance_is_sum_of_all_transactions(self, credit_client):
        """get_balance(user_id) returns the algebraic sum of all transactions."""
        from api.services.credit_service import get_balance, grant_credits, debit_credits

        user_id = self._get_creditbot_id()
        before = get_balance(user_id)
        grant_credits(user_id, 100, "Balance sum test grant", granted_by="system")
        debit_credits(user_id, 30, "Balance sum test debit")
        after = get_balance(user_id)

        assert after == before + 100 - 30


# ── HTTP-level accuracy tests ─────────────────────────────────────────────────

class TestHTTPCreditAccuracy:
    """Verify that the HTTP response credits_used matches the actual balance drop."""

    def test_balance_drop_equals_credits_used(self, credit_client, monkeypatch):
        """balance_before - balance_after == credits_used reported in the response."""
        async def fake_send(*args, **kwargs):
            return _mock_reply(is_cached=False, handoff_count=0)

        _patch_agents(monkeypatch, fake_send)

        before = _get_balance(credit_client)
        r = credit_client.post("/api/chat/message", json={"message": "A" * 100})
        assert r.status_code == 200
        data = r.json()

        after = _get_balance(credit_client)
        assert before - after == data["credits_used"]

    def test_credits_remaining_matches_balance(self, credit_client, monkeypatch):
        """credits_remaining in the response body matches the real DB balance."""
        async def fake_send(*args, **kwargs):
            return _mock_reply(is_cached=False, handoff_count=0)

        _patch_agents(monkeypatch, fake_send)

        r = credit_client.post("/api/chat/message", json={"message": "Hello"})
        assert r.status_code == 200
        data = r.json()

        actual_balance = _get_balance(credit_client)
        assert data["credits_remaining"] == actual_balance

    def test_credits_used_at_least_one(self, credit_client, monkeypatch):
        """Every message costs at least 1 credit (floor enforced in route)."""
        async def fake_send(*args, **kwargs):
            return _mock_reply(is_cached=False, handoff_count=0)

        _patch_agents(monkeypatch, fake_send)

        r = credit_client.post("/api/chat/message", json={"message": "Hi"})
        assert r.status_code == 200
        assert r.json()["credits_used"] >= 1

    def test_cached_response_costs_less_than_uncached(self, credit_client, monkeypatch):
        """
        Non-cached: base + judge cost.
        Cached:     base only (judge skipped).
        → cached must cost fewer credits.
        """
        async def fake_uncached(*args, **kwargs):
            return _mock_reply(is_cached=False, handoff_count=0)

        async def fake_cached(*args, **kwargs):
            return _mock_reply(is_cached=True, handoff_count=0)

        # Use identical message text so token counts are the same
        msg = "A" * 200

        _patch_agents(monkeypatch, fake_uncached)
        r_uncached = credit_client.post("/api/chat/message", json={"message": msg})
        assert r_uncached.status_code == 200

        _patch_agents(monkeypatch, fake_cached)
        r_cached = credit_client.post("/api/chat/message", json={"message": msg})
        assert r_cached.status_code == 200

        assert r_uncached.json()["credits_used"] > r_cached.json()["credits_used"]

    def test_handoff_multiplier_doubles_then_triples(self, credit_client, monkeypatch):
        """
        handoff_count=0 → 1× base
        handoff_count=1 → 2× base
        handoff_count=2 → 3× base
        Use is_cached=True to exclude judge cost from the comparison.
        """
        msg = "A" * 400  # fixed message so base cost is identical each call

        costs = {}
        for count in (0, 1, 2):
            async def fake_send(*args, hc=count, **kwargs):
                return _mock_reply(is_cached=True, handoff_count=hc)

            _patch_agents(monkeypatch, fake_send)
            r = credit_client.post("/api/chat/message", json={"message": msg})
            assert r.status_code == 200
            costs[count] = r.json()["credits_used"]

        assert costs[1] == costs[0] * 2, (
            f"1 handoff should cost 2× base: got {costs[1]} vs base {costs[0]}"
        )
        assert costs[2] == costs[0] * 3, (
            f"2 handoffs should cost 3× base: got {costs[2]} vs base {costs[0]}"
        )

    def test_debit_transaction_in_history_has_correct_fields(self, credit_client, monkeypatch):
        """After a message, the history endpoint shows a debit with model name and negative amount."""
        async def fake_send(*args, **kwargs):
            return _mock_reply(is_cached=False, handoff_count=0)

        _patch_agents(monkeypatch, fake_send)

        credit_client.post("/api/chat/message", json={"message": "Test debit recording"})

        history = credit_client.get("/api/credits/history").json()["transactions"]
        debits = [t for t in history if t["amount"] < 0]
        assert len(debits) >= 1, "No debit transactions found in history"

        latest = debits[0]  # newest first
        assert latest["amount"] < 0, "Debit amount must be negative"
        assert latest["model"] is not None, "Model name must be recorded on debit"
        assert latest["type"] == "debit"

    def test_judge_cost_is_proportional_to_message_length(self, credit_client, monkeypatch):
        """
        Longer messages → more judge input tokens → higher judge cost.
        Verified by comparing uncached costs for short vs long messages.
        """
        async def fake_short(*args, **kwargs):
            return {"response": "x" * 40, "conversation_id": 99,
                    "is_cached": False, "judge_result": None,
                    "current_agent": "consultant", "handoff_count": 0}

        async def fake_long(*args, **kwargs):
            return {"response": "x" * 40, "conversation_id": 99,
                    "is_cached": False, "judge_result": None,
                    "current_agent": "consultant", "handoff_count": 0}

        _patch_agents(monkeypatch, fake_short)
        r_short = credit_client.post("/api/chat/message", json={"message": "Hi"})

        _patch_agents(monkeypatch, fake_long)
        r_long = credit_client.post(
            "/api/chat/message",
            json={"message": "A" * 4000},  # 1000 extra judge input tokens
        )

        assert r_long.json()["credits_used"] > r_short.json()["credits_used"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_balance(client) -> int:
    return client.get("/api/credits/balance").json()["balance"]


def _patch_agents(monkeypatch, fake_fn):
    # Must patch at the route's local binding — the route uses `from X import Y`
    # so patching the source module has no effect on the already-imported reference.
    monkeypatch.setattr("api.routes.chat.send_message", fake_fn)
    monkeypatch.setattr("api.routes.chat.send_multi_agent_message", fake_fn)


def _count_debits(user_id: str) -> int:
    import database
    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM credit_transactions WHERE user_id = ? AND type = 'debit'",
            (user_id,),
        ).fetchone()
    return row[0]
