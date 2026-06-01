import pytest
from pydantic import ValidationError

from control_plane.schemas.tool_schemas import (
    BatchRequestSchema,
    BatchResponseSchema,
    ToolCallSchema,
    ToolResultSchema,
)


class TestBatchRequestSchema:
    def test_valid_single_call(self):
        req = BatchRequestSchema(
            task_id="t1",
            calls=[ToolCallSchema(call_id="c1", tool="http_fetch", args={"url": "https://example.com"})],
        )
        assert req.task_id == "t1"
        assert len(req.calls) == 1

    def test_empty_calls_rejected(self):
        with pytest.raises(ValidationError):
            BatchRequestSchema(task_id="t1", calls=[])

    def test_unknown_tool_rejected(self):
        with pytest.raises(ValidationError):
            ToolCallSchema(call_id="c1", tool="nonexistent_tool", args={})

    def test_max_calls_boundary(self):
        calls = [
            ToolCallSchema(call_id=f"c{i}", tool="ping", args={"host": "1.1.1.1"})
            for i in range(20)
        ]
        req = BatchRequestSchema(task_id="t1", calls=calls)
        assert len(req.calls) == 20

    def test_exceeds_max_calls_rejected(self):
        calls = [
            ToolCallSchema(call_id=f"c{i}", tool="ping", args={"host": "1.1.1.1"})
            for i in range(21)
        ]
        with pytest.raises(ValidationError):
            BatchRequestSchema(task_id="t1", calls=calls)

    def test_model_dump_matches_go_schema(self):
        req = BatchRequestSchema(
            task_id="abc",
            calls=[ToolCallSchema(call_id="c1", tool="http_fetch", args={"url": "https://x.com"})],
        )
        d = req.model_dump()
        assert d["task_id"] == "abc"
        assert d["calls"][0]["tool"] == "http_fetch"
        assert "args" in d["calls"][0]


class TestBatchResponseSchema:
    def test_validates_go_payload(self):
        payload = {
            "task_id": "t1",
            "results": [
                {
                    "call_id": "c1", "tool": "http_fetch", "ok": True,
                    "data": {"status_code": 200, "body": "hello", "content_type": "text/html", "url": "x"},
                    "duration_ms": 45,
                },
                {
                    "call_id": "c2", "tool": "ping", "ok": False,
                    "error": "connection refused", "duration_ms": 12,
                },
            ],
            "duration_ms": 50,
        }
        resp = BatchResponseSchema.model_validate(payload)
        assert resp.results[0].ok is True
        assert resp.results[1].error == "connection refused"

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            BatchResponseSchema.model_validate({"results": [], "duration_ms": 0})  # missing task_id

    def test_result_with_no_data_or_error(self):
        result = ToolResultSchema(call_id="c1", tool="ping", ok=True, duration_ms=1)
        assert result.data is None
        assert result.error is None
