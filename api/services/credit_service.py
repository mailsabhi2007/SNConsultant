"""Credit management service — single source of truth for all credit operations."""

import uuid
from typing import Optional
from datetime import datetime

from database import get_db_connection


# Minimum credits required to send a message
MIN_CREDITS_TO_SEND = 1

# Fallback credit cost when model is unknown
DEFAULT_CREDITS_PER_1K_TOKENS = 5.0


def get_balance(user_id: str) -> int:
    """Return current credit balance for a user (SUM of all transactions)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM credit_transactions WHERE user_id = ?",
            (user_id,),
        )
        return int(cursor.fetchone()[0])


def has_sufficient_credits(user_id: str) -> bool:
    """Check whether user has enough credits to send at least one message."""
    return get_balance(user_id) >= MIN_CREDITS_TO_SEND


def grant_credits(
    user_id: str,
    amount: int,
    description: str,
    granted_by: str,
) -> dict:
    """Grant credits to a user. Returns the new balance."""
    if amount <= 0:
        raise ValueError("Grant amount must be positive")

    txn_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO credit_transactions
            (txn_id, user_id, amount, type, description, granted_by)
            VALUES (?, ?, ?, 'grant', ?, ?)
            """,
            (txn_id, user_id, amount, description, granted_by),
        )

    return {"txn_id": txn_id, "balance": get_balance(user_id)}


def debit_credits(
    user_id: str,
    amount: int,
    description: str,
    ref_message_id: Optional[str] = None,
    tokens_input: Optional[int] = None,
    tokens_output: Optional[int] = None,
    model: Optional[str] = None,
) -> dict:
    """Debit credits from a user after a chat response. Returns remaining balance."""
    if amount <= 0:
        return {"txn_id": None, "balance": get_balance(user_id)}

    txn_id = str(uuid.uuid4())
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO credit_transactions
            (txn_id, user_id, amount, type, description, ref_message_id,
             tokens_input, tokens_output, model)
            VALUES (?, ?, ?, 'debit', ?, ?, ?, ?, ?)
            """,
            (txn_id, user_id, -amount, description, ref_message_id,
             tokens_input, tokens_output, model),
        )

    return {"txn_id": txn_id, "balance": get_balance(user_id)}


def estimate_credits_for_text(input_text: str, output_text: str, model: str) -> int:
    """
    Estimate credit cost for a message exchange.

    Uses character-to-token approximation (4 chars ≈ 1 token), which is the
    standard rough estimate. Replace with actual token counts from the API
    response when available.
    """
    input_tokens = max(1, len(input_text) // 4)
    output_tokens = max(1, len(output_text) // 4)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT credits_per_1k_input_tokens, credits_per_1k_output_tokens
            FROM credit_rate_config
            WHERE model = ? AND is_active = 1
            """,
            (model,),
        )
        row = cursor.fetchone()

    if row:
        rate_in, rate_out = row[0], row[1]
    else:
        rate_in = rate_out = DEFAULT_CREDITS_PER_1K_TOKENS

    cost = (input_tokens / 1000 * rate_in) + (output_tokens / 1000 * rate_out)
    return max(1, round(cost))


def get_transaction_history(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """Return paginated transaction history for a user, newest first."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT txn_id, amount, type, description, ref_message_id,
                   tokens_input, tokens_output, model, granted_by, created_at
            FROM credit_transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
        rows = cursor.fetchall()

    return [
        {
            "txn_id": r[0],
            "amount": r[1],
            "type": r[2],
            "description": r[3],
            "ref_message_id": r[4],
            "tokens_input": r[5],
            "tokens_output": r[6],
            "model": r[7],
            "granted_by": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]


def get_all_user_balances() -> list[dict]:
    """Return all users with their current balance. For admin overview."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.user_id, u.username, u.email,
                   COALESCE(SUM(t.amount), 0) AS balance,
                   MAX(t.created_at) AS last_transaction_at,
                   COUNT(CASE WHEN t.type = 'debit' THEN 1 END) AS total_debits
            FROM users u
            LEFT JOIN credit_transactions t ON u.user_id = t.user_id
            GROUP BY u.user_id, u.username, u.email
            ORDER BY balance DESC
            """,
        )
        rows = cursor.fetchall()

    return [
        {
            "user_id": r[0],
            "username": r[1],
            "email": r[2],
            "balance": int(r[3]),
            "last_transaction_at": r[4],
            "total_debits": int(r[5]),
        }
        for r in rows
    ]


def get_rate_config() -> list[dict]:
    """Return all model rate configs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT model, display_name, credits_per_1k_input_tokens,
                   credits_per_1k_output_tokens, api_cost_per_1k_input_usd,
                   api_cost_per_1k_output_usd, typical_input_ratio, is_active, updated_at
            FROM credit_rate_config
            ORDER BY is_active DESC, display_name
            """
        )
        rows = cursor.fetchall()

    return [
        {
            "model": r[0],
            "display_name": r[1],
            "credits_per_1k_input_tokens": r[2],
            "credits_per_1k_output_tokens": r[3],
            "api_cost_per_1k_input_usd": r[4],
            "api_cost_per_1k_output_usd": r[5],
            "typical_input_ratio": r[6],
            "is_active": bool(r[7]),
            "updated_at": r[8],
        }
        for r in rows
    ]


def upsert_rate_config(
    model: str,
    display_name: str,
    credits_per_1k_input_tokens: float,
    credits_per_1k_output_tokens: float,
    api_cost_per_1k_input_usd: float,
    api_cost_per_1k_output_usd: float,
    typical_input_ratio: float = 0.70,
    is_active: bool = True,
) -> None:
    """Insert or update a model's rate config."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO credit_rate_config
            (model, display_name, credits_per_1k_input_tokens, credits_per_1k_output_tokens,
             api_cost_per_1k_input_usd, api_cost_per_1k_output_usd, typical_input_ratio,
             is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(model) DO UPDATE SET
                display_name = excluded.display_name,
                credits_per_1k_input_tokens = excluded.credits_per_1k_input_tokens,
                credits_per_1k_output_tokens = excluded.credits_per_1k_output_tokens,
                api_cost_per_1k_input_usd = excluded.api_cost_per_1k_input_usd,
                api_cost_per_1k_output_usd = excluded.api_cost_per_1k_output_usd,
                typical_input_ratio = excluded.typical_input_ratio,
                is_active = excluded.is_active,
                updated_at = CURRENT_TIMESTAMP
            """,
            (model, display_name, credits_per_1k_input_tokens, credits_per_1k_output_tokens,
             api_cost_per_1k_input_usd, api_cost_per_1k_output_usd, typical_input_ratio,
             int(is_active)),
        )


def get_cost_estimate_for_credits(credits: int) -> dict:
    """
    For a given credit amount, return the estimated API cost breakdown per model.
    Also returns a blended_cost_usd reflecting real-world usage mix:
      85% Claude Sonnet (main agent, runs every message)
      15% GPT-4o-mini  (LLM judge, runs every non-cached message)
    Used by the admin assign-credits modal.
    """
    rates = get_rate_config()
    models = []
    cost_by_model: dict[str, float] = {}

    for r in rates:
        if not r["is_active"]:
            continue

        ratio_in = r["typical_input_ratio"]
        ratio_out = 1.0 - ratio_in

        blended_rate = ratio_in * r["credits_per_1k_input_tokens"] + ratio_out * r["credits_per_1k_output_tokens"]
        if blended_rate <= 0:
            continue

        total_tokens = (credits / blended_rate) * 1000
        tokens_in = total_tokens * ratio_in
        tokens_out = total_tokens * ratio_out

        input_cost = tokens_in / 1000 * r["api_cost_per_1k_input_usd"]
        output_cost = tokens_out / 1000 * r["api_cost_per_1k_output_usd"]
        total_cost = input_cost + output_cost

        cost_by_model[r["model"]] = total_cost
        models.append({
            "model": r["model"],
            "display_name": r["display_name"],
            "estimated_api_cost_usd": round(total_cost, 4),
            "estimated_input_tokens": int(tokens_in),
            "estimated_output_tokens": int(tokens_out),
        })

    if not models:
        return {"credits": credits, "models": [], "min_cost_usd": 0, "max_cost_usd": 0, "blended_cost_usd": 0}

    # Blended realistic estimate: 85% Sonnet (main) + 15% gpt-4o-mini (judge)
    # Falls back to averaging available models if either isn't in config
    BLEND = {"claude-sonnet-4-20250514": 0.85, "gpt-4o-mini": 0.15}
    available_blend = {m: w for m, w in BLEND.items() if m in cost_by_model}
    if available_blend:
        total_weight = sum(available_blend.values())
        blended_cost = sum(
            cost_by_model[m] * (w / total_weight)
            for m, w in available_blend.items()
        )
    else:
        # Fallback: simple average of all active model costs
        blended_cost = sum(cost_by_model.values()) / len(cost_by_model)

    costs = [m["estimated_api_cost_usd"] for m in models]
    return {
        "credits": credits,
        "models": models,
        "min_cost_usd": round(min(costs), 4),
        "max_cost_usd": round(max(costs), 4),
        "blended_cost_usd": round(blended_cost, 4),
    }
