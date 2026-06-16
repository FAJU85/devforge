#!/usr/bin/env python3
"""
Authentication Service
Handles GitHub OAuth, HF OAuth, user management, and session tokens
"""

import os
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode

# GitHub OAuth config
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23liZnqDQf1YN0jIhq")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/api/auth/callback")
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# HF OAuth config — injected automatically by HF Spaces when hf_oauth: true
HF_CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
HF_CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")
# Space host injected by HF (e.g. vooom-devforge.hf.space)
_HF_SPACE_HOST = os.getenv("SPACE_HOST", "localhost:8000")
HF_REDIRECT_URI = f"https://{_HF_SPACE_HOST}/api/auth/hf/callback"
HF_AUTH_URL = "https://huggingface.co/oauth/authorize"
HF_TOKEN_URL = "https://huggingface.co/oauth/token"
HF_USER_URL = "https://huggingface.co/oauth/userinfo"

# GitHub OAuth config — injected automatically by HF Spaces when github_oauth: true
GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
GITHUB_OAUTH_CLIENT_SECRET = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
_GITHUB_SPACE_HOST = os.getenv("SPACE_HOST", "localhost:8000")
GITHUB_OAUTH_REDIRECT_URI = f"https://{_GITHUB_SPACE_HOST}/api/auth/github/callback"
GITHUB_OAUTH_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_OAUTH_USER_URL = "https://api.github.com/user"


class AuthService:
    """Handles GitHub OAuth and user authentication"""

    def __init__(self):
        """Initialize auth service"""
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_github_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate GitHub OAuth authorization URL

        Args:
            state: Optional state token for CSRF protection

        Returns:
            Authorization URL for GitHub OAuth flow
        """
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": GITHUB_REDIRECT_URI,
            "scope": "repo,user,read:user",
            "state": state,
        }

        return f"{GITHUB_AUTH_URL}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange GitHub authorization code for access token

        Args:
            code: Authorization code from GitHub callback

        Returns:
            User data dict or None if exchange failed
        """
        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for token
                token_response = await client.post(
                    GITHUB_TOKEN_URL,
                    data={
                        "client_id": GITHUB_CLIENT_ID,
                        "client_secret": GITHUB_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": GITHUB_REDIRECT_URI,
                    },
                    headers={"Accept": "application/json"},
                )

                if token_response.status_code != 200:
                    print(f"Token exchange failed: {token_response.text}")
                    return None

                token_data = token_response.json()
                access_token = token_data.get("access_token")

                if not access_token:
                    return None

                # Get user info
                user_response = await client.get(
                    GITHUB_USER_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if user_response.status_code != 200:
                    print(f"User fetch failed: {user_response.text}")
                    return None

                user_data = user_response.json()

                return {
                    "access_token": access_token,
                    "user": {
                        "id": user_data.get("id"),
                        "login": user_data.get("login"),
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "avatar_url": user_data.get("avatar_url"),
                    },
                }

        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None

    def create_session(self, user_data: Dict[str, Any]) -> str:
        """
        Create a new session for user

        Args:
            user_data: User information

        Returns:
            Session token
        """
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            "user": user_data,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
        }
        return session_token

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data

        Args:
            session_token: Session token

        Returns:
            Session data or None if invalid/expired
        """
        if session_token not in self.sessions:
            return None

        session = self.sessions[session_token]

        # Check if session is expired (24 hours)
        if (datetime.utcnow() - session["created_at"]) > timedelta(hours=24):
            del self.sessions[session_token]
            return None

        # Update last accessed
        session["last_accessed"] = datetime.utcnow()
        return session

    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session

        Args:
            session_token: Session token to invalidate

        Returns:
            True if session was invalidated
        """
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False

    def get_user_from_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get user data from session token"""
        session = self.get_session(session_token)
        if session:
            return session.get("user")
        return None

    def get_hf_token_from_session(self, session_token: str) -> Optional[str]:
        """Get the raw HF access token stored in the session"""
        session = self.get_session(session_token)
        if session:
            return session.get("hf_access_token")
        return None

    # ------------------------------------------------------------------
    # HF OAuth helpers
    # ------------------------------------------------------------------

    def get_hf_auth_url(self) -> tuple[str, str]:
        """Return (authorize_url, state) for the HF OAuth flow."""
        state = secrets.token_urlsafe(32)
        # Store state so we can verify it on callback
        self.sessions[f"_state_{state}"] = {
            "created_at": datetime.utcnow(),
        }
        params = {
            "client_id": HF_CLIENT_ID,
            "redirect_uri": HF_REDIRECT_URI,
            "scope": "openid profile inference-api read-repos",
            "state": state,
            "response_type": "code",
        }
        return f"{HF_AUTH_URL}?{urlencode(params)}", state

    def verify_hf_state(self, state: str) -> bool:
        """Return True if the state was issued by get_hf_auth_url and is recent."""
        key = f"_state_{state}"
        entry = self.sessions.pop(key, None)
        if not entry:
            return False
        age = datetime.utcnow() - entry["created_at"]
        return age.total_seconds() < 600  # 10 minute window

    async def exchange_hf_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange HF auth code for access token and return user info."""
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    HF_TOKEN_URL,
                    data={
                        "client_id": HF_CLIENT_ID,
                        "client_secret": HF_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": HF_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                    timeout=15,
                )
                if token_resp.status_code != 200:
                    print(f"[HF OAuth] token exchange failed: {token_resp.text}")
                    return None

                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    return None

                # Fetch user info
                user_resp = await client.get(
                    HF_USER_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )
                if user_resp.status_code != 200:
                    print(f"[HF OAuth] userinfo failed: {user_resp.text}")
                    return None

                user = user_resp.json()
                return {
                    "access_token": access_token,
                    "user": {
                        "id": user.get("sub"),
                        "username": user.get("preferred_username"),
                        "name": user.get("name"),
                        "email": user.get("email"),
                        "avatar_url": user.get("picture"),
                        "profile_url": f"https://huggingface.co/{user.get('preferred_username')}",
                    },
                }
        except Exception as exc:
            print(f"[HF OAuth] exception: {exc}")
            return None

    def create_hf_session(self, user_data: Dict[str, Any], hf_access_token: str) -> str:
        """Create a session that stores the HF access token alongside user info."""
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            "user": user_data,
            "hf_access_token": hf_access_token,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
        }
        return session_token

    def get_github_token_from_session(self, session_token: str) -> Optional[str]:
        """Get the raw GitHub access token stored in the session."""
        session = self.get_session(session_token)
        if session:
            return session.get("github_access_token")
        return None

    # ------------------------------------------------------------------
    # GitHub OAuth helpers
    # ------------------------------------------------------------------

    def get_github_auth_url(self) -> tuple[str, str]:
        """Return (authorize_url, state) for the GitHub OAuth flow."""
        state = secrets.token_urlsafe(32)
        self.sessions[f"_state_{state}"] = {
            "created_at": datetime.utcnow(),
        }
        params = {
            "client_id": GITHUB_OAUTH_CLIENT_ID,
            "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
            "scope": "repo user read:user",
            "state": state,
            "allow_signup": "true",
        }
        return f"{GITHUB_OAUTH_AUTH_URL}?{urlencode(params)}", state

    def verify_github_state(self, state: str) -> bool:
        """Return True if the state was issued and is recent."""
        key = f"_state_{state}"
        entry = self.sessions.pop(key, None)
        if not entry:
            return False
        age = datetime.utcnow() - entry["created_at"]
        return age.total_seconds() < 600

    async def exchange_github_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange GitHub auth code for access token and return user info."""
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    GITHUB_OAUTH_TOKEN_URL,
                    data={
                        "client_id": GITHUB_OAUTH_CLIENT_ID,
                        "client_secret": GITHUB_OAUTH_CLIENT_SECRET,
                        "code": code,
                        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
                    },
                    headers={"Accept": "application/json"},
                    timeout=15,
                )
                if token_resp.status_code != 200:
                    print(f"[GitHub OAuth] token exchange failed: {token_resp.text}")
                    return None

                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                if not access_token:
                    return None

                user_resp = await client.get(
                    GITHUB_OAUTH_USER_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )
                if user_resp.status_code != 200:
                    print(f"[GitHub OAuth] userinfo failed: {user_resp.text}")
                    return None

                user = user_resp.json()
                return {
                    "access_token": access_token,
                    "user": {
                        "id": user.get("id"),
                        "username": user.get("login"),
                        "name": user.get("name"),
                        "email": user.get("email"),
                        "avatar_url": user.get("avatar_url"),
                        "profile_url": user.get("html_url"),
                    },
                }
        except Exception as exc:
            print(f"[GitHub OAuth] exception: {exc}")
            return None

    def create_github_session(self, user_data: Dict[str, Any], github_access_token: str) -> str:
        """Create a session that stores the GitHub access token alongside user info."""
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            "user": user_data,
            "github_access_token": github_access_token,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
        }
        return session_token


# Global auth service instance
auth_service = AuthService()
