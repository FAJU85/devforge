#!/bin/bash

# =====================================================
# Phase 1 Setup Script - DevForge QA Suite Foundation
# Sets up PostgreSQL, Milvus, MinIO, and dependencies
# =====================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PHASE1_DIR="$PROJECT_ROOT"
PYTHON_CMD=${PYTHON_CMD:-python3}
NODE_CMD=${NODE_CMD:-node}

# Utility functions
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

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Install Docker first."
        return 1
    fi
    log_success "Docker found"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not found. Install Docker Compose first."
        return 1
    fi
    log_success "Docker Compose found"

    # Check Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python not found. Install Python 3.8+ first."
        return 1
    fi
    log_success "Python found: $($PYTHON_CMD --version)"

    # Check Node.js (optional but recommended)
    if ! command -v $NODE_CMD &> /dev/null; then
        log_warning "Node.js not found (optional)"
    else
        log_success "Node.js found: $($NODE_CMD --version)"
    fi

    return 0
}

# Setup environment
setup_environment() {
    log_section "Setting Up Environment"

    # Copy .env if not exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/storage/config/.env.example" ]; then
            cp "$PROJECT_ROOT/storage/config/.env.example" "$PROJECT_ROOT/.env"
            log_success "Created .env file from template"
        fi
    else
        log_info ".env file already exists"
    fi

    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/ml/vector_db"
    mkdir -p "$PROJECT_ROOT/ml/models/checkpoints"
    mkdir -p "$PROJECT_ROOT/ml/models/configs"
    mkdir -p "$PROJECT_ROOT/storage/config"
    mkdir -p "$PROJECT_ROOT/db"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data/datasets"
    mkdir -p "$PROJECT_ROOT/data/models"
    mkdir -p "$PROJECT_ROOT/data/artifacts"

    log_success "Created directory structure"
}

# Start Docker containers
start_containers() {
    log_section "Starting Infrastructure Containers"

    log_info "Starting PostgreSQL, Milvus, and MinIO..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.phase1.yml" up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10

    # Check PostgreSQL
    log_info "Checking PostgreSQL..."
    for i in {1..30}; do
        if docker exec devforge-postgres pg_isready -U postgres > /dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "PostgreSQL failed to start"
            return 1
        fi
        sleep 2
    done

    # Check Milvus
    log_info "Checking Milvus..."
    for i in {1..30}; do
        if docker exec devforge-milvus curl -f http://localhost:9091/healthz > /dev/null 2>&1; then
            log_success "Milvus is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Milvus failed to start"
            return 1
        fi
        sleep 2
    done

    # Check MinIO
    log_info "Checking MinIO..."
    for i in {1..30}; do
        if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
            log_success "MinIO is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "MinIO failed to start"
            return 1
        fi
        sleep 2
    done

    return 0
}

# Install Python dependencies
install_dependencies() {
    log_section "Installing Python Dependencies"

    # Create virtual environment if not exists
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$PROJECT_ROOT/venv"
        log_success "Virtual environment created"
    fi

    # Activate virtual environment
    source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"

    # Install requirements
    log_info "Installing Python packages..."
    pip install --upgrade pip setuptools wheel > /dev/null

    # Phase 1 requirements
    pip install \
        pymilvus>=2.3.0 \
        boto3>=1.26.0 \
        psycopg2-binary>=2.9.0 \
        python-dotenv>=0.20.0 \
        > /dev/null

    log_success "Python dependencies installed"
}

# Setup database
setup_database() {
    log_section "Setting Up PostgreSQL Database"

    log_info "Waiting for PostgreSQL to fully initialize..."
    sleep 5

    # PostgreSQL schema should already be loaded via docker-entrypoint-initdb.d
    # But we can verify it worked
    if docker exec devforge-postgres psql -U postgres -d devforge -c "SELECT 1 FROM pg_tables WHERE tablename='ml_models';" > /dev/null 2>&1; then
        log_success "Database schema verified"
    else
        log_warning "Database schema might not be fully initialized yet"
        log_info "Running schema script manually..."
        docker exec -i devforge-postgres psql -U postgres -d devforge < "$PROJECT_ROOT/db/schema_v3.sql"
        log_success "Database schema initialized"
    fi
}

# Setup vector database
setup_vector_db() {
    log_section "Setting Up Milvus Vector Database"

    log_info "Installing Milvus Python client..."
    source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"
    pip install pymilvus>=2.3.0 > /dev/null

    log_info "Running Milvus setup script..."
    $PYTHON_CMD "$PROJECT_ROOT/ml/vector_db/setup.py"

    if [ $? -eq 0 ]; then
        log_success "Milvus vector database setup complete"
    else
        log_error "Milvus setup failed"
        return 1
    fi
}

# Setup object storage
setup_object_storage() {
    log_section "Setting Up S3 Object Storage"

    log_info "Installing boto3..."
    source "$PROJECT_ROOT/venv/bin/activate" || . "$PROJECT_ROOT/venv/Scripts/activate"
    pip install boto3>=1.26.0 > /dev/null

    log_info "Running storage setup script..."
    $PYTHON_CMD "$PROJECT_ROOT/storage/setup_storage.py"

    if [ $? -eq 0 ]; then
        log_success "S3 object storage setup complete"
    else
        log_error "Storage setup failed"
        return 1
    fi
}

# Verify setup
verify_setup() {
    log_section "Verifying Setup"

    # Check PostgreSQL
    log_info "Verifying PostgreSQL connection..."
    if $PYTHON_CMD << 'EOF'
import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="devforge",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(f"✓ PostgreSQL OK - {count} tables found")
except Exception as e:
    print(f"✗ PostgreSQL Error: {e}")
    exit(1)
EOF
    then
        log_success "PostgreSQL connection verified"
    else
        log_error "PostgreSQL verification failed"
        return 1
    fi

    # Check Milvus
    log_info "Verifying Milvus connection..."
    if $PYTHON_CMD << 'EOF'
from pymilvus import connections
try:
    connections.connect(alias="default", host="localhost", port=19530)
    print("✓ Milvus OK")
except Exception as e:
    print(f"✗ Milvus Error: {e}")
    exit(1)
EOF
    then
        log_success "Milvus connection verified"
    else
        log_error "Milvus verification failed"
        return 1
    fi

    # Check S3
    log_info "Verifying S3 connection..."
    if $PYTHON_CMD << 'EOF'
import boto3
try:
    client = boto3.client(
        's3',
        endpoint_url='http://localhost:9000',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin'
    )
    response = client.list_buckets()
    buckets = len(response.get('Buckets', []))
    print(f"✓ S3 OK - {buckets} buckets found")
except Exception as e:
    print(f"✗ S3 Error: {e}")
    exit(1)
EOF
    then
        log_success "S3 connection verified"
    else
        log_error "S3 verification failed"
        return 1
    fi
}

# Display summary
display_summary() {
    log_section "Phase 1 Setup Complete!"

    echo -e "${GREEN}Infrastructure Services:${NC}"
    echo "  PostgreSQL:    postgres://localhost:5432/devforge"
    echo "  Milvus:        localhost:19530"
    echo "  MinIO Console: http://localhost:9001"
    echo "  S3 Console:    http://localhost:9003"
    echo "  PgAdmin:       http://localhost:5050"
    echo ""

    echo -e "${GREEN}Configuration:${NC}"
    echo "  Environment:   $PROJECT_ROOT/.env"
    echo "  Database:      $PROJECT_ROOT/db/schema_v3.sql"
    echo "  Vector DB:     $PROJECT_ROOT/ml/vector_db/"
    echo "  Storage:       $PROJECT_ROOT/storage/"
    echo ""

    echo -e "${GREEN}Next Steps:${NC}"
    echo "  1. Review the .env configuration"
    echo "  2. Start Phase 2 (ML model training)"
    echo "  3. Monitor services: docker-compose -f docker-compose.phase1.yml logs -f"
    echo ""

    echo -e "${BLUE}Documentation:${NC}"
    echo "  See PHASE1_IMPLEMENTATION_GUIDE.md for detailed information"
    echo ""
}

# Main execution
main() {
    log_section "DevForge QA Suite - Phase 1 Setup"

    # Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed"
        exit 1
    fi

    # Setup environment
    if ! setup_environment; then
        log_error "Environment setup failed"
        exit 1
    fi

    # Start containers
    if ! start_containers; then
        log_error "Container startup failed"
        exit 1
    fi

    # Install dependencies
    if ! install_dependencies; then
        log_error "Dependency installation failed"
        exit 1
    fi

    # Setup database
    if ! setup_database; then
        log_error "Database setup failed"
        exit 1
    fi

    # Setup vector database
    if ! setup_vector_db; then
        log_error "Vector database setup failed"
        exit 1
    fi

    # Setup object storage
    if ! setup_object_storage; then
        log_error "Object storage setup failed"
        exit 1
    fi

    # Verify setup
    if ! verify_setup; then
        log_error "Verification failed"
        exit 1
    fi

    # Display summary
    display_summary

    log_success "Phase 1 setup completed successfully!"
}

# Run main
main "$@"
