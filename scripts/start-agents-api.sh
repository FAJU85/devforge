#!/bin/bash

# ===================================================
# Start Agent APIs - DevForge Extended QA Suite
# ===================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "Starting Agent APIs - DevForge Extended QA Suite"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_section() {
    echo -e "${BLUE}$1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# ===================================================
# Activate virtual environment
# ===================================================

log_section "Activating Python Virtual Environment"

if [ ! -d "$PROJECT_ROOT/venv" ]; then
    log_error "Virtual environment not found. Run install-qa-extended.sh first."
    exit 1
fi

source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"
log_success "Virtual environment activated"

# ===================================================
# Load environment configuration
# ===================================================

log_section "Loading Configuration"

if [ -f "$PROJECT_ROOT/.env.qa-extended" ]; then
    export $(cat "$PROJECT_ROOT/.env.qa-extended" | xargs)
    log_success "Configuration loaded from .env.qa-extended"
else
    log_info "No .env.qa-extended found, using defaults"
fi

# Set default ports if not configured
export AGENT_API_PORT=${AGENT_API_PORT:-8001}
export BROWSER_API_PORT=${BROWSER_API_PORT:-8002}
export TASK_API_PORT=${TASK_API_PORT:-8003}

log_info "Agent API Port: $AGENT_API_PORT"
log_info "Browser API Port: $BROWSER_API_PORT"
log_info "Task API Port: $TASK_API_PORT"

# ===================================================
# Function to start a server
# ===================================================

start_server() {
    local name=$1
    local port=$2
    local module=$3

    log_info "Starting $name on port $port..."

    python "$PROJECT_ROOT/api/$module" &

    local pid=$!
    sleep 2

    # Check if process is still running
    if ps -p $pid > /dev/null; then
        log_success "$name started (PID: $pid)"
        echo $pid >> /tmp/devforge_pids.txt
    else
        log_error "$name failed to start"
        exit 1
    fi
}

# ===================================================
# Start API servers
# ===================================================

log_section "Starting API Servers"

# Clear PID file
> /tmp/devforge_pids.txt

# Start servers
start_server "Agent Orchestration API" "$AGENT_API_PORT" "agents_server.py"
start_server "Browser Control API" "$BROWSER_API_PORT" "browser_server.py"
start_server "Task Orchestrator" "$TASK_API_PORT" "task_orchestrator.py"

# ===================================================
# Verification
# ===================================================

log_section "Verifying Services"

sleep 2

# Check Agent API
if curl -s http://localhost:$AGENT_API_PORT/health > /dev/null; then
    log_success "Agent API is responding"
else
    log_error "Agent API not responding"
fi

# Check Browser API
if curl -s http://localhost:$BROWSER_API_PORT/health > /dev/null; then
    log_success "Browser API is responding"
else
    log_error "Browser API not responding"
fi

# Check Task Orchestrator
if curl -s http://localhost:$TASK_API_PORT/health > /dev/null; then
    log_success "Task Orchestrator is responding"
else
    log_error "Task Orchestrator not responding"
fi

# ===================================================
# Display service info
# ===================================================

log_section "Services Running"

echo ""
echo -e "${GREEN}✓ Agent Orchestration API${NC}"
echo "  URL: http://localhost:$AGENT_API_PORT"
echo "  Docs: http://localhost:$AGENT_API_PORT/docs"
echo ""

echo -e "${GREEN}✓ Browser Control API${NC}"
echo "  URL: http://localhost:$BROWSER_API_PORT"
echo "  Docs: http://localhost:$BROWSER_API_PORT/docs"
echo ""

echo -e "${GREEN}✓ Task Orchestrator${NC}"
echo "  URL: http://localhost:$TASK_API_PORT"
echo "  Docs: http://localhost:$TASK_API_PORT/docs"
echo ""

# ===================================================
# Display usage examples
# ===================================================

log_section "Quick Start Examples"

echo ""
echo "Browser Task:"
echo "  curl -X POST http://localhost:$AGENT_API_PORT/api/agents/browser/task \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"description\": \"Navigate to example.com\", \"url\": \"https://example.com\"}'"
echo ""

echo "Generate Test:"
echo "  curl -X POST http://localhost:$AGENT_API_PORT/api/agents/test-generator/generate \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"description\": \"Test login functionality\", \"framework\": \"pytest\"}'"
echo ""

echo "Scan for Bugs:"
echo "  curl -X POST http://localhost:$AGENT_API_PORT/api/agents/bug-detector/scan \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"url\": \"https://example.com\"}'"
echo ""

echo "Execute Web Task:"
echo "  curl -X POST http://localhost:$AGENT_API_PORT/api/agents/web-task/execute \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"description\": \"Search for machine learning\", \"start_url\": \"https://google.com\"}'"
echo ""

# ===================================================
# Instructions for stopping
# ===================================================

log_section "To Stop Services"

echo ""
echo "Kill all services:"
echo "  pkill -f 'agents_server.py|browser_server.py|task_orchestrator.py'"
echo ""
echo "Or use the stop script:"
echo "  bash scripts/stop-agents-api.sh"
echo ""

# ===================================================
# Keep running
# ===================================================

log_section "Services Started"
log_info "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
wait

log_section "Shutting Down"
log_info "Stopping services..."

# Kill all child processes
kill $(cat /tmp/devforge_pids.txt) 2>/dev/null || true

log_success "All services stopped"
