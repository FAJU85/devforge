#!/usr/bin/env python3
"""
Phase 1 REST API Server for DevForge QA Suite
Provides REST endpoints for database, vector DB, and storage operations
"""

import os
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.clients import DevForgeClient

# =====================================================
# Pydantic Models
# =====================================================

class TestCaseCreate(BaseModel):
    name: str
    code: str
    framework: str = 'playwright'
    source: str = 'generated'

class TestCaseResponse(BaseModel):
    id: str
    name: str
    framework: str
    source: str
    created_at: datetime

class FailureCreate(BaseModel):
    test_id: str
    error_message: str
    error_type: str
    stack_trace: Optional[str] = None
    severity: str = 'medium'

class PatternResponse(BaseModel):
    id: str
    name: str
    category: str
    confidence: float
    occurrences: int
    severity: str

class BugCreate(BaseModel):
    title: str
    description: str
    bug_type: str
    code_snippet: Optional[str] = None
    severity: str = 'medium'

class BugResponse(BaseModel):
    id: str
    title: str
    description: str
    bug_type: str
    severity: str
    status: str
    created_at: datetime

class TestEmbeddingCreate(BaseModel):
    test_ids: List[str]
    description_embeddings: List[List[float]]
    code_embeddings: List[List[float]]
    test_names: List[str]
    frameworks: List[str]

class SimilarTestsSearch(BaseModel):
    embedding: List[float]
    top_k: int = 5

class FileUpload(BaseModel):
    remote_path: str
    local_path: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, bool]
    timestamp: datetime

# =====================================================
# FastAPI Application
# =====================================================

app = FastAPI(
    title="DevForge QA Suite Phase 1 API",
    description="REST API for ML-powered QA system",
    version="1.0.0"
)

# Global client
client = DevForgeClient()

@app.on_event("startup")
async def startup_event():
    """Initialize clients on startup"""
    if not client.connect_all():
        print("Warning: Could not connect to all services")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    client.disconnect_all()

# =====================================================
# Health & Status
# =====================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of all services"""
    health = client.health_check()
    return HealthResponse(
        status="healthy" if all(health.values()) else "degraded",
        services=health,
        timestamp=datetime.now()
    )

@app.get("/status")
async def status():
    """Get detailed status"""
    return {
        "api": "running",
        "postgres": client.postgres.conn is not None,
        "milvus": "connected",
        "storage": client.storage.client is not None,
        "timestamp": datetime.now().isoformat()
    }

# =====================================================
# Test Case Management
# =====================================================

@app.post("/api/test-cases", response_model=Dict[str, str])
async def create_test_case(test_case: TestCaseCreate):
    """Create a new test case"""
    test_id = client.postgres.insert_test_case(
        name=test_case.name,
        code=test_case.code,
        framework=test_case.framework,
        source=test_case.source
    )

    if not test_id:
        raise HTTPException(status_code=400, detail="Failed to create test case")

    return {"id": test_id, "status": "created"}

@app.get("/api/test-cases/{test_id}")
async def get_test_case(test_id: str):
    """Get test case details"""
    results = client.postgres.execute(
        "SELECT * FROM test_cases WHERE id = %s",
        (test_id,)
    )

    if not results:
        raise HTTPException(status_code=404, detail="Test case not found")

    return results[0]

# =====================================================
# Test Failure Management
# =====================================================

@app.post("/api/failures", response_model=Dict[str, str])
async def report_failure(failure: FailureCreate):
    """Report a test failure"""
    failure_id = client.postgres.insert_failure(
        test_id=failure.test_id,
        error_message=failure.error_message,
        error_type=failure.error_type,
        stack_trace=failure.stack_trace,
        severity=failure.severity
    )

    if not failure_id:
        raise HTTPException(status_code=400, detail="Failed to report failure")

    return {"id": failure_id, "status": "reported"}

@app.get("/api/failures")
async def list_failures(test_id: Optional[str] = None, limit: int = 50):
    """List test failures"""
    if test_id:
        query = "SELECT * FROM test_failures WHERE test_case_id = %s ORDER BY failed_at DESC LIMIT %s"
        results = client.postgres.execute(query, (test_id, limit))
    else:
        query = "SELECT * FROM test_failures ORDER BY failed_at DESC LIMIT %s"
        results = client.postgres.execute(query, (limit,))

    return {"failures": results, "count": len(results)}

# =====================================================
# Pattern Learning
# =====================================================

@app.get("/api/patterns", response_model=Dict)
async def get_patterns(category: Optional[str] = None, min_confidence: float = 0.6):
    """Get learned patterns"""
    patterns = client.postgres.get_patterns(category=category, min_confidence=min_confidence)
    return {
        "patterns": patterns,
        "count": len(patterns),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/patterns/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get pattern details"""
    results = client.postgres.execute(
        "SELECT * FROM patterns WHERE id = %s",
        (pattern_id,)
    )

    if not results:
        raise HTTPException(status_code=404, detail="Pattern not found")

    return results[0]

# =====================================================
# Bug Management
# =====================================================

@app.post("/api/bugs", response_model=Dict[str, str])
async def report_bug(bug: BugCreate):
    """Report a bug"""
    bug_id = client.postgres.insert_bug(
        title=bug.title,
        description=bug.description,
        bug_type=bug.bug_type,
        code_snippet=bug.code_snippet,
        severity=bug.severity
    )

    if not bug_id:
        raise HTTPException(status_code=400, detail="Failed to report bug")

    return {"id": bug_id, "status": "reported"}

@app.get("/api/bugs")
async def list_bugs(status: str = 'open', limit: int = 50):
    """List bugs"""
    bugs = client.postgres.get_bugs(status=status)
    return {
        "bugs": bugs[:limit],
        "count": len(bugs),
        "status_filter": status
    }

@app.get("/api/bugs/{bug_id}")
async def get_bug(bug_id: str):
    """Get bug details"""
    results = client.postgres.execute(
        "SELECT * FROM bugs WHERE id = %s",
        (bug_id,)
    )

    if not results:
        raise HTTPException(status_code=404, detail="Bug not found")

    return results[0]

# =====================================================
# Vector Database Operations
# =====================================================

@app.post("/api/embeddings/test-cases")
async def insert_test_embeddings(data: TestEmbeddingCreate):
    """Insert test case embeddings"""
    if not client.vector_db.insert_test_embeddings(
        test_ids=data.test_ids,
        descriptions=data.description_embeddings,
        codes=data.code_embeddings,
        test_names=data.test_names,
        frameworks=data.frameworks
    ):
        raise HTTPException(status_code=400, detail="Failed to insert embeddings")

    return {"status": "inserted", "count": len(data.test_ids)}

@app.post("/api/search/similar-tests")
async def search_similar_tests(search: SimilarTestsSearch):
    """Search for similar test cases"""
    results = client.vector_db.search_similar_tests(
        embedding=search.embedding,
        top_k=search.top_k
    )

    return {
        "results": results,
        "count": len(results),
        "query_embedding_dim": len(search.embedding)
    }

@app.post("/api/search/similar-errors")
async def search_similar_errors(search: SimilarTestsSearch):
    """Search for similar error patterns"""
    results = client.vector_db.search_similar_errors(
        embedding=search.embedding,
        top_k=search.top_k
    )

    return {
        "results": results,
        "count": len(results)
    }

# =====================================================
# Storage Operations
# =====================================================

@app.post("/api/storage/upload")
async def upload_file(file_info: FileUpload):
    """Upload file to storage"""
    if not file_info.local_path or not os.path.exists(file_info.local_path):
        raise HTTPException(status_code=400, detail="Local file not found")

    if not client.storage.upload_file(file_info.local_path, file_info.remote_path):
        raise HTTPException(status_code=400, detail="Upload failed")

    return {"status": "uploaded", "path": file_info.remote_path}

@app.get("/api/storage/list")
async def list_storage_objects(prefix: str = ''):
    """List objects in storage"""
    objects = client.storage.list_objects(prefix=prefix)
    return {"objects": objects, "count": len(objects)}

@app.post("/api/storage/download")
async def download_file(file_info: FileUpload):
    """Download file from storage"""
    if not file_info.local_path:
        raise HTTPException(status_code=400, detail="Local path required")

    if not client.storage.download_file(file_info.remote_path, file_info.local_path):
        raise HTTPException(status_code=400, detail="Download failed")

    return {"status": "downloaded", "path": file_info.local_path}

# =====================================================
# Statistics & Analytics
# =====================================================

@app.get("/api/stats/overview")
async def get_overview_stats():
    """Get overview statistics"""
    stats = {}

    # Test cases count
    results = client.postgres.execute(
        "SELECT COUNT(*) as count FROM test_cases"
    )
    stats['total_test_cases'] = results[0]['count'] if results else 0

    # Failures count
    results = client.postgres.execute(
        "SELECT COUNT(*) as count FROM test_failures"
    )
    stats['total_failures'] = results[0]['count'] if results else 0

    # Patterns count
    results = client.postgres.execute(
        "SELECT COUNT(*) as count FROM patterns"
    )
    stats['learned_patterns'] = results[0]['count'] if results else 0

    # Bugs count
    results = client.postgres.execute(
        "SELECT COUNT(*) as count FROM bugs WHERE status = 'open'"
    )
    stats['open_bugs'] = results[0]['count'] if results else 0

    return {
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats/patterns")
async def get_pattern_stats():
    """Get pattern statistics"""
    results = client.postgres.execute(
        """
        SELECT category, COUNT(*) as count, AVG(confidence) as avg_confidence
        FROM patterns GROUP BY category
        """
    )

    return {"categories": results}

# =====================================================
# Root Endpoint
# =====================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "DevForge QA Suite Phase 1 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# =====================================================
# Main
# =====================================================

if __name__ == "__main__":
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8000))
    debug = os.getenv('API_DEBUG', 'true').lower() == 'true'

    print(f"Starting Phase 1 API on {host}:{port}")
    print(f"Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")

    uvicorn.run(app, host=host, port=port, debug=debug)
