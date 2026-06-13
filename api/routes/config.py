#!/usr/bin/env python3
"""
Configuration Routes
Manages user preferences and API keys
"""

from fastapi import APIRouter, HTTPException, Cookie, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from api.services.config_service import config_service
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/config", tags=["config"])


class ConfigUpdateRequest(BaseModel):
    """Configuration update request"""
    preferred_model: Optional[str] = None
    preferred_provider: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    auto_save: Optional[bool] = None


class APIKeyRequest(BaseModel):
    """API key storage request"""
    provider: str
    api_key: str


async def get_current_user(session_token: str = Cookie(None)):
    """Dependency to get current user from session"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


@router.get("")
async def get_config(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get user configuration

    Returns:
        User configuration dict
    """
    return config_service.get_config(user.get("id"))


@router.patch("")
async def update_config(
    request: ConfigUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update user configuration

    Args:
        request: Configuration updates

    Returns:
        Updated configuration
    """
    config_dict = request.model_dump(exclude_none=True)
    updated = config_service.update_config(user.get("id"), config_dict)
    return updated


@router.get("/keys")
async def list_api_keys(user: Dict[str, Any] = Depends(get_current_user)):
    """
    List stored API keys (without exposing actual keys)

    Returns:
        List of stored providers
    """
    keys = config_service.list_api_keys(user.get("id"))
    return {"stored_keys": keys}


@router.post("/keys")
async def store_api_key(
    request: APIKeyRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Store API key

    Args:
        request: API key and provider

    Returns:
        Success message
    """
    # Validate key format
    if not config_service.validate_api_key(request.provider, request.api_key):
        raise HTTPException(status_code=400, detail="Invalid API key format")

    config_service.store_api_key(user.get("id"), request.provider, request.api_key)
    return {"message": f"API key stored for {request.provider}"}


@router.delete("/keys/{provider}")
async def delete_api_key(
    provider: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Delete API key

    Args:
        provider: Provider name

    Returns:
        Success message
    """
    config_service.delete_api_key(user.get("id"), provider)
    return {"message": f"API key deleted for {provider}"}


@router.post("/keys/test")
async def test_api_key(
    request: APIKeyRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Test API key validity

    Args:
        request: API key and provider

    Returns:
        Test result
    """
    # In a real implementation, this would make a test API call
    is_valid = config_service.validate_api_key(request.provider, request.api_key)

    return {
        "provider": request.provider,
        "valid": is_valid,
        "message": "API key format is valid" if is_valid else "Invalid API key format",
    }
