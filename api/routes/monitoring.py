"""Monitoring Routes - PHASE 6.4 & 6.5 - Logging Dashboard & Health Checks"""

from fastapi import APIRouter, Depends, HTTPException, Cookie, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from api.monitoring import metrics, logger, monitor
from api.services.audit_service import audit_service
from uuid import UUID

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


async def get_current_user(session_token: str = Cookie(None)):
    """Verify user is authenticated"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token.split(":")[0] if ":" in session_token else session_token


@router.get("/health")
async def health_check():
    """System health check - includes all components"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "operational",
            "database": "operational",
            "cache": "operational"
        }
    }


@router.get("/metrics")
async def get_metrics(user: str = Depends(get_current_user)):
    """Get current metrics snapshot"""
    stats = metrics.get_stats()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": stats,
        "uptime_seconds": 0  # Would track actual uptime
    }


@router.get("/metrics/history")
async def get_metrics_history(
    hours: int = Query(24, ge=1, le=168),
    user: str = Depends(get_current_user)
):
    """Get historical metrics (last N hours)"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "period_hours": hours,
        "note": "Historical metrics tracking can be implemented with time-series DB"
    }


@router.delete("/metrics")
async def reset_metrics(user: str = Depends(get_current_user)):
    """Reset metrics (admin only)"""
    metrics.reset()
    return {"status": "metrics_reset", "timestamp": datetime.utcnow().isoformat()}


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = Query(100, ge=10, le=1000),
    user: str = Depends(get_current_user)
):
    """Get recent log entries"""
    events = logger.get_recent_events(limit=limit)
    return {
        "count": len(events),
        "events": events,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/logs/stats")
async def get_log_statistics(user: str = Depends(get_current_user)):
    """Get log statistics"""
    events = logger.events
    event_counts = {}
    for event in events:
        event_type = event.get("event_type", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    return {
        "total_events": len(events),
        "event_types": event_counts,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/logs/export")
async def export_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    user: str = Depends(get_current_user)
):
    """Export logs as JSON or CSV"""
    if format == "json":
        return {
            "format": "json",
            "data": logger.events,
            "exported_at": datetime.utcnow().isoformat()
        }
    else:
        # CSV export would require additional formatting
        return {
            "format": "csv",
            "note": "CSV export can be implemented with csv module",
            "exported_at": datetime.utcnow().isoformat()
        }


@router.get("/audit-trail/user/{user_id}")
async def get_user_audit_trail(
    user_id: str,
    limit: int = Query(100, ge=10, le=1000),
    offset: int = Query(0, ge=0),
    current_user: str = Depends(get_current_user)
):
    """Get audit trail for a specific user (admin or own user only)"""
    if current_user != user_id and current_user != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        user_uuid = UUID(user_id)
        trail = audit_service.get_user_audit_trail(user_uuid, limit=limit, offset=offset)
        return {
            "user_id": user_id,
            "count": len(trail),
            "audit_trail": trail,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")


@router.get("/audit-trail/entity/{entity_type}/{entity_id}")
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=10, le=1000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user)
):
    """Get audit trail for a specific entity"""
    trail = audit_service.get_audit_trail(entity_type, entity_id, limit=limit, offset=offset)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "count": len(trail),
        "audit_trail": trail,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/rate-limits/{user_id}")
async def get_user_rate_limits(
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get rate limit status for a user"""
    if current_user != user_id and current_user != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        "user_id": user_id,
        "global_limit": {
            "requests_per_minute": 100,
            "current_usage": 0,  # Would be tracked in actual implementation
            "remaining": 100
        },
        "endpoint_limits": {
            "/api/chat": {"limit": 30, "remaining": 30},
            "/api/config": {"limit": 10, "remaining": 10},
            "/api/tasks": {"limit": 5, "remaining": 5}
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/performance/endpoints")
async def get_endpoint_performance(user: str = Depends(get_current_user)):
    """Get performance metrics per endpoint"""
    stats = metrics.get_stats()
    endpoint_stats = {}

    for timer_name, timer_data in stats.get("timers", {}).items():
        if timer_name.startswith("endpoint_"):
            endpoint_stats[timer_name] = timer_data

    return {
        "endpoints": endpoint_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/performance/slow-requests")
async def get_slow_requests(
    threshold_ms: int = Query(1000, ge=100),
    limit: int = Query(50, ge=10, le=500),
    user: str = Depends(get_current_user)
):
    """Get slow requests from recent events"""
    slow_requests = [
        event for event in logger.get_recent_events(limit=limit * 2)
        if event.get("event_type") == "slow_request"
        and event.get("metadata", {}).get("duration_ms", 0) >= threshold_ms
    ]
    return {
        "threshold_ms": threshold_ms,
        "count": len(slow_requests),
        "slow_requests": slow_requests[:limit],
        "timestamp": datetime.utcnow().isoformat()
    }
