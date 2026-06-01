package tools

import (
	"fmt"

	"github.com/faju85/devforge/data_plane/internal/executor"
)

// registry maps tool names to their Executor implementations.
// Add new tools here — no other file needs to change.
var registry = map[string]executor.Executor{
	"http_fetch": executor.NewHTTPFetch(),
	"ping":       &executor.Ping{},
}

func lookup(tool string) (executor.Executor, error) {
	e, ok := registry[tool]
	if !ok {
		return nil, fmt.Errorf("unknown tool %q — registered: %v", tool, registeredTools())
	}
	return e, nil
}

func registeredTools() []string {
	names := make([]string, 0, len(registry))
	for k := range registry {
		names = append(names, k)
	}
	return names
}
