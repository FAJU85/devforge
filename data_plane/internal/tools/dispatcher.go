package tools

import (
	"context"
	"sync"
	"time"

	"github.com/faju85/devforge/data_plane/internal/executor"
)

// overallBatchTimeout is the hard ceiling for an entire batch, regardless
// of how many calls it contains or what per-call timeouts are set.
const overallBatchTimeout = 30 * time.Second

// dispatch fans out all ToolCalls concurrently, one goroutine per call,
// and fans in the results. Order is preserved: results[i] matches calls[i].
//
// It respects two timeout layers:
//  1. overallBatchTimeout — the whole batch must finish within this window.
//  2. Per-executor timeout — each tool enforces its own inner deadline.
func dispatch(ctx context.Context, calls []ToolCall) []executor.ToolResult {
	batchCtx, cancel := context.WithTimeout(ctx, overallBatchTimeout)
	defer cancel()

	results := make([]executor.ToolResult, len(calls))
	var wg sync.WaitGroup

	for i, call := range calls {
		wg.Add(1)
		// Capture loop variables explicitly — required for goroutine closures.
		go func(idx int, c ToolCall) {
			defer wg.Done()

			exe, err := lookup(c.Tool)
			if err != nil {
				results[idx] = executor.ToolResult{
					CallID: c.CallID,
					Tool:   c.Tool,
					Ok:     false,
					Error:  err.Error(),
				}
				return
			}

			results[idx] = exe.Execute(batchCtx, c.CallID, c.Args)
		}(i, call)
	}

	wg.Wait()
	return results
}
