package tools

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// ToolRequest is the payload sent by the Python control plane.
// Phase 2 will flesh out the full schema.
type ToolRequest struct {
	TaskID string         `json:"task_id" binding:"required"`
	Tool   string         `json:"tool"    binding:"required"`
	Args   map[string]any `json:"args"`
}

// ToolResponse is the strictly formatted JSON returned to Python.
type ToolResponse struct {
	TaskID string         `json:"task_id"`
	Tool   string         `json:"tool"`
	Result map[string]any `json:"result,omitempty"`
	Error  string         `json:"error,omitempty"`
}

// ExecuteHandler is a stub; Phase 2 implements concurrent dispatch.
func ExecuteHandler(c *gin.Context) {
	var req ToolRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, ToolResponse{Error: err.Error()})
		return
	}

	// TODO Phase 2: dispatch to goroutine pool
	c.JSON(http.StatusOK, ToolResponse{
		TaskID: req.TaskID,
		Tool:   req.Tool,
		Result: map[string]any{"status": "stub — Phase 2 pending"},
	})
}
