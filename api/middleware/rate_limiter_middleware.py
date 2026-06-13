"""Rate Limiter Middleware - PHASE 6.3 - Rate Limiting Integration"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime
from uuid import UUID
from api.security import RateLimiter
from api.monitoring import logger as event_logger
import os

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-endpoint and per-user rate limiting middleware"""

    # Global rate limiter (100 req/min per user)
    global_limiter = RateLimiter(requests_per_minute=100)

    # Endpoint-specific limiters
    endpoint_limiters = {
        "/api/chat": RateLimiter(requests_per_minute=30),
        "/api/config": RateLimiter(requests_per_minute=10),
        "/api/tasks": RateLimiter(requests_per_minute=5),
    }

    # Bypass paths (no rate limiting)
    BYPASS_PATHS = {
        "/health",
        "/api/health",
        "/api/auth/login",
        "/api/auth/callback",
        "/api/auth/logout",
        "/metrics"
    }

    def __init__(self, app):
        super().__init__(app)
        self.ratelimit_enabled = os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true"

    async def dispatch(self, request: Request, call_next):
        if not self.ratelimit_enabled:
            return await call_next(request)

        # Bypass rate limiting for certain paths
        if any(request.url.path.startswith(p) for p in self.BYPASS_PATHS):
            return await call_next(request)

        # Extract user ID from session or auth header
        user_id = self._extract_user_id(request)
        if not user_id:
            # Allow unauthenticated users for auth endpoints
            if request.url.path.startswith("/api/auth"):
                return await call_next(request)
            # For other endpoints, require authentication
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )

        # Check global rate limit
        if not self.global_limiter.is_allowed(user_id):
            retry_after = self.global_limiter.get_retry_after(user_id)
            event_logger.log_event(
                "rate_limit_exceeded",
                "warning",
                f"Global rate limit exceeded for user {user_id}",
                {"user_id": user_id, "retry_after": retry_after}
            )
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)}
            )

        # Check endpoint-specific rate limit
        endpoint = self._get_endpoint_key(request.url.path)
        if endpoint in self.endpoint_limiters:
            if not self.endpoint_limiters[endpoint].is_allowed(f"{user_id}:{endpoint}"):
                retry_after = self.endpoint_limiters[endpoint].get_retry_after(f"{user_id}:{endpoint}")
                event_logger.log_event(
                    "rate_limit_exceeded",
                    "warning",
                    f"Endpoint rate limit exceeded for user {user_id} on {endpoint}",
                    {"user_id": user_id, "endpoint": endpoint, "retry_after": retry_after}
                )
                return JSONResponse(
                    status_code=429,
                    content={"error": "Endpoint rate limit exceeded"},
                    headers={"Retry-After": str(retry_after)}
                )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining_global = self.global_limiter.requests_per_minute - len(self.global_limiter.buckets.get(user_id, []))
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining_global))
        response.headers["X-RateLimit-Reset"] = str(int((datetime.utcnow().timestamp()) + 60))

        return response

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from session cookie or auth header"""
        # Try session cookie
        if "session_token" in request.cookies:
            return request.cookies.get("session_token", "").split(":")[0]

        # Try Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].split(":")[0]

        # Try custom header
        return request.headers.get("X-User-ID", "")

    def _get_endpoint_key(self, path: str) -> str:
        """Get endpoint key for rate limiting"""
        for endpoint in self.endpoint_limiters:
            if path.startswith(endpoint):
                return endpoint
        return ""
