package executor

import (
	"context"
	"time"
)

// Executor is the interface every tool must implement.
type Executor interface {
	Execute(ctx context.Context, callID string, args map[string]any) ToolResult
}

// ToolResult is the canonical result returned for every tool call.
// Python receives a JSON array of these inside BatchResponse.
type ToolResult struct {
	CallID     string         `json:"call_id"`
	Tool       string         `json:"tool"`
	Ok         bool           `json:"ok"`
	Data       map[string]any `json:"data,omitempty"`
	Error      string         `json:"error,omitempty"`
	DurationMs int64          `json:"duration_ms"`
}

// ms returns elapsed milliseconds since start.
func ms(start time.Time) int64 { return time.Since(start).Milliseconds() }

// errResult is a convenience constructor for failure results.
func errResult(callID, tool, msg string, start time.Time) ToolResult {
	return ToolResult{CallID: callID, Tool: tool, Ok: false, Error: msg, DurationMs: ms(start)}
}
