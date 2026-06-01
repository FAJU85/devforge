from unittest.mock import MagicMock, patch

import httpx
import pytest

from control_plane.nodes.execution import execution_node
from control_plane.schemas.tool_schemas import (
    BatchRequestSchema,
    BatchResponseSchema,
    ToolCallSchema,
)

_PLAN = BatchRequestSchema(
    task_id="test-task",
    calls=[ToolCallSchema(call_id="c1", tool="ping", args={"host": "1.1.1.1"})],
)

_GO_SUCCESS_PAYLOAD = {
    "task_id": "test-task",
    "results": [
        {"call_id": "c1", "tool": "ping", "ok": True, "data": {"latency_ms": 1}, "duration_ms": 1},
    ],
    "duration_ms": 1,
}


def _state(**overrides):
    base = {
        "task": "test task",
        "messages": [],
        "rag_context": "",
        "tool_plan": _PLAN,
        "tool_results": None,
        "final_answer": "",
        "error": None,
        "retry_count": 0,
    }
    base.update(overrides)
    return base


class TestExecutionNodeSuccess:
    def test_returns_validated_batch_response(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = _GO_SUCCESS_PAYLOAD

        with patch("httpx.post", return_value=mock_resp):
            result = execution_node(_state())

        assert result["error"] is None
        assert isinstance(result["tool_results"], BatchResponseSchema)
        assert result["tool_results"].results[0].ok is True

    def test_clears_previous_error_on_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = _GO_SUCCESS_PAYLOAD

        with patch("httpx.post", return_value=mock_resp):
            result = execution_node(_state(error="previous failure", retry_count=1))

        assert result["error"] is None


class TestExecutionNodeFailures:
    def test_timeout_increments_retry_and_sets_error(self):
        with patch("httpx.post", side_effect=httpx.TimeoutException("timed out")):
            result = execution_node(_state())

        assert result["retry_count"] == 1
        assert "timed out" in result["error"].lower()

    def test_http_5xx_increments_retry(self):
        err = httpx.HTTPStatusError(
            "server error",
            request=MagicMock(),
            response=MagicMock(status_code=500, text="internal server error"),
        )
        with patch("httpx.post", side_effect=err):
            result = execution_node(_state(retry_count=1))

        assert result["retry_count"] == 2
        assert "500" in result["error"]

    def test_request_error_increments_retry(self):
        with patch("httpx.post", side_effect=httpx.RequestError("connection refused")):
            result = execution_node(_state())

        assert result["retry_count"] == 1
        assert result["error"] is not None

    def test_malformed_go_response_fails_validation(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"unexpected": "shape"}  # fails Pydantic

        with patch("httpx.post", return_value=mock_resp):
            result = execution_node(_state())

        assert result["retry_count"] == 1
        assert "validation" in result["error"].lower()

    def test_no_plan_returns_error_immediately(self):
        result = execution_node(_state(tool_plan=None))

        assert result["error"] is not None
        assert "no tool_plan" in result["error"]
