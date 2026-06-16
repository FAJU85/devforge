"""
SRE/Observability middleware for FastAPI.
Provides structured logging, metrics, health checks, and request tracing.
"""

import json
import logging
import time
from datetime import datetime
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import os
import sys
import resource

# --- Structured Logging ---
class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_structured_logging(name: str = "devforge") -> logging.Logger:
    """Configure structured JSON logging."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    return logger


# --- Metrics & Health State ---
class HealthMetrics:
    """Track application health metrics."""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.total_request_time = 0.0

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def avg_request_time_ms(self) -> float:
        if self.request_count == 0:
            return 0.0
        return (self.total_request_time / self.request_count) * 1000

    def record_request(self, duration: float, is_error: bool = False):
        """Record request metrics."""
        self.request_count += 1
        self.total_request_time += duration
        if is_error:
            self.error_count += 1

    def get_health_status(self) -> dict:
        """Get full health status."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        memory_mb = usage.ru_maxrss / 1024  # RSS in MB

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(self.uptime_seconds, 2),
            "version": os.environ.get("APP_VERSION", "1.0.0"),
            "checks": {
                "memory": {
                    "healthy": memory_mb < 2000,  # 2GB threshold
                    "used_mb": round(memory_mb, 2),
                    "threshold_mb": 2000,
                },
                "requests": {
                    "healthy": self.error_count < self.request_count * 0.1 if self.request_count > 0 else True,
                    "total": self.request_count,
                    "errors": self.error_count,
                    "error_rate": round(
                        (self.error_count / self.request_count * 100) if self.request_count > 0 else 0, 2
                    ),
                },
            },
        }


metrics = HealthMetrics()
logger = setup_structured_logging()


# --- HTTP Logging Middleware ---
class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests and responses with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        start_time = time.time()

        # Log request
        logger.info(
            json.dumps({
                "type": "http_request",
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            })
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            metrics.record_request(duration, is_error=response.status_code >= 400)

            # Log response
            logger.info(
                json.dumps({
                    "type": "http_response",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                })
            )

            return response
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_request(duration, is_error=True)
            logger.error(
                json.dumps({
                    "type": "http_error",
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                })
            )
            raise


# --- Prometheus Metrics Format ---
def generate_prometheus_metrics() -> str:
    """Generate metrics in Prometheus exposition format."""
    health = metrics.get_health_status()
    usage = resource.getrusage(resource.RUSAGE_SELF)

    lines = [
        "# HELP devforge_uptime_seconds Application uptime in seconds",
        "# TYPE devforge_uptime_seconds gauge",
        f'devforge_uptime_seconds {health["uptime_seconds"]}',
        "",
        "# HELP devforge_requests_total Total HTTP requests processed",
        "# TYPE devforge_requests_total counter",
        f'devforge_requests_total {metrics.request_count}',
        "",
        "# HELP devforge_errors_total Total HTTP errors",
        "# TYPE devforge_errors_total counter",
        f'devforge_errors_total {metrics.error_count}',
        "",
        "# HELP devforge_request_duration_ms Average request duration in milliseconds",
        "# TYPE devforge_request_duration_ms gauge",
        f'devforge_request_duration_ms {metrics.avg_request_time_ms}',
        "",
        "# HELP devforge_memory_usage_mb Process memory usage in MB",
        "# TYPE devforge_memory_usage_mb gauge",
        f'devforge_memory_usage_mb {health["checks"]["memory"]["used_mb"]}',
        "",
        "# HELP devforge_user_cpu_time_seconds User CPU time in seconds",
        "# TYPE devforge_user_cpu_time_seconds gauge",
        f'devforge_user_cpu_time_seconds {usage.ru_utime}',
    ]

    return "\n".join(lines) + "\n"
