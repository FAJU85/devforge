#!/usr/bin/env python3
"""
Monitoring Module - Production monitoring and observability
Handles metrics, logging, and performance tracking
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json


class EventLevel(str, Enum):
    """Event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricsCollector:
    """Collects application metrics"""

    def __init__(self):
        """Initialize metrics collector"""
        self.counters: Dict[str, int] = {}
        self.timers: Dict[str, List[float]] = {}
        self.gauges: Dict[str, float] = {}

    def increment_counter(self, name: str, amount: int = 1):
        """Increment counter metric"""
        if name not in self.counters:
            self.counters[name] = 0
        self.counters[name] += amount

    def record_timer(self, name: str, duration_ms: float):
        """Record timer metric"""
        if name not in self.timers:
            self.timers[name] = []
        self.timers[name].append(duration_ms)

    def set_gauge(self, name: str, value: float):
        """Set gauge metric"""
        self.gauges[name] = value

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics"""
        stats = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {}
        }

        for name, values in self.timers.items():
            if values:
                stats["timers"][name] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
                }

        return stats

    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()


class EventLogger:
    """Logs events for debugging and auditing"""

    def __init__(self, name: str = "devforge"):
        """Initialize event logger"""
        self.name = name
        self.events: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(name)

        # Setup logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_event(
        self,
        event_type: str,
        level: EventLevel,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "level": level.value,
            "message": message,
            "metadata": metadata or {}
        }

        self.events.append(event)

        # Also log to Python logger
        log_func = {
            EventLevel.DEBUG: self.logger.debug,
            EventLevel.INFO: self.logger.info,
            EventLevel.WARNING: self.logger.warning,
            EventLevel.ERROR: self.logger.error,
            EventLevel.CRITICAL: self.logger.critical,
        }[level]

        log_func(f"{event_type}: {message}")

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[int] = None
    ):
        """Log HTTP request"""
        self.log_event(
            "http_request",
            EventLevel.INFO,
            f"{method} {path} - {status_code}",
            {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id
            }
        )

    def log_error(
        self,
        error_type: str,
        message: str,
        exception: Optional[Exception] = None,
        user_id: Optional[int] = None
    ):
        """Log error event"""
        metadata = {
            "error_type": error_type,
            "user_id": user_id
        }

        if exception:
            metadata["exception"] = str(exception)
            metadata["exception_type"] = type(exception).__name__

        self.log_event(
            "error",
            EventLevel.ERROR,
            message,
            metadata
        )

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self.events[-limit:]

    def export_events(self) -> str:
        """Export events as JSON"""
        return json.dumps(self.events, indent=2)


class PerformanceMonitor:
    """Monitors performance metrics"""

    def __init__(self, metrics: MetricsCollector, logger: EventLogger):
        """Initialize performance monitor"""
        self.metrics = metrics
        self.logger = logger

    def measure_operation(self, operation_name: str):
        """Context manager for measuring operation time"""
        class OperationTimer:
            def __init__(self, monitor, name):
                self.monitor = monitor
                self.name = name
                self.start_time = None

            def __enter__(self):
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration_ms = (time.time() - self.start_time) * 1000
                self.monitor.metrics.record_timer(self.name, duration_ms)

                if duration_ms > 1000:  # Log slow operations
                    self.monitor.logger.log_event(
                        "slow_operation",
                        EventLevel.WARNING,
                        f"{self.name} took {duration_ms:.2f}ms",
                        {"operation": self.name, "duration_ms": duration_ms}
                    )

        return OperationTimer(self, operation_name)


# Global instances
metrics = MetricsCollector()
logger = EventLogger("devforge")
monitor = PerformanceMonitor(metrics, logger)
