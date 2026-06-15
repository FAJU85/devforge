#!/usr/bin/env python3
"""
Authentication Routes
Handles GitHub OAuth and Hugging Face OAuth flows
"""

from fastapi import APIRouter, HTTPException, Cookie, Response
from fastapi.responses import RedirectResponse
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
    """Logout user and invalidate session"""
    if session_token:
        auth_service.invalidate_session(session_token)
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}


# ---------------------------------------------------------------------------
# Hugging Face OAuth endpoints
# ---------------------------------------------------------------------------

@router.get("/hf/login")
async def hf_login():
    """Redirect user to HF OAuth authorization page."""
    from api.services.auth_service import HF_CLIENT_ID
    if not HF_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="HF OAuth is not configured (OAUTH_CLIENT_ID missing). "
                   "This is available on Hugging Face Spaces with hf_oauth: true.",
        )
    auth_url, _state = auth_service.get_hf_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/hf/callback")
async def hf_callback(code: str, state: str, response: Response):
    """Handle HF OAuth callback, set session cookie, redirect to frontend."""
    if not auth_service.verify_hf_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    token_data = await auth_service.exchange_hf_code(code)
    if not token_data:
        raise HTTPException(status_code=401, detail="Failed to authenticate with Hugging Face")

    session_token = auth_service.create_hf_session(
        token_data["user"],
        token_data["access_token"],
    )

    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,  # 24 h
    )
    return redirect


@router.get("/hf/me")
async def hf_me(session_token: str = Cookie(None)):
    """Return current HF user info (without the raw token)."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    hf_token = auth_service.get_hf_token_from_session(session_token)
    return {
        **user,
        "has_hf_token": bool(hf_token),
    }


@router.post("/hf/logout")
async def hf_logout(response: Response, session_token: str = Cookie(None)):
    """Invalidate HF session and clear cookie."""
    if session_token:
        auth_service.invalidate_session(session_token)
    response.delete_cookie("session_token")
    return {"message": "Logged out"}


# ---------------------------------------------------------------------------
# GitHub OAuth endpoints
# ---------------------------------------------------------------------------

@router.get("/github/login")
async def github_login():
    """Redirect user to GitHub OAuth authorization page."""
    from api.services.auth_service import GITHUB_OAUTH_CLIENT_ID
    if not GITHUB_OAUTH_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth is not configured. "
                   "This is available on Hugging Face Spaces with github_oauth: true.",
        )
    auth_url, _state = auth_service.get_github_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(code: str, state: str, response: Response):
    """Handle GitHub OAuth callback, set session cookie, redirect to frontend."""
    if not auth_service.verify_github_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    token_data = await auth_service.exchange_github_code(code)
    if not token_data:
        raise HTTPException(status_code=401, detail="Failed to authenticate with GitHub")

    session_token = auth_service.create_github_session(
        token_data["user"],
        token_data["access_token"],
    )

    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    return redirect


@router.get("/github/me")
async def github_me(session_token: str = Cookie(None)):
    """Return current GitHub user info (without the raw token)."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    github_token = auth_service.get_github_token_from_session(session_token)
    return {
        **user,
        "has_github_token": bool(github_token),
    }


@router.post("/github/logout")
async def github_logout(response: Response, session_token: str = Cookie(None)):
    """Invalidate GitHub session and clear cookie."""
    if session_token:
        auth_service.invalidate_session(session_token)
    response.delete_cookie("session_token")
    return {"message": "Logged out"}
