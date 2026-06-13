#!/bin/bash
set -e

echo "=== DevForge Deployment Script ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check for docker-compose
if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose is not installed"
    exit 1
fi

log_info "Checking docker-compose configuration..."
docker-compose -f docker-compose.prod.yml config > /dev/null || {
    log_error "Invalid docker-compose configuration"
    exit 1
}

log_info "Building images..."
docker-compose -f docker-compose.prod.yml build --no-cache

log_info "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

log_info "Waiting for services to be healthy..."
sleep 10

# Health check
log_info "Running health checks..."
attempts=0
max_attempts=30
until docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U devforge > /dev/null 2>&1; do
    if [ $attempts -ge $max_attempts ]; then
        log_error "PostgreSQL failed health check"
        exit 1
    fi
    attempts=$((attempts+1))
    echo "Checking PostgreSQL... ($attempts/$max_attempts)"
    sleep 2
done

log_info "PostgreSQL is healthy"

# Check FastAPI
attempts=0
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [ $attempts -ge 30 ]; then
        log_error "FastAPI failed health check"
        exit 1
    fi
    attempts=$((attempts+1))
    echo "Checking FastAPI... ($attempts/30)"
    sleep 2
done

log_info "FastAPI is healthy"

log_info "Deployment completed successfully!"
log_info "API available at http://localhost:8000"
log_info "PgAdmin available at http://localhost:5050"
