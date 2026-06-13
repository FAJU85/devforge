#!/usr/bin/env python3
"""
Authentication Routes
Handles GitHub OAuth flow and user sessions
"""

from fastapi import APIRouter, HTTPException, Cookie, Response
from pydantic import BaseModel
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthCallbackRequest(BaseModel):
    """GitHub OAuth callback request"""
    code: str
    state: str


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    user: dict


@router.get("/github/redirect")
async def github_redirect():
    """
    Get GitHub OAuth authorization URL

    Returns:
        dict with authorization URL
    """
    auth_url = auth_service.get_github_auth_url()
    return {"auth_url": auth_url}


@router.post("/github/callback")
async def github_callback(request: AuthCallbackRequest, response: Response):
    """
    Handle GitHub OAuth callback

    Args:
        request: Callback request with code and state
        response: Response object to set cookie

    Returns:
        User data and session token
    """
    # Exchange code for token and get user data
    token_data = await auth_service.exchange_code_for_token(request.code)

    if not token_data:
        raise HTTPException(status_code=401, detail="Failed to authenticate with GitHub")

    # Create session
    session_token = auth_service.create_session(token_data["user"])

    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,  # 24 hours
    )

    return {
        "access_token": session_token,
        "user": token_data["user"],
    }


@router.get("/user")
async def get_current_user(session_token: str = Cookie(None)):
    """
    Get current authenticated user

    Args:
        session_token: Session cookie

    Returns:
        Current user data
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


@router.post("/logout")
async def logout(response: Response, session_token: str = Cookie(None)):
    """
    Logout user and invalidate session

    Args:
        response: Response object to clear cookie
        session_token: Session cookie

    Returns:
        Success message
    """
    if session_token:
        auth_service.invalidate_session(session_token)

    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}
