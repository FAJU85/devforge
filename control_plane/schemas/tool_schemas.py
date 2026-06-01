from typing import Any, Literal
from pydantic import BaseModel, Field


# ── Outbound: Python → Go ─────────────────────────────────────────────────────

class ToolCallSchema(BaseModel):
    """One tool invocation in a batch. Maps 1:1 to Go's tools.ToolCall."""
    call_id: str = Field(..., description="Unique ID within the batch, e.g. 'fetch-1'")
    tool: Literal["http_fetch", "ping"] = Field(
        ..., description="Name of the registered Go executor"
    )
    args: dict[str, Any] = Field(default_factory=dict)


class BatchRequestSchema(BaseModel):
    """The full payload sent to POST /tools/execute on the Go service."""
    task_id: str = Field(..., description="Trace ID for this batch")
    calls: list[ToolCallSchema] = Field(..., min_length=1, max_length=20)


# ── Inbound: Go → Python ──────────────────────────────────────────────────────

class ToolResultSchema(BaseModel):
    """Result for one tool call. Maps 1:1 to Go's executor.ToolResult."""
    call_id: str
    tool: str
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: int


class BatchResponseSchema(BaseModel):
    """Full response from the Go service. Pydantic validates every field."""
    task_id: str
    results: list[ToolResultSchema]
    duration_ms: int
