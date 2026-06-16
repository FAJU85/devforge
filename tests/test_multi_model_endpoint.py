"""
Verification test for /api/generate/code-parallel.

Per CLAUDE.md: code that exists is not the same as code that works. The
parallel-multi-HF-model endpoint was written but never observed end-to-end.
This test verifies the orchestration mechanics directly against the real
FastAPI route, with the network-bound dependencies (GitHub, HF) stubbed.

What it proves:
  - The endpoint accepts N model names and returns N results (incl. duplicates).
  - Models are dispatched concurrently — total wall time is bounded by the
    slowest model, not by sum-of-all (proves asyncio.gather is doing its job).
  - An exception in one model is isolated: the failing model returns with an
    `error` field; other models still produce a `diff`.
  - The response shape matches MultiModelCodeGenerationResponse.

What it does NOT prove:
  - That the legacy `api-inference.huggingface.co` endpoint actually returns
    code. That host is DNS-blocked by this sandbox's network policy, so we
    cannot exercise it from here. It needs to be verified on the deployed Space.
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


# --- Fakes -------------------------------------------------------------------

class _FakeProvider:
    """Stand-in for HuggingFaceProvider that records calls and returns canned
    output without touching the network. Lets us control per-model behaviour
    (delay, error)."""

    # Per-model behaviour, keyed by model name. Set via _configure().
    behaviour: dict = {}

    def __init__(self, *_args, **_kwargs):
        pass

    async def generate(self, messages, model, **kwargs):
        from api.services.providers.base import ProviderResponse, MessageUsage
        cfg = _FakeProvider.behaviour.get(model, {})
        await asyncio.sleep(cfg.get("delay", 0.1))
        if cfg.get("raise"):
            raise RuntimeError(cfg["raise"])
        return ProviderResponse(
            content=cfg.get("content", f"# modified by {model}\nprint('hi')\n"),
            usage=MessageUsage(input_tokens=10, output_tokens=20, total_tokens=30),
            model=model,
            provider="huggingface",
            stop_reason="end_of_sequence",
        )


def _configure_fakes(behaviour):
    _FakeProvider.behaviour = behaviour


# --- Fixtures ----------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    # The endpoint reads get_api_key_for_provider() which requires HF_TOKEN.
    monkeypatch.setenv("HF_TOKEN", "test-token-for-orchestration-only")

    # Don't hit GitHub — return canned file content.
    fake_github = AsyncMock(return_value={
        "content": "def hello():\n    return 1\n",
        "sha": "abc123",
    })

    # Don't hit HF — return our fake provider regardless of provider name.
    with patch(
        "api.routes.generate.github_service.get_file_content",
        fake_github,
    ), patch(
        "api.routes.generate.ProviderFactory.create_provider",
        return_value=_FakeProvider(),
    ):
        from main import app
        yield TestClient(app)


# --- Tests -------------------------------------------------------------------

def test_returns_one_result_per_model_including_duplicates(client):
    """Three model names → three results, in order. Duplicate names allowed."""
    _configure_fakes({})  # all defaults

    resp = client.post("/api/generate/code-parallel", json={
        "repo_url": "https://github.com/octocat/Hello-World",
        "file_path": "README.md",
        "instruction": "rewrite the function to return 2",
        "github_token": "fake-github-token",
        "models": ["model-a", "model-b", "model-a"],  # duplicate on purpose
        "provider": "huggingface",
    })

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["models"] == ["model-a", "model-b", "model-a"]
    assert body["provider"] == "huggingface"
    assert body["original_code"] == "def hello():\n    return 1\n"
    assert len(body["results"]) == 3
    # Each result wired through generate_diff
    for r in body["results"]:
        assert r["model"] in ("model-a", "model-b")
        assert r["modified_code"].startswith("# modified by")
        assert r["diff"].startswith("--- a/README.md")
        assert r["error"] is None
        assert r["tokens_used"] == 30


def test_models_actually_run_in_parallel(client):
    """Three models each delayed 0.5s should finish in well under 1.5s.
    If they ran serially, the wall time would be >= 1.5s."""
    _configure_fakes({
        "slow-1": {"delay": 0.5},
        "slow-2": {"delay": 0.5},
        "slow-3": {"delay": 0.5},
    })

    t0 = time.perf_counter()
    resp = client.post("/api/generate/code-parallel", json={
        "repo_url": "https://github.com/octocat/Hello-World",
        "file_path": "README.md",
        "instruction": "x",
        "github_token": "fake",
        "models": ["slow-1", "slow-2", "slow-3"],
        "provider": "huggingface",
    })
    elapsed = time.perf_counter() - t0

    assert resp.status_code == 200
    assert elapsed < 1.2, (
        f"Expected parallel dispatch (~0.5s), got {elapsed:.2f}s — "
        f"models appear to be running serially"
    )


def test_one_model_error_is_isolated(client):
    """If one model raises, the others still return successful diffs."""
    _configure_fakes({
        "bad-model": {"raise": "simulated HF 503"},
        "good-model": {},
    })

    resp = client.post("/api/generate/code-parallel", json={
        "repo_url": "https://github.com/octocat/Hello-World",
        "file_path": "README.md",
        "instruction": "x",
        "github_token": "fake",
        "models": ["bad-model", "good-model"],
        "provider": "huggingface",
    })

    assert resp.status_code == 200
    body = resp.json()
    by_model = {r["model"]: r for r in body["results"]}
    assert "simulated HF 503" in by_model["bad-model"]["error"]
    assert by_model["bad-model"]["modified_code"] == ""
    assert by_model["bad-model"]["diff"] == ""
    assert by_model["good-model"]["error"] is None
    assert by_model["good-model"]["diff"].startswith("--- a/README.md")


# --- Streaming endpoint tests -----


def test_streaming_returns_ndjson_events(client):
    """Stream endpoint returns newline-delimited JSON with proper event types."""
    _configure_fakes({})  # all defaults

    resp = client.post("/api/generate/code-parallel-stream", json={
        "repo_url": "https://github.com/octocat/Hello-World",
        "file_path": "README.md",
        "instruction": "rewrite the function to return 2",
        "github_token": "fake-github-token",
        "models": ["model-a", "model-b"],
        "provider": "huggingface",
    })

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/x-ndjson"

    # Parse NDJSON response
    events = []
    for line in resp.text.strip().split('\n'):
        if line:
            import json
            events.append(json.loads(line))

    # Verify event sequence
    assert len(events) > 0
    assert events[0]["type"] == "init"
    assert events[0]["original_code"] == "def hello():\n    return 1\n"
    assert events[0]["instruction"] == "rewrite the function to return 2"
    assert events[0]["models"] == ["model-a", "model-b"]

    # Check result events
    result_events = [e for e in events if e["type"] == "result"]
    assert len(result_events) == 2
    for event in result_events:
        assert event["model"] in ("model-a", "model-b")
        assert event["modified_code"].startswith("# modified by")
        assert event["diff"].startswith("--- a/README.md")
        assert event.get("error") is None

    # Final event should be done
    assert events[-1]["type"] == "done"


def test_streaming_with_error_in_one_model(client):
    """Streaming endpoint handles errors in individual models gracefully."""
    _configure_fakes({
        "bad-model": {"raise": "simulated HF 503"},
        "good-model": {},
    })

    resp = client.post("/api/generate/code-parallel-stream", json={
        "repo_url": "https://github.com/octocat/Hello-World",
        "file_path": "README.md",
        "instruction": "x",
        "github_token": "fake",
        "models": ["bad-model", "good-model"],
        "provider": "huggingface",
    })

    assert resp.status_code == 200

    # Parse NDJSON response
    events = []
    for line in resp.text.strip().split('\n'):
        if line:
            import json
            events.append(json.loads(line))

    # Check results
    result_events = [e for e in events if e["type"] == "result"]
    by_model = {r["model"]: r for r in result_events}

    assert "simulated HF 503" in by_model["bad-model"]["error"]
    assert by_model["good-model"].get("error") is None
    assert by_model["good-model"]["diff"].startswith("--- a/README.md")
