#!/usr/bin/env python3
"""
Authentication Service
Handles GitHub OAuth, user management, and session tokens
"""

import os
import json
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
        """
        Get user data from session token

        Args:
            session_token: Session token

        Returns:
            User data or None
        """
        session = self.get_session(session_token)
        if session:
            return session.get("user")
        return None


# Global auth service instance
auth_service = AuthService()
