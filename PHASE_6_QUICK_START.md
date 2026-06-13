# Phase 6 Quick Start Guide

## 5-Minute Setup

### 1. Copy Enhanced Models
```bash
cp db/models_v2.py db/models.py
```

### 2. Add Imports to main.py
```python
from api.services.database_service import DatabaseService
from api.middleware.rate_limiter_middleware import RateLimitMiddleware
from api.middleware.request_logging_middleware import RequestLoggingMiddleware
from api.routes.monitoring import router as monitoring_router
```

### 3. Register Middleware (early in stack)
```python
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
```

### 4. Add Startup/Shutdown Events
```python
@app.on_event("startup")
async def startup():
    DatabaseService.init_db()

@app.on_event("shutdown")
async def shutdown():
    DatabaseService.cleanup()
```

### 5. Include Monitoring Routes
```python
app.include_router(monitoring_router)
```

### 6. Run Tests
```bash
pytest tests/test_phase6_integration.py -v
```

---

## Key Endpoints

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/api/monitoring/health

# Metrics
curl http://localhost:8000/api/monitoring/metrics

# Audit trail
curl http://localhost:8000/api/monitoring/audit-trail/user/{user_id}

# Rate limit status
curl http://localhost:8000/api/monitoring/rate-limits/{user_id}

# Logs
curl http://localhost:8000/api/monitoring/logs/recent
```

---

## Docker Deployment

```bash
# Copy env template
cp .env.example .env

# Generate encryption key (paste in .env)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Deploy
./scripts/deploy.sh

# Access
# API: http://localhost:8000
# PgAdmin: http://localhost:5050
```

---

## Service Migration Example

### Chat Service
```python
from api.services.database_service import RepositoryBase
from api.services.audit_service import audit_service
from db.models import Conversation, Message, ActionEnum

class ChatService:
    def __init__(self):
        self.conv_repo = RepositoryBase(Conversation)
        self.msg_repo = RepositoryBase(Message)
    
    def create_conversation(self, user_id: UUID, name: str):
        db = DatabaseService.get_session()
        
        # Create in database
        conv = self.conv_repo.create(
            db, 
            user_id=user_id, 
            name=name
        )
        
        # Log to audit trail
        audit_service.log_action(
            user_id,
            "Conversation",
            str(conv.id),
            ActionEnum.CREATE,
            reason="User created conversation"
        )
        
        db.close()
        return conv
```

---

## Testing Examples

### Test Database Operations
```python
from tests.test_phase6_integration import TestDatabaseService
pytest tests/test_phase6_integration.py::TestDatabaseService -v
```

### Test Rate Limiting
```python
from tests.test_phase6_integration import TestRateLimiter
pytest tests/test_phase6_integration.py::TestRateLimiter -v
```

### Test Audit Trail
```python
from tests.test_phase6_integration import TestAuditService
pytest tests/test_phase6_integration.py::TestAuditService -v
```

---

## Rate Limit Testing

```bash
# Test global limit (100 req/min)
for i in {1..101}; do
  curl -s -H "X-User-ID: test-user" \
    http://localhost:8000/api/chat/send \
    -o /dev/null -w "%{http_code}\n"
done

# Should see 429 on request #101
```

---

## Common Tasks

### Check Database Health
```python
from api.services.database_service import DatabaseService
health = DatabaseService.health_check()
print(health)  # {'status': 'healthy', 'database': 'connected', ...}
```

### Log Audit Event
```python
from api.services.audit_service import audit_service
from db.models import ActionEnum
from uuid import UUID

audit_service.log_action(
    user_id=UUID("..."),
    entity_type="Config",
    entity_id="user_config",
    action=ActionEnum.CONFIG_CHANGE,
    changes={"theme": "dark"},
    reason="User preference"
)
```

### Get Audit Trail
```python
trail = audit_service.get_user_audit_trail(
    user_id=UUID("..."),
    limit=50
)
for entry in trail:
    print(f"{entry['timestamp']}: {entry['action']}")
```

### Check Rate Limits
```bash
curl http://localhost:8000/api/monitoring/rate-limits/user-123
# Returns: remaining requests, reset time, per-endpoint limits
```

---

## Troubleshooting

### Database Won't Connect
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check logs
docker-compose -f docker-compose.prod.yml logs postgres
```

### Rate Limiting Not Working
```bash
# Verify it's enabled
echo $RATELIMIT_ENABLED  # Should be 'true'

# Check response headers
curl -v http://localhost:8000/api/chat/send | grep X-RateLimit
```

### Audit Trail Empty
```bash
# Verify audit service is being called
tail -f logs/app.log | grep audit

# Check database directly
psql -U devforge -d devforge -c "SELECT COUNT(*) FROM audit_logs;"
```

---

## Architecture Overview

```
Request → RateLimitMiddleware → RequestLoggingMiddleware → Route Handler
              ↓                          ↓                        ↓
         Check limits,           Generate ID,              Call service
         Add headers            Sanitize data              (uses DB)
                                                                 ↓
                                                         AuditService logs
                                                                 ↓
                                                         Database updated
                                                                 ↓
                                                         Response returned
```

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/devforge
ENCRYPTION_KEY=<generated_fernet_key>

# Recommended
LOG_LEVEL=INFO
RATELIMIT_ENABLED=true
ALLOWED_ORIGINS=http://localhost:3000

# Optional
ENVIRONMENT=production
DB_POOL_SIZE=10
SENTRY_DSN=<sentry_url>
```

---

## Performance Tips

1. **Increase pool size** for high concurrency:
   ```bash
   DB_POOL_SIZE=20 python main.py
   ```

2. **Use Redis** for distributed rate limiting:
   ```python
   # Configure RateLimiter to use Redis backend
   # (enhancement available)
   ```

3. **Batch audit writes** for high volume:
   ```python
   # Move audit logging to background queue
   # (enhancement available)
   ```

4. **Archive old logs**:
   ```bash
   # Move logs older than 30 days
   find logs -name "*.log" -mtime +30 -exec gzip {} \;
   ```

---

## Next Steps

1. ✓ Copy models: `cp db/models_v2.py db/models.py`
2. ✓ Update main.py with middleware and events
3. ✓ Migrate services to database
4. ✓ Run tests: `pytest tests/test_phase6_integration.py`
5. ✓ Deploy: `./scripts/deploy.sh`
6. ✓ Verify endpoints: `curl http://localhost:8000/api/monitoring/health`

---

## Documentation

- **Detailed Guide**: PHASE_6_IMPLEMENTATION_GUIDE.md
- **Integration Checklist**: INTEGRATION_CHECKLIST.md
- **Architecture**: PHASE_6_README.md
- **Completion Summary**: PHASE_6_SUMMARY.md
- **This File**: PHASE_6_QUICK_START.md (you are here)

---

## Support

Issues? Check:
1. Logs: `tail -f logs/app.log`
2. Tests: `pytest tests/test_phase6_integration.py -v`
3. Guides: See documentation list above

---

**Ready to integrate! You've got this! 🚀**
