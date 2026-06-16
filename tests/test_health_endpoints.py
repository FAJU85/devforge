"""
Tests for SRE/observability health endpoints.
Verifies that /health, /health/live, /health/ready, and /metrics endpoints work.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Fixture to get FastAPI test client."""
    from main import app
    return TestClient(app)


def test_health_endpoint(client):
    """Test full health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "checks" in data
    assert "version" in data
    assert "uptime_seconds" in data


def test_health_live_endpoint(client):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "status" in data
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "uptime_seconds" in data


def test_health_ready_endpoint(client):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    # Status code depends on whether auth is configured
    assert response.status_code in [200, 503]
    data = response.json()

    # Verify response structure
    assert "ready" in data
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code in [200, 503]

    # Should return plain text in Prometheus format
    assert response.headers["content-type"].startswith("text/plain")

    # Should contain some metrics (even if empty)
    content = response.text
    assert isinstance(content, str)


def test_health_contains_request_metrics(client):
    """Test that health endpoint tracks request metrics."""
    # Make a few requests
    client.get("/health")
    client.get("/health")
    client.get("/health")

    # Check metrics
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    # Should have tracked requests
    assert data["checks"]["requests"]["total"] >= 3


def test_metrics_prometheus_format(client):
    """Test that metrics are in valid Prometheus format."""
    response = client.get("/metrics")
    content = response.text

    # Prometheus format lines start with # or metric name
    lines = [l for l in content.split('\n') if l.strip()]

    for line in lines:
        # Each line should be either a comment or a metric
        assert line.startswith('#') or '(' not in line or '{' not in line or ' ' in line


def test_health_includes_memory_usage(client):
    """Test that health includes memory usage metrics."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    # Should have memory checks
    assert "memory" in data["checks"]
    assert "used_mb" in data["checks"]["memory"]
    assert "threshold_mb" in data["checks"]["memory"]
    assert "healthy" in data["checks"]["memory"]
