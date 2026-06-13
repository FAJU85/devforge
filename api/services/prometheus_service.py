#!/usr/bin/env python3
"""
Prometheus Metrics Service - Phase 8.5
Metrics collection and monitoring for DevForge
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus metrics collection"""

    def __init__(self):
        self.metrics = {
            "http_requests_total": {},
            "http_request_duration_seconds": [],
            "inference_requests_total": {},
            "cache_hits_total": {},
            "cache_misses_total": {},
            "db_queries_total": {},
            "db_query_duration_seconds": [],
            "errors_total": {},
            "active_users": 0,
            "active_conversations": 0,
        }
        self.request_count = 0
        self.error_count = 0

    def record_http_request(self, method: str, endpoint: str, status: int, duration_ms: float):
        """Record HTTP request metric"""
        try:
            key = f"{method}:{endpoint}:{status}"
            if key not in self.metrics["http_requests_total"]:
                self.metrics["http_requests_total"][key] = 0
            self.metrics["http_requests_total"][key] += 1

            self.metrics["http_request_duration_seconds"].append({
                "endpoint": endpoint,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Keep only last 1000 measurements
            if len(self.metrics["http_request_duration_seconds"]) > 1000:
                self.metrics["http_request_duration_seconds"].pop(0)

            self.request_count += 1

            if status >= 400:
                if status not in self.metrics["errors_total"]:
                    self.metrics["errors_total"][status] = 0
                self.metrics["errors_total"][status] += 1
                self.error_count += 1

        except Exception as e:
            logger.error(f"Error recording HTTP request metric: {e}")

    def record_inference_request(self, model: str, status: str, duration_ms: float):
        """Record inference request metric"""
        try:
            key = f"{model}:{status}"
            if key not in self.metrics["inference_requests_total"]:
                self.metrics["inference_requests_total"][key] = 0
            self.metrics["inference_requests_total"][key] += 1
        except Exception as e:
            logger.error(f"Error recording inference metric: {e}")

    def record_cache_hit(self, layer: str):
        """Record cache hit"""
        try:
            if layer not in self.metrics["cache_hits_total"]:
                self.metrics["cache_hits_total"][layer] = 0
            self.metrics["cache_hits_total"][layer] += 1
        except Exception as e:
            logger.error(f"Error recording cache hit: {e}")

    def record_cache_miss(self, layer: str):
        """Record cache miss"""
        try:
            if layer not in self.metrics["cache_misses_total"]:
                self.metrics["cache_misses_total"][layer] = 0
            self.metrics["cache_misses_total"][layer] += 1
        except Exception as e:
            logger.error(f"Error recording cache miss: {e}")

    def record_db_query(self, query_type: str, duration_ms: float):
        """Record database query metric"""
        try:
            key = query_type
            if key not in self.metrics["db_queries_total"]:
                self.metrics["db_queries_total"][key] = 0
            self.metrics["db_queries_total"][key] += 1

            self.metrics["db_query_duration_seconds"].append({
                "query_type": query_type,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat()
            })

            if len(self.metrics["db_query_duration_seconds"]) > 1000:
                self.metrics["db_query_duration_seconds"].pop(0)

        except Exception as e:
            logger.error(f"Error recording DB query metric: {e}")

    def set_active_users(self, count: int):
        """Set active user count"""
        try:
            self.metrics["active_users"] = count
        except Exception as e:
            logger.error(f"Error setting active users: {e}")

    def set_active_conversations(self, count: int):
        """Set active conversation count"""
        try:
            self.metrics["active_conversations"] = count
        except Exception as e:
            logger.error(f"Error setting active conversations: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        try:
            return {
                "http_requests": self.metrics["http_requests_total"],
                "http_errors": self.metrics["errors_total"],
                "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
                "cache_hits": self.metrics["cache_hits_total"],
                "cache_misses": self.metrics["cache_misses_total"],
                "db_queries": self.metrics["db_queries_total"],
                "active_users": self.metrics["active_users"],
                "active_conversations": self.metrics["active_conversations"],
                "total_requests": self.request_count,
                "total_errors": self.error_count,
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

    def get_latency_stats(self) -> Dict[str, Any]:
        """Get latency statistics"""
        try:
            if not self.metrics["http_request_duration_seconds"]:
                return {}

            durations = [m["duration_ms"] for m in self.metrics["http_request_duration_seconds"]]
            durations.sort()

            return {
                "p50_ms": durations[int(len(durations) * 0.5)],
                "p95_ms": durations[int(len(durations) * 0.95)],
                "p99_ms": durations[int(len(durations) * 0.99)],
                "min_ms": min(durations),
                "max_ms": max(durations),
                "avg_ms": sum(durations) / len(durations),
                "count": len(durations),
            }
        except Exception as e:
            logger.error(f"Error calculating latency stats: {e}")
            return {}

    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        try:
            lines = []

            for key, value in self.metrics["http_requests_total"].items():
                method, endpoint, status = key.split(":")
                lines.append(f'http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {value}')

            for layer, count in self.metrics["cache_hits_total"].items():
                lines.append(f'cache_hits_total{{layer="{layer}"}} {count}')

            for layer, count in self.metrics["cache_misses_total"].items():
                lines.append(f'cache_misses_total{{layer="{layer}"}} {count}')

            lines.append(f'active_users {self.metrics["active_users"]}')
            lines.append(f'active_conversations {self.metrics["active_conversations"]}')

            return "\n".join(lines) + "\n"
        except Exception as e:
            logger.error(f"Error exporting Prometheus format: {e}")
            return ""


prometheus_metrics = PrometheusMetrics()
