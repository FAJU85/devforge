package tools

import (
	"net/http"
	"time"

	"github.com/faju85/devforge/data_plane/internal/executor"
	"github.com/gin-gonic/gin"
)

// ToolCall is a single tool invocation within a batch request.
type ToolCall struct {
	CallID string         `json:"call_id" binding:"required"`
	Tool   string         `json:"tool"    binding:"required"`
	Args   map[string]any `json:"args"`
}

// BatchRequest is the payload the Python control plane sends.
// A single request may contain many tool calls; all are executed concurrently.
type BatchRequest struct {
	TaskID string     `json:"task_id" binding:"required"`
	Calls  []ToolCall `json:"calls"   binding:"required,min=1"`
}

// BatchResponse is the strictly typed JSON payload returned to Python.
// Python must not receive partial or untyped responses from this service.
type BatchResponse struct {
	TaskID     string               `json:"task_id"`
	Results    []executor.ToolResult `json:"results"`
	DurationMs int64                `json:"duration_ms"`
}

// ExecuteHandler accepts a BatchRequest, fans out all calls concurrently,
// and returns a BatchResponse with one result per call, order preserved.
func ExecuteHandler(c *gin.Context) {
	var req BatchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	start := time.Now()
	results := dispatch(c.Request.Context(), req.Calls)

	c.JSON(http.StatusOK, BatchResponse{
		TaskID:     req.TaskID,
		Results:    results,
		DurationMs: time.Since(start).Milliseconds(),
	})
}
