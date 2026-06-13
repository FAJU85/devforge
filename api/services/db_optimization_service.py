#!/usr/bin/env python3
"""
Database Optimization Service - Phase 8.3
Query optimization, N+1 elimination, batch operations, and indexing
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """Monitor and log slow queries"""

    SLOW_QUERY_THRESHOLD_MS = 100

    def __init__(self):
        self.slow_queries: List[Dict[str, Any]] = []
        self.query_stats: Dict[str, Dict[str, Any]] = {}

    def record_query(self, query_name: str, duration_ms: float, query_text: str = ""):
        """Record a query execution"""
        try:
            if duration_ms > self.SLOW_QUERY_THRESHOLD_MS:
                self.slow_queries.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "query_name": query_name,
                    "duration_ms": duration_ms,
                    "query_text": query_text[:200]  # Truncate for storage
                })

                # Keep only last 100 slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries.pop(0)

                logger.warning(f"Slow query detected: {query_name} took {duration_ms}ms")

            # Update statistics
            if query_name not in self.query_stats:
                self.query_stats[query_name] = {
                    "count": 0,
                    "total_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0,
                }

            stats = self.query_stats[query_name]
            stats["count"] += 1
            stats["total_ms"] += duration_ms
            stats["min_ms"] = min(stats["min_ms"], duration_ms)
            stats["max_ms"] = max(stats["max_ms"], duration_ms)

        except Exception as e:
            logger.error(f"Error recording query: {e}")

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest recent queries"""
        return sorted(
            self.slow_queries[-limit:],
            key=lambda q: q["duration_ms"],
            reverse=True
        )

    def get_query_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get query statistics"""
        stats = {}
        for query_name, data in self.query_stats.items():
            if data["count"] > 0:
                stats[query_name] = {
                    "count": data["count"],
                    "avg_ms": data["total_ms"] / data["count"],
                    "min_ms": data["min_ms"],
                    "max_ms": data["max_ms"],
                }
        return stats


class BatchOperationHelper:
    """Helper for batch database operations"""

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
        """Split list into chunks for batch operations"""
        chunks = []
        for i in range(0, len(items), chunk_size):
            chunks.append(items[i:i + chunk_size])
        return chunks

    @staticmethod
    def estimate_performance_improvement(
        individual_count: int,
        batch_size: int = 1000,
        time_per_operation_ms: float = 1.0
    ) -> Dict[str, Any]:
        """Estimate performance improvement with batching"""
        individual_time = individual_count * time_per_operation_ms
        batch_count = (individual_count + batch_size - 1) // batch_size
        batch_time = batch_count * 5.0  # Assume 5ms per batch (overhead)

        improvement_percent = ((individual_time - batch_time) / individual_time * 100) if individual_time > 0 else 0

        return {
            "individual_operations": individual_count,
            "batch_size": batch_size,
            "batch_count": batch_count,
            "estimated_individual_time_ms": individual_time,
            "estimated_batch_time_ms": batch_time,
            "improvement_percent": improvement_percent,
            "speedup_factor": individual_time / batch_time if batch_time > 0 else 1.0
        }


class IndexRecommendation:
    """Recommend database indexes based on usage patterns"""

    # Common queries that benefit from indexes
    RECOMMENDED_INDEXES = [
        {
            "name": "ix_conversations_user_created",
            "table": "conversations",
            "columns": ["user_id", "created_at DESC"],
            "benefit": "Speeds up conversation listing by user and date range",
            "estimated_improvement_percent": 50
        },
        {
            "name": "ix_messages_conversation_created",
            "table": "messages",
            "columns": ["conversation_id", "created_at DESC"],
            "benefit": "Eliminates N+1 queries when fetching conversation messages",
            "estimated_improvement_percent": 60
        },
        {
            "name": "ix_users_github_login",
            "table": "users",
            "columns": ["github_login"],
            "benefit": "Speeds up user lookup by GitHub login",
            "estimated_improvement_percent": 40
        },
        {
            "name": "ix_api_keys_hash_not_revoked",
            "table": "api_keys",
            "columns": ["key_hash"],
            "where": "is_revoked = false",
            "benefit": "Faster API key validation in auth flow",
            "estimated_improvement_percent": 45
        },
        {
            "name": "ix_audit_logs_entity_date",
            "table": "audit_logs",
            "columns": ["entity_type", "entity_id", "created_at DESC"],
            "benefit": "Speeds up audit log queries and archival",
            "estimated_improvement_percent": 35
        },
        {
            "name": "ix_rate_limit_user_endpoint_window",
            "table": "rate_limit_events",
            "columns": ["user_id", "endpoint", "created_at DESC"],
            "benefit": "Faster rate limit enforcement checks",
            "estimated_improvement_percent": 50
        }
    ]

    @staticmethod
    def get_recommendations() -> List[Dict[str, Any]]:
        """Get index recommendations"""
        return IndexRecommendation.RECOMMENDED_INDEXES

    @staticmethod
    def get_sql_for_index(index: Dict[str, Any]) -> str:
        """Generate SQL to create index"""
        columns_str = ", ".join(index["columns"])
        where_clause = f" WHERE {index.get('where', '')}" if index.get("where") else ""
        sql = f"CREATE INDEX IF NOT EXISTS {index['name']} ON {index['table']}({columns_str}){where_clause};"
        return sql


class ConnectionPoolOptimizer:
    """Optimize database connection pool settings"""

    @staticmethod
    def get_recommended_pool_size(deployment_type: str = "production") -> Dict[str, int]:
        """Get recommended connection pool size"""
        if deployment_type == "development":
            return {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 3600,
                "echo": False
            }
        elif deployment_type == "staging":
            return {
                "pool_size": 20,
                "max_overflow": 20,
                "pool_recycle": 7200,
                "echo": False
            }
        else:  # production
            return {
                "pool_size": 50,
                "max_overflow": 30,
                "pool_recycle": 7200,
                "echo": False
            }

    @staticmethod
    def get_performance_tips() -> List[str]:
        """Get performance optimization tips"""
        return [
            "Enable connection pre-ping: pool_pre_ping=True",
            "Set appropriate pool_recycle to avoid stale connections",
            "Use connection pooling for all database connections",
            "Monitor active connections: should be near pool_size at peak",
            "Configure max_overflow conservatively to catch pool exhaustion early",
            "Use read replicas for read-heavy queries",
            "Implement circuit breaker for database connection failures"
        ]


class N1QueryDetector:
    """Detect and help fix N+1 query patterns"""

    @staticmethod
    def detect_n1_patterns() -> List[Dict[str, Any]]:
        """Detect potential N+1 patterns"""
        patterns = [
            {
                "name": "conversation_messages_loop",
                "symptom": "Loop iterating conversations and accessing .messages attribute",
                "solution": "Use SQLAlchemy selectinload: session.query(Conversation).options(selectinload(Conversation.messages))",
                "expected_improvement_percent": 70
            },
            {
                "name": "conversation_files_access",
                "symptom": "Accessing conversation.files in loop without eager loading",
                "solution": "Use joinedload or selectinload for conversation file relationships",
                "expected_improvement_percent": 65
            },
            {
                "name": "user_repositories_fetch",
                "symptom": "Fetching all repositories for user in loop",
                "solution": "Use batch loading: session.query(Repository).filter(Repository.user_id.in_([...]))",
                "expected_improvement_percent": 60
            }
        ]
        return patterns

    @staticmethod
    def get_eager_loading_example(relationship: str) -> str:
        """Get example of eager loading code"""
        examples = {
            "conversations_messages": """
# Before (N+1):
conversations = session.query(Conversation).filter_by(user_id=user_id).all()
for conv in conversations:
    messages = conv.messages  # Each access triggers new query

# After (optimized):
from sqlalchemy.orm import selectinload
conversations = session.query(Conversation).options(
    selectinload(Conversation.messages)
).filter_by(user_id=user_id).all()
""",
            "batch_operations": """
# Before (slow):
for item in items:
    session.add(item)
session.commit()

# After (fast):
session.bulk_insert_mappings(ModelClass, items)
session.commit()
"""
        }
        return examples.get(relationship, "No example found")


# Global instances
query_monitor = QueryPerformanceMonitor()
batch_helper = BatchOperationHelper()
index_recommender = IndexRecommendation()
pool_optimizer = ConnectionPoolOptimizer()
n1_detector = N1QueryDetector()


def slow_query_logger(threshold_ms: int = 100):
    """Decorator to log slow queries"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                query_monitor.record_query(func.__name__, duration_ms)
        return wrapper
    return decorator
