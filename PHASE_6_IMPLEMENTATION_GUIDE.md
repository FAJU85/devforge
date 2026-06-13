# PHASE 6.2-6.5 Production Hardening Implementation Guide

## Overview

This document outlines the implementation of production hardening features including:
- **Phase 6.2**: Database Integration (SQLAlchemy, Alembic, PostgreSQL)
- **Phase 6.3**: Rate Limiting Integration (per-user, per-endpoint)
- **Phase 6.4**: Logging & Audit Trail (request/response logging, audit trail)
- **Phase 6.5**: Deployment Optimization (Docker, health checks, graceful shutdown)

## Phase 6.2: Database Integration

### Enhanced Models
- **File**: `/api/db/models_v2.py`
- Added fields: soft delete (is_deleted, deleted_at), versioning (version for optimistic locking)
- New models:
  - `AuditLog`: Immutable audit trail
  - `APIKey`: API key lifecycle management
  - `RateLimitEvent`: Rate limit violation tracking
  - `Task`: Background task management
  - `Config`: User configuration
  - `Notification`: User notifications

### Database Service
- **File**: `/api/services/database_service.py`
- `RepositoryBase`: Generic CRUD operations with soft delete support
- `DatabaseService`: High-level database operations
  - `init_db()`: Initialize database
  - `health_check()`: Database connectivity check
  - `cleanup()`: Graceful connection pool shutdown
  - `log_audit()`: Log audit events to database

### Usage Example
```python
from api.services.database_service import DatabaseService, RepositoryBase
from db.models import User

# Initialize
DatabaseService.init_db()

# Use repository pattern
user_repo = RepositoryBase(User)
db = DatabaseService.get_session()

# Create
user = user_repo.create(db, github_id=12345, github_login="octocat")

# Read
user = user_repo.read(db, user.id)

# Update
user = user_repo.update(db, user.id, github_name="Octocat User")

# Soft delete
user_repo.delete(db, user.id)

# Cleanup
DatabaseService.cleanup()
```

## Phase 6.3: Rate Limiting Integration

### Rate Limiter Middleware
- **File**: `/api/middleware/rate_limiter_middleware.py`
- **Global limit**: 100 requests/minute per user
- **Endpoint-specific limits**:
  - `/api/chat`: 30 req/min
  - `/api/config`: 10 req/min
  - `/api/tasks`: 5 req/min
- **Bypass paths**: `/health`, `/api/health`, `/api/auth/*`, `/metrics`

### Response Headers
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp of window reset
- `Retry-After`: Seconds to wait before retry (on 429 response)

### Usage
The middleware is integrated into FastAPI app startup:
```python
from api.middleware.rate_limiter_middleware import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware)
```

## Phase 6.4: Logging & Audit Trail

### Request Logging Middleware
- **File**: `/api/middleware/request_logging_middleware.py`
- Sanitizes sensitive headers and query parameters
- Adds correlation ID to all requests
- Logs slow requests (>1000ms)
- Captures user ID for audit trail

### Audit Service
- **File**: `/api/services/audit_service.py`
- Methods:
  - `log_action()`: Generic audit logging
  - `log_config_change()`: Config modifications
  - `log_api_key_access()`: API key usage
  - `log_task_execution()`: Task execution events
  - `log_conversation_delete()`: Conversation deletions
  - `get_audit_trail()`: Retrieve audit history by entity
  - `get_user_audit_trail()`: Retrieve user's audit history

### Monitoring Routes
- **File**: `/api/routes/monitoring.py`
- Endpoints:
  - `GET /api/monitoring/health`: System health check
  - `GET /api/monitoring/metrics`: Current metrics
  - `GET /api/monitoring/logs/recent`: Recent log entries
  - `GET /api/monitoring/logs/stats`: Log statistics
  - `GET /api/monitoring/audit-trail/user/{user_id}`: User audit trail
  - `GET /api/monitoring/audit-trail/entity/{entity_type}/{entity_id}`: Entity audit trail
  - `GET /api/monitoring/rate-limits/{user_id}`: Rate limit status
  - `GET /api/monitoring/performance/endpoints`: Endpoint performance metrics
  - `GET /api/monitoring/performance/slow-requests`: Slow request tracking

### Usage Example
```python
from api.services.audit_service import audit_service
from db.models import ActionEnum
from uuid import UUID

# Log config change
audit_service.log_config_change(
    user_id=UUID("..."),
    config_key="theme",
    old_value="light",
    new_value="dark",
    reason="User preference change"
)

# Get audit trail
trail = audit_service.get_user_audit_trail(
    user_id=UUID("..."),
    limit=50
)
```

## Phase 6.5: Deployment Optimization

### Docker Compose
- **File**: `/docker-compose.prod.yml`
- Services:
  - `fastapi-backend`: Python FastAPI application
  - `postgres`: PostgreSQL 15 database
  - `redis`: Redis cache
  - `pgadmin`: Database administration UI
- Health checks for all services
- Volume management for persistence
- Network isolation

### Dockerfile
- **File**: `/Dockerfile.api`
- Multi-stage build (optimized)
- System dependencies: curl, git, netcat
- Python 3.11-slim base image
- Health check endpoint
- 4 worker processes via Uvicorn

### Entrypoint Script
- **File**: `/scripts/entrypoint.sh`
- Waits for PostgreSQL and Redis
- Runs database migrations
- Starts FastAPI server with proper logging

### Deployment Script
- **File**: `/scripts/deploy.sh`
- Validates docker-compose configuration
- Builds images
- Starts services
- Runs health checks
- Reports deployment status

### Configuration Files
- **`.env.example`**: Environment variable template
- **`config/logging.json`**: Logging configuration (rotation, levels)
- **`config/prometheus.yml`** (optional): Prometheus scrape config

## Integration Steps

### Step 1: Update main.py
```python
from api.middleware.rate_limiter_middleware import RateLimitMiddleware
from api.middleware.request_logging_middleware import RequestLoggingMiddleware
from api.services.database_service import DatabaseService

# Add middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    DatabaseService.init_db()

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    DatabaseService.cleanup()
```

### Step 2: Update Services
Inject audit service into chat_service, config_service, task_service:
```python
from api.services.audit_service import audit_service

class ConfigService:
    def update_config(self, user_id: UUID, config_data: Dict):
        old_config = self.get_config(user_id)
        new_config = {**old_config, **config_data}
        
        # Persist to database
        # ...
        
        # Log audit
        audit_service.log_config_change(
            user_id, 
            "config", 
            old_config,
            new_config
        )
```

### Step 3: Include Monitoring Routes
```python
from api.routes.monitoring import router as monitoring_router
app.include_router(monitoring_router)
```

### Step 4: Update Requirements
Add new dependencies:
```
sqlalchemy==2.0.23
alembic==1.12.0
cryptography==41.0.0
python-json-logger==2.0.7
```

## Deployment

### Local Development
```bash
# Run with SQLite
python main.py

# Or with Docker
docker-compose -f docker-compose.prod.yml up
```

### Production Deployment
```bash
# Copy .env.example to .env and configure
cp .env.example .env

# Run deployment script
./scripts/deploy.sh

# API will be available at http://localhost:8000
# PgAdmin at http://localhost:5050
```

### Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check full system health
curl http://localhost:8000/api/monitoring/health

# Get metrics
curl http://localhost:8000/api/monitoring/metrics

# Get audit trail
curl http://localhost:8000/api/monitoring/audit-trail/user/{user_id}
```

## Database Migrations

### With Alembic (if configured)
```bash
# Create migration
alembic revision --autogenerate -m "Add audit tables"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Without Alembic
Database tables are created automatically on first `init_db()` call:
```python
from api.services.database_service import DatabaseService
DatabaseService.init_db()
```

## Security Considerations

1. **Encryption**: API keys and secrets are encrypted with Fernet
2. **Rate Limiting**: Prevents abuse and DDoS attacks
3. **Audit Trail**: Immutable record of all changes
4. **Soft Deletes**: Data retention and compliance
5. **CORS**: Configurable origins for production
6. **Sensitive Data**: Headers and params sanitized in logs

## Performance Optimization

1. **Connection Pooling**: PostgreSQL QueuePool with pre-ping health checks
2. **Indexing**: Strategic indexes on audit logs, rate limit events
3. **Metrics**: Performance tracking of slow operations
4. **Caching**: Redis for session and rate limit storage
5. **Graceful Shutdown**: In-flight requests completed before shutdown

## Monitoring & Observability

### Logs
- Request/response logging with correlation IDs
- Structured JSON logging for log aggregation
- Rotating file handlers (10 x 100MB files)
- Per-component log levels

### Metrics
- Request count, latency (mean, p95, p99)
- Slow operation tracking
- Rate limit violation tracking
- Database connection pool stats

### Audit Trail
- All entity modifications tracked
- Config changes audited
- API key access logged
- Task execution tracked
- User actions retained for compliance

## Testing

### Unit Tests
```bash
pytest tests/test_database_service.py
pytest tests/test_audit_service.py
pytest tests/test_rate_limiter.py
```

### Integration Tests
```bash
# Run full integration tests
pytest tests/test_integration.py

# Run with PostgreSQL
DATABASE_URL=postgresql://... pytest
```

### Load Testing
```bash
# Using locust
locust -f tests/load_test.py --host=http://localhost:8000

# Simulate rate limiting
python -c "
import requests
for i in range(150):
    resp = requests.get('http://localhost:8000/api/chat/send', 
                       headers={'X-User-ID': 'test-user'})
    print(f'{i}: {resp.status_code}')
"
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
psql -U devforge -d devforge -h localhost
```

### Rate Limiting Not Working
```bash
# Check middleware is registered
curl -v http://localhost:8000/api/health | grep X-RateLimit

# Check RATELIMIT_ENABLED env var
echo $RATELIMIT_ENABLED
```

### Slow Log Queries
```bash
# Enable query logging
SQLALCHEMY_ECHO=true python main.py

# Check slow query log
tail -f logs/app.log | grep slow_operation
```

## Future Enhancements

1. **Redis Integration**: Use Redis for distributed rate limiting
2. **Prometheus Metrics**: Expose metrics for Prometheus scraping
3. **ELK Stack**: Send logs to Elasticsearch for analysis
4. **Circuit Breaker**: Prevent cascading failures to external APIs
5. **Distributed Tracing**: OpenTelemetry integration for request tracing
6. **Database Replication**: Master-replica setup for HA
7. **Backup & Recovery**: Automated backups and point-in-time recovery
8. **Feature Flags**: Dynamic feature control without redeployment

