.PHONY: setup-python setup-go build-go run-go run-python health

# ── Python control plane ──────────────────────────────────────────────────────
setup-python:
	pip install -r control_plane/requirements.txt

run-python:
	cd control_plane && python -m agent

# ── Go data plane ─────────────────────────────────────────────────────────────
setup-go:
	cd data_plane && go mod tidy

build-go:
	cd data_plane && go build -o bin/data-plane ./...

run-go:
	cd data_plane && go run main.go

# ── Health check (requires data-plane running) ────────────────────────────────
health:
	curl -sf http://localhost:8080/health | python3 -m json.tool
