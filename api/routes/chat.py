#!/usr/bin/env python3
"""
Chat Routes
Handles chat message processing and conversation management
"""

from fastapi import APIRouter, HTTPException, Cookie, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import uuid
from api.services.chat_service import chat_service
from api.services.auth_service import auth_service
from api.services.token_counter import token_counter
from api.services.providers import ProviderFactory

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


class TokenCountRequest(BaseModel):
    """Token count request"""
    text: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    provider: str
    model: Optional[str] = None


class ProviderListResponse(BaseModel):
    """List of supported providers"""
    providers: List[str]
    models: Dict[str, List[str]]


class ModelListResponse(BaseModel):
    """List of supported models for a provider"""
    provider: str
    models: List[str]


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


@router.get("/providers")
async def list_providers(user: Dict[str, Any] = Depends(get_current_user)):
    """
    List available LLM providers and their models

    Returns:
        Available providers and models
    """
    from api.services.providers import ProviderFactory

    providers = ProviderFactory.get_supported_providers()
    models = {}

    for provider_name in providers:
        try:
            # Try to create a dummy provider to get supported models
            # Note: We don't have a real API key, so this is a workaround
            if provider_name == "anthropic" or provider_name == "claude":
                from api.services.providers.anthropic_provider import AnthropicProvider
                models[provider_name] = AnthropicProvider.SUPPORTED_MODELS
            elif provider_name == "groq":
                from api.services.providers.groq_provider import GroqProvider
                models[provider_name] = GroqProvider.SUPPORTED_MODELS
            elif provider_name in ["huggingface", "hf"]:
                from api.services.providers.huggingface_provider import HuggingFaceProvider
                models[provider_name] = HuggingFaceProvider.SUPPORTED_MODELS
        except Exception:
            models[provider_name] = []

    return {
        "providers": providers,
        "models": models,
    }


@router.post("/count-tokens")
async def count_tokens(
    request: TokenCountRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Count tokens for text or messages

    Args:
        request: Token count request

    Returns:
        Token count and estimated cost
    """
    try:
        # Get user's API key for the provider
        from api.services.config_service import config_service

        api_key = config_service.get_api_key(user.get("id"), request.provider)

        if request.text:
            token_count = token_counter.count_text_tokens(
                request.text,
                request.provider,
                request.model,
                api_key,
            )
        elif request.messages:
            token_count = token_counter.count_messages_tokens(
                request.messages,
                request.provider,
                request.model,
                api_key,
            )
        else:
            raise ValueError("Either 'text' or 'messages' must be provided")

        # Estimate cost (assuming typical output of 20% of input)
        estimated_output = int(token_count * 0.2)
        cost_info = token_counter.estimate_cost(
            token_count,
            estimated_output,
            request.provider,
            request.model,
        )

        # Get token limits
        limits = token_counter.get_token_limits(request.provider, request.model)

        return {
            "provider": request.provider,
            "model": request.model,
            "input_tokens": token_count,
            "estimated_output_tokens": estimated_output,
            "total_estimated_tokens": token_count + estimated_output,
            "cost_info": cost_info,
            "limits": limits,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting tokens: {str(e)}")


@router.get("/models/{provider}")
async def get_provider_models(
    provider: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get supported models for a provider

    Args:
        provider: Provider name

    Returns:
        List of supported models
    """
    try:
        provider_instance = None

        if provider.lower() in ["anthropic", "claude"]:
            from api.services.providers.anthropic_provider import AnthropicProvider
            models = AnthropicProvider.SUPPORTED_MODELS
        elif provider.lower() == "groq":
            from api.services.providers.groq_provider import GroqProvider
            models = GroqProvider.SUPPORTED_MODELS
        elif provider.lower() in ["huggingface", "hf"]:
            from api.services.providers.huggingface_provider import HuggingFaceProvider
            models = HuggingFaceProvider.SUPPORTED_MODELS
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return {
            "provider": provider,
            "models": models,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")


@router.post("/validate-provider")
async def validate_provider(
    provider: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Validate provider connection

    Args:
        provider: Provider name

    Returns:
        Validation result
    """
    try:
        from api.services.config_service import config_service

        api_key = config_service.get_api_key(user.get("id"), provider)
        if not api_key:
            return {
                "provider": provider,
                "valid": False,
                "reason": "No API key configured for this provider",
            }

        llm_provider = ProviderFactory.create_provider(provider, api_key)
        is_valid = await llm_provider.validate_connection()

        return {
            "provider": provider,
            "valid": is_valid,
            "reason": "Connection successful" if is_valid else "Connection failed",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return {
            "provider": provider,
            "valid": False,
            "reason": str(e),
        }
