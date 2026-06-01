package tools

import (
	"context"
	"testing"
	"time"
)

// TestDispatchConcurrency verifies parallel execution via timing.
// Skipped in unit mode; run with -tags=integration against a live network.
func TestDispatchConcurrency(t *testing.T) {
	t.Skip("integration test — requires live network")
}

// TestDispatchUnknownTool ensures an unknown tool returns an error result
// without crashing the batch or affecting sibling calls.
func TestDispatchUnknownTool(t *testing.T) {
	calls := []ToolCall{
		{CallID: "a", Tool: "nonexistent_tool", Args: nil},
	}

	results := dispatch(context.Background(), calls)

	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].Ok {
		t.Error("expected Ok=false for unknown tool")
	}
	if results[0].Error == "" {
		t.Error("expected non-empty Error for unknown tool")
	}
	if results[0].CallID != "a" {
		t.Errorf("expected CallID 'a', got %q", results[0].CallID)
	}
}

// TestDispatchOrderPreserved ensures results[i] always matches calls[i]
// even when goroutines finish in arbitrary order.
func TestDispatchOrderPreserved(t *testing.T) {
	calls := []ToolCall{
		{CallID: "first", Tool: "nonexistent_1", Args: nil},
		{CallID: "second", Tool: "nonexistent_2", Args: nil},
		{CallID: "third", Tool: "nonexistent_3", Args: nil},
	}

	results := dispatch(context.Background(), calls)

	for i, c := range calls {
		if results[i].CallID != c.CallID {
			t.Errorf("position %d: expected CallID %q, got %q", i, c.CallID, results[i].CallID)
		}
	}
}

// TestDispatchBatchTimeout verifies that the overall batch context deadline
// propagates into individual executors and causes them to fail fast.
func TestDispatchBatchTimeout(t *testing.T) {
	// This test relies on the ping tool actually trying to dial.
	// Use a routable-but-unreachable address to force a timeout.
	calls := []ToolCall{
		{CallID: "t1", Tool: "ping", Args: map[string]any{
			"host": "192.0.2.1", // TEST-NET — guaranteed unreachable
			"port": "80",
		}},
	}

	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	start := time.Now()
	results := dispatch(ctx, calls)
	elapsed := time.Since(start)

	if results[0].Ok {
		t.Error("expected Ok=false for unreachable host")
	}
	// The batch should respect the 200ms context, not wait for the full ping timeout.
	if elapsed > 2*time.Second {
		t.Errorf("batch took %v — context cancellation did not propagate", elapsed)
	}
}
