"""Chat endpoints."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Response, Request

from api.dependencies import get_current_user
from api.models.chat import ChatRequest, ChatResponse, ConversationSummary, ConversationDetail
from api.services.agent_service import send_message
from api.services.auth_service import verify_access_token
from api.services.session_service import get_or_create_session, track_prompt
from history_manager import list_user_conversations, get_conversation, get_conversation_messages


router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def post_message(
    payload: ChatRequest,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to the agent."""
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

    # Track the prompt
    track_prompt(session_id)

    result = await send_message(
        message=payload.message,
        user_id=current_user["user_id"],
        conversation_id=payload.conversation_id,
    )
    return ChatResponse(**result)


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
