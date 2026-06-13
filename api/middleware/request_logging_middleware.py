"""Request Logging Middleware - PHASE 6.4 - Logging & Audit Trail"""

import logging
import time
import json
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from api.monitoring import logger as event_logger, EventLevel

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses with correlation IDs"""

    # Paths to skip logging
    SKIP_PATHS = {
        "/health",
        "/metrics",
        "/static",
    }

    # Sensitive headers to redact
    SENSITIVE_HEADERS = {
        "authorization",
        "x-api-key",
        "x-auth-token",
        "password",
        "secret",
        "token"
    }

    # Sensitive query parameters
    SENSITIVE_PARAMS = {
        "password",
        "api_key",
        "token",
        "secret"
    }

    def __init__(self, app):
        super().__init__(app)
        self.correlation_id_context = {}

    async def dispatch(self, request: Request, call_next):
        # Skip logging for certain paths
        if any(request.url.path.startswith(p) for p in self.SKIP_PATHS):
            return await call_next(request)

        # Generate or retrieve correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        # Extract user ID
        user_id = self._extract_user_id(request)
        request.state.user_id = user_id

        # Capture request info
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_string = str(request.url.query) if request.url.query else ""

        # Log request
        sanitized_headers = self._sanitize_headers(dict(request.headers))
        sanitized_query = self._sanitize_query(query_string)

        event_logger.log_event(
            event_type="http_request_received",
            level=EventLevel.INFO,
            message=f"{method} {path}",
            metadata={
                "correlation_id": correlation_id,
                "user_id": user_id,
                "method": method,
                "path": path,
                "query_string": sanitized_query,
                "headers": sanitized_headers
            }
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            event_logger.log_request(
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Log slow requests
            if duration_ms > 1000:
                event_logger.log_event(
                    event_type="slow_request",
                    level=EventLevel.WARNING,
                    message=f"Slow request: {method} {path} took {duration_ms:.2f}ms",
                    metadata={
                        "correlation_id": correlation_id,
                        "user_id": user_id,
                        "method": method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms
                    }
                )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            event_logger.log_error(
                error_type="request_error",
                message=f"Request failed: {method} {path}",
                exception=e,
                user_id=user_id
            )
            raise

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request"""
        # Try custom header
        if "X-User-ID" in request.headers:
            return request.headers.get("X-User-ID")

        # Try session cookie
        if "session_token" in request.cookies:
            token = request.cookies.get("session_token", "")
            if ":" in token:
                return token.split(":")[0]

        # Try Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if ":" in token:
                return token.split(":")[0]

        return "anonymous"

    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive information from headers"""
        sanitized = {}
        for key, value in headers.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_HEADERS):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = str(value)[:100]  # Limit value length
        return sanitized

    def _sanitize_query(self, query_string: str) -> str:
        """Remove sensitive parameters from query string"""
        if not query_string:
            return ""

        params = query_string.split("&")
        sanitized = []
        for param in params:
            if "=" in param:
                key, value = param.split("=", 1)
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_PARAMS):
                    sanitized.append(f"{key}=***REDACTED***")
                else:
                    sanitized.append(param)
            else:
                sanitized.append(param)

        return "&".join(sanitized)
