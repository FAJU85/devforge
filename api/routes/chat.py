#!/usr/bin/env python3
"""
Chat Routes
Handles chat message processing and conversation management
"""

from fastapi import APIRouter, HTTPException, Cookie, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import uuid
from api.services.chat_service import chat_service
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class MessageRequest(BaseModel):
    """Chat message request"""
    conversation_id: Optional[str] = None
    message: str
    model: Optional[str] = None
    provider: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: str
    model: str
    provider: str
    message_count: int


async def get_current_user(session_token: str = Cookie(None)):
    """Dependency to get current user from session"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


@router.post("/send")
async def send_message(
    request: MessageRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Send a chat message

    Args:
        request: Message request with conversation ID and content

    Returns:
        Response from LLM
    """
    # Create or get conversation
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Process message
    response = await chat_service.process_message(
        user_id=user.get("id"),
        conversation_id=conversation_id,
        message=request.message,
        model=request.model,
        provider=request.provider,
    )

    return {
        "conversation_id": conversation_id,
        "response": response,
    }


@router.post("/stream")
async def stream_message(
    request: MessageRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Stream a chat message response

    Args:
        request: Message request

    Returns:
        Streaming response
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    async def generate():
        async for chunk in chat_service.stream_message(
            user_id=user.get("id"),
            conversation_id=conversation_id,
            message=request.message,
            model=request.model,
            provider=request.provider,
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/conversations")
async def list_conversations(user: Dict[str, Any] = Depends(get_current_user)):
    """
    List conversations for current user

    Returns:
        List of conversations
    """
    conversations = chat_service.list_conversations(user.get("id"))
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get specific conversation

    Args:
        conversation_id: Conversation ID

    Returns:
        Conversation data
    """
    conv = chat_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conv.to_dict()


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete a conversation

    Args:
        conversation_id: Conversation ID

    Returns:
        Success message
    """
    if chat_service.delete_conversation(conversation_id):
        return {"message": "Conversation deleted"}

    raise HTTPException(status_code=404, detail="Conversation not found")
