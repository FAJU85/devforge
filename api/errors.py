#!/usr/bin/env python3
"""
Error Handling - Standardized error responses and exception handling
"""

from typing import Optional, Dict, Any
from enum import Enum
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """Standard error codes"""
    # Auth errors (4xx)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Validation errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Resource errors (4xx)
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"

    # Provider errors
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_API_KEY = "INVALID_API_KEY"


class DevForgeError(Exception):
    """Base exception for DevForge"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_response(self) -> Dict[str, Any]:
        """Convert to HTTP response"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details
            }
        }

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_response()
        )


class AuthenticationError(DevForgeError):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(DevForgeError):
    """Authorization failed"""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationError(DevForgeError):
    """Input validation failed"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            code=ErrorCode.INVALID_INPUT,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field} if field else {}
        )


class NotFoundError(DevForgeError):
    """Resource not found"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource_type} not found: {resource_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ConflictError(DevForgeError):
    """Resource conflict"""

    def __init__(self, message: str, conflict_field: Optional[str] = None):
        super().__init__(
            code=ErrorCode.CONFLICT,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details={"conflict_field": conflict_field} if conflict_field else {}
        )


class RateLimitError(DevForgeError):
    """Rate limit exceeded"""

    def __init__(self, retry_after: int):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Rate limit exceeded. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after_seconds": retry_after}
        )


class ProviderError(DevForgeError):
    """LLM provider error"""

    def __init__(
        self,
        provider: str,
        message: str,
        code: ErrorCode = ErrorCode.PROVIDER_ERROR
    ):
        super().__init__(
            code=code,
            message=f"{provider} error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"provider": provider}
        )


class InvalidAPIKeyError(DevForgeError):
    """Invalid API key"""

    def __init__(self, provider: str):
        super().__init__(
            code=ErrorCode.INVALID_API_KEY,
            message=f"Invalid API key for {provider}",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"provider": provider}
        )


class ServiceUnavailableError(DevForgeError):
    """Service temporarily unavailable"""

    def __init__(self, service: str, message: Optional[str] = None):
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message or f"{service} is temporarily unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class TimeoutError(DevForgeError):
    """Operation timeout"""

    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            code=ErrorCode.TIMEOUT,
            message=f"{operation} timed out after {timeout_seconds} seconds",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details={"operation": operation, "timeout_seconds": timeout_seconds}
        )


# Error handling utilities
def safe_operation(func):
    """Decorator for safe operation handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DevForgeError:
            raise
        except Exception as e:
            # Log unexpected error
            raise DevForgeError(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"error_type": type(e).__name__}
            )
    return wrapper
