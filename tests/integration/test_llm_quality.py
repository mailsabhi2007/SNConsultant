"""
LLM Quality Tests — calls the real Anthropic API.

These tests are marked `llm_quality` and are SKIPPED unless ANTHROPIC_API_KEY is set.
In GitHub Actions they run only on pushes to main and on the weekly schedule.

Run locally:
    pytest -m llm_quality -v
"""

import json
import os
import pytest
from pathlib import Path

# Skip entire module if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping LLM quality tests",
)

GOLDEN_QUERIES_PATH = Path(__file__).parent.parent / "fixtures" / "golden_queries.json"
CREDIT_GRANT_FOR_QUALITY_TESTS = 2000  # enough for all 5 queries


@pytest.fixture(scope="module")
def quality_client(api_app):
    """A dedicated client with enough credits to run all quality queries."""
    from tests.integration.conftest import _make_client
    import database
    from api.services.credit_service import grant_credits

    with _make_client(api_app) as setup:
        setup.post("/api/auth/register", json={
            "username": "qualitybot",
            "password": "Qualpass123!",
            "email": "quality@example.com",
        })

    with database.get_db_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE username='qualitybot'"
        ).fetchone()
    user_id = row["user_id"]
    grant_credits(user_id, CREDIT_GRANT_FOR_QUALITY_TESTS, "LLM quality test grant",
                  granted_by="system")

    with _make_client(api_app) as c:
        r = c.post("/api/auth/login", json={
            "username": "qualitybot",
            "password": "Qualpass123!",
        })
        assert r.status_code == 200
        yield c


def load_golden_queries():
    with open(GOLDEN_QUERIES_PATH) as f:
        return json.load(f)


def send_real_message(client, query: str) -> dict:
    r = client.post(
        "/api/chat/message",
        json={"message": query},
        timeout=60,  # LLM can be slow
    )
    assert r.status_code == 200, f"Chat failed ({r.status_code}): {r.text}"
    return r.json()


@pytest.mark.llm_quality
@pytest.mark.parametrize("query_spec", load_golden_queries(), ids=[q["id"] for q in load_golden_queries()])
def test_golden_query(quality_client, query_spec):
    """
    For each golden query:
      1. Response must meet minimum length
      2. All required_keywords must appear (case-insensitive)
      3. At least one of any_of_keywords must appear
      4. Hallucination score (from built-in judge) must be below threshold
    """
    data = send_real_message(quality_client, query_spec["query"])
    response_text = data["response"].lower()

    # 1. Minimum length
    assert len(data["response"]) >= query_spec["min_length"], (
        f"[{query_spec['id']}] Response too short: {len(data['response'])} chars "
        f"(min {query_spec['min_length']})\nResponse: {data['response'][:200]}"
    )

    # 2. Required keywords — all must appear
    for kw in query_spec["required_keywords"]:
        assert kw.lower() in response_text, (
            f"[{query_spec['id']}] Required keyword '{kw}' not found in response.\n"
            f"Response: {data['response'][:300]}"
        )

    # 3. At least one of the contextual keywords
    found_any = any(kw.lower() in response_text for kw in query_spec["any_of_keywords"])
    assert found_any, (
        f"[{query_spec['id']}] None of {query_spec['any_of_keywords']} found in response.\n"
        f"Response: {data['response'][:300]}"
    )

    # 4. Hallucination score from built-in LLM judge
    judge = data.get("judge_result")
    if judge and judge.get("hallucination_score") is not None:
        score = judge["hallucination_score"]
        assert score <= query_spec["max_hallucination_score"], (
            f"[{query_spec['id']}] Hallucination score {score:.2f} exceeds threshold "
            f"{query_spec['max_hallucination_score']}.\n"
            f"Judge reasoning: {judge.get('reasoning', 'N/A')}\n"
            f"Flagged sections: {judge.get('flagged_sections', [])}"
        )


@pytest.mark.llm_quality
@pytest.mark.skipif(
    os.getenv("SEMANTIC_CACHE_ENABLED", "false").lower() != "true",
    reason="Semantic cache is disabled (SEMANTIC_CACHE_ENABLED != true)",
)
def test_cached_response_skips_judge(quality_client):
    """Send the same query twice — second response should be cached."""
    query = "What is a business rule in ServiceNow and when does it run?"

    first = send_real_message(quality_client, query)
    second = send_real_message(quality_client, query)

    assert second.get("is_cached") is True, (
        "Second identical query was not served from cache. "
        "Semantic cache may not be working."
    )
    # Cached responses should cost 0 or very few credits
    if second.get("credits_used") is not None:
        assert second["credits_used"] <= first.get("credits_used", 999), (
            "Cached response cost more credits than original — debit logic may be wrong"
        )


@pytest.mark.llm_quality
def test_credits_debited_per_message(quality_client):
    """Each message reduces the balance by at least 1 credit."""
    before = quality_client.get("/api/credits/balance").json()["balance"]

    send_real_message(quality_client, "How do I use the ServiceNow REST API?")

    after = quality_client.get("/api/credits/balance").json()["balance"]

    assert after < before, "Credits were not debited after a real LLM call"
    assert before - after >= 1, "Credit debit is unrealistically small"
