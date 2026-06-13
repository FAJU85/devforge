# Phase 6 Integration Checklist

This checklist guides integration of Phase 6.2-6.5 features into main.py and services.

## Phase 6.2: Database Integration - Checklist

### Step 1: Update main.py imports
- [ ] Add database initialization
```python
from api.services.database_service import DatabaseService
from db.models import Base, User, Conversation, Message, AuditLog, APIKey, RateLimitEvent, Task, Config, Notification
```

### Step 2: Add startup/shutdown events
- [ ] Add to app initialization:
```python
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    DatabaseService.init_db()
    logger.info("Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    DatabaseService.cleanup()
    logger.info("Services shutdown cleanly")
```

### Step 3: Update models.py
- [ ] Replace with models_v2.py or merge changes:
  - Add is_deleted, deleted_at fields to all tables
  - Add version field to User, Conversation, Message
  - Add ActionEnum for audit logging
  - Add new models: AuditLog, APIKey, RateLimitEvent, Task, Config, Notification

### Step 4: Migrate existing services
- [ ] Update chat_service.py:
  - [ ] Replace in-memory store with database queries
  - [ ] Inject audit_service for logging
  - [ ] Use RepositoryBase for CRUD operations
  
- [ ] Update config_service.py:
  - [ ] Store config in Config model
  - [ ] Log changes to AuditLog
  - [ ] Use database transactions
  
- [ ] Update auth_service.py:
  - [ ] Store sessions in UserSession model
  - [ ] Log authentication events
  - [ ] Support API keys via APIKey model
  
- [ ] Update task_service.py:
  - [ ] Store tasks in Task model
  - [ ] Track task status and progress
  - [ ] Log task execution
  
- [ ] Update repository_service.py:
  - [ ] Store repositories in Repository model
  - [ ] Track last_accessed timestamp

### Phase 6.2 Validation
- [ ] Test: Create user -> store in DB
- [ ] Test: Create conversation -> retrieve from DB
- [ ] Test: Soft delete -> verify is_deleted flag
- [ ] Test: Version tracking -> increment on update
- [ ] Test: Connection pooling -> verify pool stats

---

## Phase 6.3: Rate Limiting - Checklist

### Step 1: Add middleware to main.py
- [ ] Import middleware:
```python
from api.middleware.rate_limiter_middleware import RateLimitMiddleware
```

- [ ] Register middleware (add early in middleware stack):
```python
app.add_middleware(RateLimitMiddleware)
```

### Step 2: Configure rate limits
- [ ] Review limits in rate_limiter_middleware.py:
  - Global: 100 req/min
  - /api/chat: 30 req/min
  - /api/config: 10 req/min
  - /api/tasks: 5 req/min

- [ ] Update in environment if needed:
```bash
RATELIMIT_ENABLED=true
```

### Step 3: Test rate limiting
- [ ] Test: Global limit (send 101 requests)
- [ ] Test: Endpoint limit (send 31 requests to /api/chat)
- [ ] Test: Bypass paths (health check should never rate limit)
- [ ] Test: Response headers (X-RateLimit-*)
- [ ] Test: 429 response with Retry-After header

### Phase 6.3 Validation
- [ ] Request #101 returns 429
- [ ] Response includes X-RateLimit-Limit header
- [ ] Rate limit events logged to database
- [ ] /health bypasses rate limiting

---

## Phase 6.4: Logging & Audit Trail - Checklist

### Step 1: Add logging middleware
- [ ] Import middleware:
```python
from api.middleware.request_logging_middleware import RequestLoggingMiddleware
```

- [ ] Register middleware:
```python
app.add_middleware(RequestLoggingMiddleware)
```

### Step 2: Import audit service
- [ ] In services that need auditing:
```python
from api.services.audit_service import audit_service
```

### Step 3: Log audit events
- [ ] In chat_service.py:
  - [ ] Log after creating conversation
  - [ ] Log after saving message
  - [ ] Log after deleting conversation

- [ ] In config_service.py:
  - [ ] Log after config update
  - [ ] Include old_value, new_value in changes

- [ ] In auth_service.py:
  - [ ] Log auth events (login, logout, API key access)
  - [ ] Log API key rotation

- [ ] In task_service.py:
  - [ ] Log task status changes
  - [ ] Log task completion/failure

### Step 4: Add monitoring routes
- [ ] Include monitoring router in main.py:
```python
from api.routes.monitoring import router as monitoring_router
app.include_router(monitoring_router)
```

### Step 5: Test audit trail
- [ ] Test: Create conversation -> check audit log
- [ ] Test: Update config -> verify changes logged
- [ ] Test: Delete conversation -> check deleted_at
- [ ] Test: API endpoint `/api/monitoring/audit-trail/user/{user_id}`
- [ ] Test: Request logging with correlation ID

### Phase 6.4 Validation
- [ ] Audit entries exist in database
- [ ] Sensitive headers redacted in logs
- [ ] Correlation IDs track requests
- [ ] Monitoring endpoints return valid data
- [ ] Slow requests logged (>1000ms)

---

## Phase 6.5: Deployment Optimization - Checklist

### Step 1: Update main.py for graceful shutdown
- [ ] Add lifespan context manager (Python 3.9+):
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    startup_event()
    yield
    # Shutdown
    shutdown_event()

app = FastAPI(lifespan=lifespan)
```

### Step 2: Configure CORS
- [ ] Add CORS configuration:
```python
from fastapi.middleware.cors import CORSMiddleware

origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
    max_age=3600,
)
```

### Step 3: Environment setup
- [ ] Copy .env.example to .env
- [ ] Set all required environment variables
- [ ] Generate ENCRYPTION_KEY:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 4: Docker setup
- [ ] Review Dockerfile.api
- [ ] Review docker-compose.prod.yml
- [ ] Create logs directory:
```bash
mkdir -p logs
```

### Step 5: Deploy
- [ ] Run deployment script:
```bash
./scripts/deploy.sh
```

- [ ] Verify all services healthy:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/monitoring/health
```

### Step 6: Test production setup
- [ ] Test: API requests work
- [ ] Test: Rate limiting enforced
- [ ] Test: Audit trail recorded
- [ ] Test: Logs rotated
- [ ] Test: Database backups scheduled

### Phase 6.5 Validation
- [ ] All services start without error
- [ ] Health checks pass
- [ ] Logs in /logs directory
- [ ] PostgreSQL data persisted
- [ ] Redis cache operational
- [ ] PgAdmin accessible at :5050

---

## Post-Deployment Checklist

### Monitoring
- [ ] Set up log aggregation (ELK, Datadog)
- [ ] Set up metrics monitoring (Prometheus)
- [ ] Set up alerting for errors
- [ ] Set up alerting for slow requests
- [ ] Set up alerting for rate limit violations

### Security
- [ ] Rotate encryption key securely
- [ ] Enable SSL/TLS on production
- [ ] Configure WAF rules
- [ ] Set up IP whitelisting
- [ ] Enable security headers (done via SecurityHeaders middleware)

### Performance
- [ ] Monitor database connection pool
- [ ] Monitor Redis memory usage
- [ ] Tune PostgreSQL query cache
- [ ] Enable query caching where appropriate
- [ ] Monitor API response times

### Backup & Recovery
- [ ] Set up automated database backups
- [ ] Test backup restoration
- [ ] Document disaster recovery procedures
- [ ] Set up point-in-time recovery
- [ ] Encrypt backups

### Testing
- [ ] Run full integration test suite
- [ ] Load test with k6 or locust
- [ ] Test failover scenarios
- [ ] Test rollback procedures
- [ ] Verify audit trail compliance

---

## Rollback Procedures

If issues arise, follow this rollback procedure:

### Database
```bash
# Rollback migrations
alembic downgrade -1

# Restore from backup
psql -U devforge -d devforge < backup.sql
```

### Docker
```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restore previous image
docker-compose -f docker-compose.prod.yml down -v
docker rmi devforge-api:previous
docker tag devforge-api:current devforge-api:broken
docker tag devforge-api:backup devforge-api:current
docker-compose -f docker-compose.prod.yml up -d
```

### Features
```bash
# Disable rate limiting if causing issues
RATELIMIT_ENABLED=false

# Disable audit logging if causing performance issues
# (remove audit_service calls from services)
```

---

## Files Checklist - All Created

### Core Infrastructure
- [x] `/db/models_v2.py` - Enhanced ORM models
- [x] `/api/services/database_service.py` - Database operations
- [x] `/api/services/audit_service.py` - Audit trail management

### Middleware
- [x] `/api/middleware/__init__.py`
- [x] `/api/middleware/rate_limiter_middleware.py`
- [x] `/api/middleware/request_logging_middleware.py`

### Routes
- [x] `/api/routes/monitoring.py` - Monitoring endpoints

### Deployment
- [x] `/docker-compose.prod.yml` - Production docker stack
- [x] `/Dockerfile.api` - FastAPI container image
- [x] `/scripts/entrypoint.sh` - Container startup script
- [x] `/scripts/deploy.sh` - Deployment automation

### Configuration
- [x] `/.env.example` - Environment template
- [x] `/config/logging.json` - Logging configuration

### Documentation
- [x] `/PHASE_6_IMPLEMENTATION_GUIDE.md` - Detailed guide
- [x] `/INTEGRATION_CHECKLIST.md` - This file

---

## Next Steps

1. **Update main.py**: Follow the integration checklist above
2. **Run tests**: Verify each phase works independently
3. **Integration testing**: Test full flow end-to-end
4. **Load testing**: Ensure rate limits work under load
5. **Deployment**: Use deploy.sh to bring up production stack
6. **Monitoring**: Set up observability infrastructure
7. **Documentation**: Update API docs with new endpoints

---

## Support & Troubleshooting

### Common Issues

**Issue**: Database connection refused
- Solution: Check PostgreSQL is running: `docker-compose -f docker-compose.prod.yml ps postgres`

**Issue**: Rate limiting too aggressive
- Solution: Adjust limits in `rate_limiter_middleware.py`

**Issue**: Slow requests after audit logging
- Solution: Enable batching or async audit writes

**Issue**: Disk full from logs
- Solution: Ensure rotation configured in `config/logging.json` and logs directory has space

### Getting Help

1. Check `/PHASE_6_IMPLEMENTATION_GUIDE.md` for detailed information
2. Review logs: `tail -f logs/app.log`
3. Check metrics: `curl http://localhost:8000/api/monitoring/metrics`
4. Verify audit trail: `curl http://localhost:8000/api/monitoring/audit-trail/user/{user_id}`

