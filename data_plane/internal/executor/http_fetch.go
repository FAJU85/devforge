package executor

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	httpFetchTimeout = 10 * time.Second
	maxBodyBytes     = 64 * 1024 // 64 KB cap — prevents runaway reads
)

// HTTPFetch performs a single HTTP request and returns status + body.
// Registered as "http_fetch" in the tool registry.
type HTTPFetch struct {
	client *http.Client
}

func NewHTTPFetch() *HTTPFetch {
	return &HTTPFetch{
		client: &http.Client{Timeout: httpFetchTimeout},
	}
}

func (h *HTTPFetch) Execute(ctx context.Context, callID string, args map[string]any) ToolResult {
	start := time.Now()

	url, ok := args["url"].(string)
	if !ok || url == "" {
		return errResult(callID, "http_fetch", "missing or invalid 'url' arg", start)
	}

	method := "GET"
	if m, ok := args["method"].(string); ok && m != "" {
		method = m
	}

	// Honour the parent context (overall batch timeout) AND add a per-call cap.
	callCtx, cancel := context.WithTimeout(ctx, httpFetchTimeout)
	defer cancel()

	req, err := http.NewRequestWithContext(callCtx, method, url, nil)
	if err != nil {
		return errResult(callID, "http_fetch", fmt.Sprintf("build request: %v", err), start)
	}
	req.Header.Set("User-Agent", "DevForge-DataPlane/1.0")

	resp, err := h.client.Do(req)
	if err != nil {
		return errResult(callID, "http_fetch", fmt.Sprintf("fetch: %v", err), start)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(io.LimitReader(resp.Body, maxBodyBytes))
	if err != nil {
		return errResult(callID, "http_fetch", fmt.Sprintf("read body: %v", err), start)
	}

	return ToolResult{
		CallID: callID,
		Tool:   "http_fetch",
		Ok:     resp.StatusCode < 400,
		Data: map[string]any{
			"status_code":  resp.StatusCode,
			"body":         string(body),
			"content_type": resp.Header.Get("Content-Type"),
			"url":          url,
		},
		DurationMs: ms(start),
	}
}
