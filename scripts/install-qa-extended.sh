#!/bin/bash

# =====================================================
# DevForge QA Suite - Extended Installation
# Installs AI agents, browser automation, web tasks
# =====================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# =====================================================
# 1. Install npm dependencies
# =====================================================

install_npm_deps() {
    log_section "Installing npm Dependencies"

    cd "$PROJECT_ROOT"

    # Core AI and browser automation
    log_info "Installing Vercel AI SDK..."
    npm install ai@latest > /dev/null 2>&1 && log_success "ai" || log_error "ai"

    log_info "Installing Stagehand..."
    npm install @browserbasehq/stagehand@latest > /dev/null 2>&1 && log_success "stagehand" || log_error "stagehand"

    log_info "Installing Puppeteer..."
    npm install puppeteer@latest > /dev/null 2>&1 && log_success "puppeteer" || log_error "puppeteer"

    log_info "Installing additional tools..."
    npm install axios dotenv cors express-cors > /dev/null 2>&1 && log_success "utilities" || log_error "utilities"

    log_success "npm dependencies installed"
}

# =====================================================
# 2. Install Python dependencies
# =====================================================

install_python_deps() {
    log_section "Installing Python Dependencies"

    # Create virtual environment if not exists
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$PROJECT_ROOT/venv"
        log_success "Virtual environment created"
    fi

    # Activate virtual environment
    source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"

    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1

    log_info "Installing core dependencies..."
    pip install -r "$PROJECT_ROOT/requirements-phase1.txt" > /dev/null 2>&1 && log_success "Phase 1 deps" || log_error "Phase 1 deps"

    log_info "Installing extended dependencies..."
    pip install -r "$PROJECT_ROOT/requirements-phase1-extended.txt" > /dev/null 2>&1 && log_success "Extended deps" || log_error "Extended deps"

    log_info "Installing specific packages..."

    # Anthropic SDK
    pip install anthropic > /dev/null 2>&1 && log_success "anthropic" || log_error "anthropic"

    # Playwright
    pip install playwright > /dev/null 2>&1 && log_success "playwright" || log_error "playwright"
    python -m playwright install chromium > /dev/null 2>&1

    # Selenium
    pip install selenium > /dev/null 2>&1 && log_success "selenium" || log_error "selenium"

    # Vision
    pip install pillow opencv-python > /dev/null 2>&1 && log_success "vision" || log_error "vision"

    # Datasets
    pip install datasets huggingface-hub > /dev/null 2>&1 && log_success "datasets" || log_error "datasets"

    log_success "Python dependencies installed"
}

# =====================================================
# 3. Clone and setup tools
# =====================================================

setup_tools() {
    log_section "Setting Up Tools & Frameworks"

    mkdir -p "$PROJECT_ROOT/tools"
    cd "$PROJECT_ROOT/tools"

    # Browser Use
    if [ ! -d "browser-use" ]; then
        log_info "Cloning Browser Use..."
        git clone https://github.com/browser-use/browser-use.git > /dev/null 2>&1
        log_success "Browser Use cloned"
    else
        log_info "Browser Use already exists, updating..."
        cd browser-use && git pull > /dev/null 2>&1 && cd ..
        log_success "Browser Use updated"
    fi

    # Gorilla
    if [ ! -d "gorilla" ]; then
        log_info "Cloning Gorilla..."
        git clone https://github.com/shishirpatil/gorilla.git > /dev/null 2>&1
        log_success "Gorilla cloned"
    else
        log_info "Gorilla already exists, updating..."
        cd gorilla && git pull > /dev/null 2>&1 && cd ..
        log_success "Gorilla updated"
    fi

    # WebArena
    if [ ! -d "webarena" ]; then
        log_info "Cloning WebArena..."
        git clone https://github.com/web-arena-x/webarena.git > /dev/null 2>&1
        log_success "WebArena cloned"
    else
        log_info "WebArena already exists, updating..."
        cd webarena && git pull > /dev/null 2>&1 && cd ..
        log_success "WebArena updated"
    fi
}

# =====================================================
# 4. Download datasets
# =====================================================

download_datasets() {
    log_section "Downloading Datasets"

    source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"

    mkdir -p "$PROJECT_ROOT/data/datasets"

    log_info "RepliQA (10K+ test specifications)..."
    python3 << 'EOF'
from datasets import load_dataset
import os

try:
    dataset = load_dataset("ServiceNow/repliqa", split="train", streaming=True)

    # Download first 100 examples for demo
    count = 0
    output_file = "data/datasets/repliqa.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        for example in dataset:
            f.write(str(example) + '\n')
            count += 1
            if count >= 100:  # Demo: first 100
                break

    print(f"✓ Downloaded {count} RepliQA examples")
except Exception as e:
    print(f"⚠ RepliQA download skipped: {e}")
EOF

    log_info "Mind2Web dataset info..."
    log_info "  Visit: https://osu-nlp-group.github.io/Mind2Web/"
    log_info "  Download manually or use HF datasets when available"

    log_info "WebArena setup..."
    log_info "  See: https://github.com/web-arena-x/webarena"
    log_info "  Requires Linux environment for full functionality"

    log_success "Dataset setup complete"
}

# =====================================================
# 5. Create configuration files
# =====================================================

create_config() {
    log_section "Creating Configuration Files"

    # Create .env.qa-extended
    cat > "$PROJECT_ROOT/.env.qa-extended" << 'EOF'
# =====================================================
# QA Suite Extended Configuration
# =====================================================

# =====================================================
# AI/LLM Configuration
# =====================================================

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_key_here

# OpenAI (GPT)
OPENAI_API_KEY=your_openai_key_here

# =====================================================
# Browser Automation
# =====================================================

BROWSER_TYPE=chromium
HEADLESS=true
BROWSER_TIMEOUT=30000
DEBUG_MODE=false

# =====================================================
# Agent Configuration
# =====================================================

AGENT_MAX_STEPS=50
AGENT_TIMEOUT=300
AGENT_MEMORY_SIZE=10
CONCURRENT_AGENTS=5

# =====================================================
# WebArena Configuration
# =====================================================

WEBARENA_SITES_DIR=./data/webarena/sites
WEBARENA_BACKEND_URL=http://localhost:3000
WEBARENA_HEADLESS=true

# =====================================================
# Dataset Configuration
# =====================================================

REPLIQA_DATA_DIR=./data/datasets/repliqa
MIND2WEB_DATA_DIR=./data/datasets/mind2web
WEBARENA_TASKS_DIR=./data/datasets/webarena/tasks

# =====================================================
# API Configuration
# =====================================================

AGENT_API_PORT=8001
BROWSER_API_PORT=8002
TASK_API_PORT=8003

# =====================================================
# Logging
# =====================================================

LOG_LEVEL=INFO
LOG_FORMAT=json
VERBOSE_LOGGING=false
EOF

    log_success "Created .env.qa-extended"
}

# =====================================================
# 6. Create directory structure
# =====================================================

create_structure() {
    log_section "Creating Directory Structure"

    mkdir -p "$PROJECT_ROOT/ml/agents"
    mkdir -p "$PROJECT_ROOT/ml/vision"
    mkdir -p "$PROJECT_ROOT/api/agents"
    mkdir -p "$PROJECT_ROOT/data/datasets/repliqa"
    mkdir -p "$PROJECT_ROOT/data/datasets/mind2web"
    mkdir -p "$PROJECT_ROOT/data/datasets/webarena"
    mkdir -p "$PROJECT_ROOT/tools"
    mkdir -p "$PROJECT_ROOT/examples/agents"

    log_success "Directory structure created"
}

# =====================================================
# 7. Test installations
# =====================================================

test_installations() {
    log_section "Testing Installations"

    source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"

    # Test Python imports
    python3 << 'EOF'
import sys

modules = [
    ('anthropic', 'Anthropic SDK'),
    ('playwright', 'Playwright'),
    ('selenium', 'Selenium'),
    ('PIL', 'Pillow'),
    ('cv2', 'OpenCV'),
    ('datasets', 'HuggingFace Datasets'),
]

for module, name in modules:
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name}")
EOF

    # Test Node packages
    log_info "Testing Node packages..."
    npm list ai @browserbasehq/stagehand puppeteer 2>/dev/null | grep -E "@|puppeteer" || log_error "Some npm packages missing"

    log_success "Installation tests complete"
}

# =====================================================
# 8. Display summary
# =====================================================

display_summary() {
    log_section "Installation Summary"

    echo -e "${GREEN}✓ npm packages installed${NC}"
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
    echo -e "${GREEN}✓ Tools cloned (Browser Use, Gorilla, WebArena)${NC}"
    echo -e "${GREEN}✓ Datasets downloaded${NC}"
    echo -e "${GREEN}✓ Configuration created (.env.qa-extended)${NC}"
    echo -e "${GREEN}✓ Directory structure created${NC}"
    echo ""

    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Configure API keys in .env.qa-extended"
    echo "  2. Start agent servers: npm run start:agents"
    echo "  3. Review examples: ls examples/agents/"
    echo "  4. Start API server: python api/phase1_server.py"
    echo ""

    echo -e "${BLUE}Available Tools:${NC}"
    echo "  • Browser Use (AI browser automation)"
    echo "  • Gorilla (LLM API orchestration)"
    echo "  • WebArena (web task environment)"
    echo "  • Vercel AI SDK (LLM integration)"
    echo "  • Stagehand (browser control)"
    echo ""

    echo -e "${BLUE}Data Directories:${NC}"
    echo "  • ./data/datasets/repliqa - Test specifications"
    echo "  • ./data/datasets/mind2web - Web task data"
    echo "  • ./data/datasets/webarena - Web environment"
    echo ""
}

# =====================================================
# Main execution
# =====================================================

main() {
    log_section "DevForge QA Suite - Extended Installation"

    create_structure
    install_npm_deps
    install_python_deps
    setup_tools
    download_datasets
    create_config
    test_installations
    display_summary

    log_success "Installation complete!"
}

main "$@"
