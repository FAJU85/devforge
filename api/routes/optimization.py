#!/usr/bin/env python3
"""
Optimization Routes - Phase 8
Endpoints for caching, monitoring, and bug detection
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import hashlib
import json

# Import optimization services
from api.services.cache_service import cache_service, api_response_cache, model_inference_cache, db_query_cache
from api.services.prometheus_service import prometheus_metrics
from api.services.bug_detection_service import bug_detection_service

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


class CacheStatsResponse(BaseModel):
    """Cache statistics response"""
    api_response_cache_hits: float
    model_inference_cache_hits: float
    db_query_cache_hits: float
    redis_enabled: bool
    redis_memory_mb: float
    in_memory_size: int


class MetricsResponse(BaseModel):
    """Metrics response"""
    http_requests: Dict[str, int]
    error_rate: float
    cache_hit_rate: Dict[str, float]
    active_users: int
    active_conversations: int
    latency_stats: Dict[str, float]


class BugAnalysisRequest(BaseModel):
    """Bug analysis request"""
    code_snippet: str
    language: str = "python"
    context: Optional[str] = None


class BugAnalysisResponse(BaseModel):
    """Bug analysis response"""
    bugs_found: int
    severity: str
    confidence_score: float
    suggestions: List[str]
    processing_time_ms: float
    bugs: List[Dict[str, Any]]


class ClearCacheRequest(BaseModel):
    """Clear cache request"""
    namespace: Optional[str] = None
    pattern: Optional[str] = None


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_statistics():
    """Get cache statistics and metrics"""
    try:
        cache_stats = await cache_service.get_stats()

        redis_memory_mb = cache_stats.get("redis_memory_bytes", 0) / (1024 * 1024)

        return CacheStatsResponse(
            api_response_cache_hits=api_response_cache.get_hit_rate(),
            model_inference_cache_hits=model_inference_cache.get_hit_rate(),
            db_query_cache_hits=db_query_cache.get_hit_rate(),
            redis_enabled=cache_stats.get("redis_enabled", False),
            redis_memory_mb=redis_memory_mb,
            in_memory_size=cache_stats.get("in_memory_size", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(request: ClearCacheRequest):
    """Clear cache entries"""
    try:
        cleared = 0

        if request.namespace:
            # Clear specific namespace
            cleared = await cache_service.delete_pattern(f"{request.namespace}:*")
        elif request.pattern:
            # Clear specific pattern
            cleared = await cache_service.delete_pattern(request.pattern)
        else:
            # Clear all cache
            await cache_service.clear()
            cleared = -1  # Indicate full clear

        return {
            "message": "Cache cleared successfully",
            "entries_cleared": cleared
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get current metrics"""
    try:
        metrics = prometheus_metrics.get_metrics()
        latency_stats = prometheus_metrics.get_latency_stats()

        return MetricsResponse(
            http_requests=metrics.get("http_requests", {}),
            error_rate=metrics.get("error_rate", 0),
            cache_hit_rate={
                "api": api_response_cache.get_hit_rate(),
                "inference": model_inference_cache.get_hit_rate(),
                "database": db_query_cache.get_hit_rate(),
            },
            active_users=metrics.get("active_users", 0),
            active_conversations=metrics.get("active_conversations", 0),
            latency_stats=latency_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get metrics in Prometheus format"""
    try:
        return prometheus_metrics.export_prometheus_format()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")


@router.post("/analyze-bugs", response_model=BugAnalysisResponse)
async def analyze_code_for_bugs(request: BugAnalysisRequest):
    """Analyze code for potential bugs using fine-tuned model"""
    try:
        analysis = bug_detection_service.analyze_code(
            code_snippet=request.code_snippet,
            language=request.language,
            context=request.context
        )

        return BugAnalysisResponse(
            bugs_found=len(analysis.bugs_found),
            severity=analysis.severity,
            confidence_score=analysis.confidence_score,
            suggestions=analysis.suggestions,
            processing_time_ms=analysis.processing_time_ms,
            bugs=analysis.bugs_found
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing code: {str(e)}")


@router.post("/bug-analysis/{analysis_id}/feedback")
async def log_bug_analysis_feedback(
    analysis_id: str,
    feedback_correct: bool = Query(...),
    notes: Optional[str] = None
):
    """Log user feedback on bug analysis"""
    try:
        success = bug_detection_service.log_user_feedback(
            analysis_id=analysis_id,
            feedback_correct=feedback_correct,
            user_notes=notes
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to log feedback")

        return {
            "message": "Feedback recorded successfully",
            "analysis_id": analysis_id,
            "feedback": feedback_correct
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging feedback: {str(e)}")


@router.get("/analysis-stats")
async def get_analysis_statistics():
    """Get bug detection analysis statistics"""
    try:
        stats = bug_detection_service.get_analysis_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")


@router.get("/health")
async def optimization_health():
    """Health check for optimization services"""
    try:
        cache_stats = await cache_service.get_stats()
        metrics = prometheus_metrics.get_metrics()

        return {
            "status": "healthy",
            "services": {
                "cache": "operational" if cache_stats else "degraded",
                "metrics": "operational" if metrics else "degraded",
                "bug_detection": "operational"
            },
            "cache_stats": cache_stats,
            "error_rate": metrics.get("error_rate", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


