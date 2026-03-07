"""Chat endpoints."""

import asyncio
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Response, Request

from api.dependencies import get_current_user
from api.models.chat import ChatRequest, ChatResponse, ConversationSummary, ConversationDetail
from api.services.agent_service import send_message
from api.services.multi_agent_service import send_multi_agent_message
from api.services.auth_service import verify_access_token
from api.services.session_service import get_or_create_session, track_prompt
from api.services.credit_service import (
    has_sufficient_credits,
    debit_credits,
    estimate_credits_for_text,
    get_balance,
)
from history_manager import list_user_conversations, get_conversation, get_conversation_messages


def _active_model() -> str:
    """Return the model name currently in use (mirrors agent.py logic)."""
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT config_value FROM multi_agent_config WHERE config_key = 'anthropic_model' AND is_active = 1"
            )
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def post_message(
    payload: ChatRequest,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to the agent.

    Automatically routes to multi-agent system if enabled for user via feature flag.
    """
    # Get or create session for tracking
    session_id = request.cookies.get("session_id")
    session_id = get_or_create_session(current_user["user_id"], session_id)

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=1800  # 30 minutes
    )

    # Check credits before calling LLM
    if not has_sufficient_credits(current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient credits")

    # Track the prompt
    track_prompt(session_id)

    result = await send_message(
        message=payload.message,
        user_id=current_user["user_id"],
        conversation_id=payload.conversation_id,
    )

    # Debit credits based on estimated token usage
    model = _active_model()
    response_text = result.get("response", "")
    is_cached = result.get("is_cached", False)
    handoff_count = int(result.get("handoff_count") or 0)

    # Base estimate: user message → final response (1 agent call)
    base_credits = estimate_credits_for_text(payload.message, response_text, model)

    # Handoff multiplier: each additional specialist agent processes the full context again
    credits_used = base_credits * (1 + handoff_count)

    # Judge cost: gpt-4o-mini runs on every non-cached response
    # Input = user message + assistant response; output = ~100-token JSON verdict
    if not is_cached:
        judge_model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
        judge_credits = estimate_credits_for_text(
            payload.message + response_text,
            "x" * 400,  # ~100 tokens JSON output
            judge_model,
        )
        credits_used += judge_credits

    credits_used = max(1, round(credits_used))
    debit_result = debit_credits(
        user_id=current_user["user_id"],
        amount=credits_used,
        description=f"Chat ({model}{f', {handoff_count} handoff(s)' if handoff_count else ''}{', cached' if is_cached else ''})",
        tokens_input=len(payload.message) // 4,
        tokens_output=len(response_text) // 4,
        model=model,
    )

    return ChatResponse(**result, credits_used=credits_used, credits_remaining=debit_result["balance"])


@router.post("/multi-agent/message", response_model=ChatResponse)
async def post_multi_agent_message(
    payload: ChatRequest,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to the multi-agent system (direct access for testing/admin).

    This endpoint always uses the multi-agent system, bypassing the feature flag.
    Useful for testing and admin preview.
    """
    # Get or create session for tracking
    session_id = request.cookies.get("session_id")
    session_id = get_or_create_session(current_user["user_id"], session_id)

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=1800  # 30 minutes
    )

    # Check credits before calling LLM
    if not has_sufficient_credits(current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient credits")

    # Track the prompt
    track_prompt(session_id)

    result = await send_multi_agent_message(
        message=payload.message,
        user_id=current_user["user_id"],
        conversation_id=payload.conversation_id,
    )

    # Debit credits based on estimated token usage
    model = _active_model()
    response_text = result.get("response", "")
    is_cached = result.get("is_cached", False)
    handoff_count = int(result.get("handoff_count") or 0)

    # Base estimate: user message → final response (1 agent call)
    base_credits = estimate_credits_for_text(payload.message, response_text, model)

    # Handoff multiplier: each additional specialist agent processes the full context again
    credits_used = base_credits * (1 + handoff_count)

    # Judge cost: gpt-4o-mini runs on every non-cached response
    if not is_cached:
        judge_model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
        judge_credits = estimate_credits_for_text(
            payload.message + response_text,
            "x" * 400,  # ~100 tokens JSON output
            judge_model,
        )
        credits_used += judge_credits

    credits_used = max(1, round(credits_used))
    debit_result = debit_credits(
        user_id=current_user["user_id"],
        amount=credits_used,
        description=f"Chat ({model}{f', {handoff_count} handoff(s)' if handoff_count else ''}{', cached' if is_cached else ''})",
        tokens_input=len(payload.message) // 4,
        tokens_output=len(response_text) // 4,
        model=model,
    )

    return ChatResponse(**result, credits_used=credits_used, credits_remaining=debit_result["balance"])


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    limit: int = 50, current_user: dict = Depends(get_current_user)
) -> list[ConversationSummary]:
    """List user's conversations."""
    conversations = list_user_conversations(current_user["user_id"], limit=limit)
    return [ConversationSummary(**conv) for conv in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation_detail(
    conversation_id: int, current_user: dict = Depends(get_current_user)
) -> ConversationDetail:
    """Get conversation detail and messages."""
    conversation = get_conversation(conversation_id, user_id=current_user["user_id"])
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    messages = get_conversation_messages(conversation_id)
    return ConversationDetail(**conversation, messages=messages)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int, current_user: dict = Depends(get_current_user)
) -> dict:
    """Delete a conversation."""
    from history_manager import delete_conversation as delete_conv
    success = delete_conv(conversation_id, user_id=current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {"status": "ok"}


@router.websocket("/stream")
async def stream_chat(websocket: WebSocket, token: Optional[str] = None) -> None:
    """WebSocket endpoint for streaming responses."""
    await websocket.accept()

    # Try cookie-based auth first (from HTTP-only cookie)
    cookie_token = websocket.cookies.get("access_token")
    auth_token = cookie_token or token

    if not auth_token:
        await websocket.send_json({"type": "error", "error": "Authentication required"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = verify_access_token(auth_token)
    if not user:
        await websocket.send_json({"type": "error", "error": "Invalid token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get or create session
    session_id = websocket.cookies.get("session_id")
    session_id = get_or_create_session(user["user_id"], session_id)

    try:
        payload = await websocket.receive_json()
        message = payload.get("message", "")
        conversation_id = payload.get("conversation_id")

        if not message:
            await websocket.send_json({"type": "error", "error": "Message is required"})
            await websocket.close()
            return

        # Track the prompt
        track_prompt(session_id)

        result = await send_message(
            message=message,
            user_id=user["user_id"],
            conversation_id=conversation_id,
        )
        response_text = result.get("response", "")

        # Stream tokens with small delays for smooth animation
        words = response_text.split()
        for i, word in enumerate(words):
            await websocket.send_json({"type": "token", "content": word + " "})
            # Small delay between words for streaming effect
            if i < len(words) - 1:
                await asyncio.sleep(0.02)

        await websocket.send_json({
            "type": "done",
            "conversation_id": result.get("conversation_id"),
            "is_cached": result.get("is_cached", False),
            "judge_result": result.get("judge_result"),
        })
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "error": str(exc)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
