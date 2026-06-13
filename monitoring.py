"""Metrics collection and health monitoring for canary rollout."""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict


@dataclass
class MetricSnapshot:
    """A snapshot of metrics at a point in time."""
    timestamp: datetime
    api_latency_p50_ms: float
    api_latency_p95_ms: float
    api_latency_p99_ms: float
    request_count: int
    error_count: int
    error_rate_percent: float
    db_query_count: int
    db_avg_latency_ms: float
    db_connection_pool_utilization_percent: float
    conversations_created: int
    messages_created: int
    users_active: int
    data_consistency_match_percent: float
    feature_flag_enabled_percent: float


class MetricsCollector:
    """Collect and aggregate metrics from the application."""

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.request_times: deque = deque(maxlen=10000)
        self.error_times: deque = deque(maxlen=10000)
        self.db_query_times: deque = deque(maxlen=10000)
        self.snapshots: List[MetricSnapshot] = []
        self.last_snapshot_time = time.time()

    def record_request(self, latency_ms: float, error: bool = False):
        """Record an API request."""
        now = time.time()
        self.request_times.append((now, latency_ms))
        if error:
            self.error_times.append(now)

    def record_db_query(self, latency_ms: float):
        """Record a database query."""
        now = time.time()
        self.db_query_times.append((now, latency_ms))

    def get_current_metrics(self) -> MetricSnapshot:
        """Calculate current metrics."""
        now = time.time()
        window_start = now - (self.window_minutes * 60)

        # Filter to current window
        requests_in_window = [
            (t, lat) for t, lat in self.request_times
            if t > window_start
        ]
        errors_in_window = [
            t for t in self.error_times
            if t > window_start
        ]
        queries_in_window = [
            (t, lat) for t, lat in self.db_query_times
            if t > window_start
        ]

        # Calculate percentiles
        if requests_in_window:
            latencies = sorted([lat for _, lat in requests_in_window])
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        error_rate = (
            (len(errors_in_window) / len(requests_in_window) * 100)
            if requests_in_window else 0
        )

        db_avg_latency = (
            sum(lat for _, lat in queries_in_window) / len(queries_in_window)
            if queries_in_window else 0
        )

        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            api_latency_p50_ms=p50,
            api_latency_p95_ms=p95,
            api_latency_p99_ms=p99,
            request_count=len(requests_in_window),
            error_count=len(errors_in_window),
            error_rate_percent=error_rate,
            db_query_count=len(queries_in_window),
            db_avg_latency_ms=db_avg_latency,
            db_connection_pool_utilization_percent=0,  # TODO: from DB
            conversations_created=0,  # TODO: from DB
            messages_created=0,  # TODO: from DB
            users_active=0,  # TODO: from API
            data_consistency_match_percent=100,  # TODO: compare DB vs localStorage
            feature_flag_enabled_percent=0,  # TODO: from feature flags
        )

        self.snapshots.append(snapshot)
        return snapshot

    def get_snapshot_dict(self, snapshot: Optional[MetricSnapshot] = None) -> Dict:
        """Get metrics as dictionary."""
        if snapshot is None:
            snapshot = self.get_current_metrics()

        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "api_latency_p50_ms": round(snapshot.api_latency_p50_ms, 2),
            "api_latency_p95_ms": round(snapshot.api_latency_p95_ms, 2),
            "api_latency_p99_ms": round(snapshot.api_latency_p99_ms, 2),
            "request_count": snapshot.request_count,
            "error_count": snapshot.error_count,
            "error_rate_percent": round(snapshot.error_rate_percent, 2),
            "db_query_count": snapshot.db_query_count,
            "db_avg_latency_ms": round(snapshot.db_avg_latency_ms, 2),
            "db_connection_pool_utilization_percent": snapshot.db_connection_pool_utilization_percent,
            "data_consistency_match_percent": snapshot.data_consistency_match_percent,
            "feature_flag_enabled_percent": snapshot.feature_flag_enabled_percent,
        }

    def export_metrics(self, filepath: str):
        """Export metrics to JSON for analysis."""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "snapshots": [self.get_snapshot_dict(s) for s in self.snapshots[-288:]],  # Last 24h (5-min intervals)
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)


class HealthCheck:
    """Perform health checks on the system."""

    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.last_check_time = time.time()
        self.health_history = deque(maxlen=1000)

    def check_api_health(self) -> Dict[str, bool]:
        """Check API health."""
        snapshot = self.metrics.get_current_metrics()
        return {
            "api_responding": snapshot.request_count > 0,
            "api_latency_ok": snapshot.api_latency_p95_ms < 500,
            "error_rate_ok": snapshot.error_rate_percent < 1,
        }

    def check_db_health(self) -> Dict[str, bool]:
        """Check database health."""
        snapshot = self.metrics.get_current_metrics()
        return {
            "db_responding": snapshot.db_query_count > 0,
            "db_latency_ok": snapshot.db_avg_latency_ms < 100,
            "db_pool_ok": snapshot.db_connection_pool_utilization_percent < 90,
        }

    def check_data_consistency(self) -> Dict[str, bool]:
        """Check data consistency between DB and localStorage."""
        snapshot = self.metrics.get_current_metrics()
        return {
            "data_consistent": snapshot.data_consistency_match_percent > 98,
            "no_data_loss": snapshot.data_consistency_match_percent > 99.5,
        }

    def overall_health(self) -> Dict:
        """Get overall system health."""
        api_health = self.check_api_health()
        db_health = self.check_db_health()
        data_health = self.check_data_consistency()

        all_healthy = all(
            list(api_health.values()) +
            list(db_health.values()) +
            list(data_health.values())
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_healthy": all_healthy,
            "api": api_health,
            "database": db_health,
            "data": data_health,
        }


# Global metrics collector
metrics = MetricsCollector(window_minutes=5)
health = HealthCheck(metrics)
