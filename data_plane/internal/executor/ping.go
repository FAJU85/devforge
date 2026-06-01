package executor

import (
	"context"
	"fmt"
	"net"
	"time"
)

const pingTimeout = 5 * time.Second

// Ping performs a TCP dial to verify a host:port is reachable.
// Registered as "ping" in the tool registry.
type Ping struct{}

func (p *Ping) Execute(ctx context.Context, callID string, args map[string]any) ToolResult {
	start := time.Now()

	host, _ := args["host"].(string)
	if host == "" {
		return errResult(callID, "ping", "missing 'host' arg", start)
	}

	port := "80"
	if pt, ok := args["port"].(string); ok && pt != "" {
		port = pt
	}

	addr := net.JoinHostPort(host, port)

	dialCtx, cancel := context.WithTimeout(ctx, pingTimeout)
	defer cancel()

	conn, err := (&net.Dialer{}).DialContext(dialCtx, "tcp", addr)
	if err != nil {
		return errResult(callID, "ping", fmt.Sprintf("dial %s: %v", addr, err), start)
	}
	conn.Close()

	latency := ms(start)
	return ToolResult{
		CallID: callID,
		Tool:   "ping",
		Ok:     true,
		Data: map[string]any{
			"host":       host,
			"port":       port,
			"latency_ms": latency,
		},
		DurationMs: latency,
	}
}
