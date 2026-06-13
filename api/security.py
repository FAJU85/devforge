#!/usr/bin/env python3
"""
Security Module - Production-grade security features
Handles request validation, rate limiting, and security headers
"""

from typing import Callable, Dict, Any, Optional
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import hmac
import secrets
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, requests_per_minute: int = 60):
        """Initialize rate limiter"""
        self.requests_per_minute = requests_per_minute
        self.buckets: Dict[str, list] = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Clean old requests
        self.buckets[identifier] = [
            req_time for req_time in self.buckets[identifier]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.buckets[identifier]) >= self.requests_per_minute:
            return False

        self.buckets[identifier].append(now)
        return True

    def get_retry_after(self, identifier: str) -> int:
        """Get seconds until next request allowed"""
        if not self.buckets[identifier]:
            return 0

        oldest = self.buckets[identifier][0]
        retry_after = (oldest + timedelta(minutes=1) - datetime.utcnow()).total_seconds()
        return max(1, int(retry_after))


class SecurityHeaders(BaseHTTPMiddleware):
    """Add security headers to responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection (note: no X-Frame-Options for iframe embedding)
        response.headers["X-XSS-Protection"] = "0"

        # Strict referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content security policy (permissive for development)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://api.github.com https://api.huggingface.co"
        )

        return response


class InputValidator:
    """Validate user input"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        pattern = r'^https?://[a-zA-Z0-9.-]+'
        return re.match(pattern, url) is not None

    @staticmethod
    def validate_token_format(token: str, min_length: int = 32) -> bool:
        """Validate token format and length"""
        return isinstance(token, str) and len(token) >= min_length

    @staticmethod
    def sanitize_string(s: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(s, str):
            raise ValueError("Input must be string")

        # Truncate
        s = s[:max_length]

        # Remove null bytes
        s = s.replace('\x00', '')

        return s.strip()


class CryptoHelper:
    """Cryptographic utilities"""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple:
        """Hash password with salt"""
        if not salt:
            salt = secrets.token_hex(16)

        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )

        return salt, hash_obj.hex()

    @staticmethod
    def verify_password(password: str, salt: str, hash_value: str) -> bool:
        """Verify password against hash"""
        _, new_hash = CryptoHelper.hash_password(password, salt)
        return hmac.compare_digest(new_hash, hash_value)

    @staticmethod
    def sign_data(data: str, secret: str) -> str:
        """Sign data with HMAC"""
        signature = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def verify_signature(data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        expected = CryptoHelper.sign_data(data, secret)
        return hmac.compare_digest(signature, expected)


# Global rate limiter
rate_limiter = RateLimiter(requests_per_minute=100)

# Input validator
validator = InputValidator()

# Crypto helper
crypto = CryptoHelper()
