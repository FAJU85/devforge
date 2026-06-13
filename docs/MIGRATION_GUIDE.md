# Database Migration & Rollout Guide

## Quick Start

### Development Setup (Local PostgreSQL)

```bash
# 1. Install dependencies
pip install -r requirements-db.txt

# 2. Create local PostgreSQL database
createdb devforge
createuser devforge -P  # Enter password when prompted

# 3. Run migrations
export DATABASE_URL="postgresql://devforge:password@localhost:5432/devforge"
alembic upgrade head

# 4. Verify tables created
psql devforge -c "\dt"
```

### Using Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: devforge
      POSTGRES_USER: devforge
      POSTGRES_PASSWORD: devforge
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  app:
    build: .
    environment:
      DATABASE_URL: postgresql://devforge:devforge@postgres:5432/devforge
      ENABLE_DB_SYNC: "false"
    ports:
      - "7860:7860"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

```bash
docker-compose up
```

---

## Phased Rollout Plan

### Phase 1: Feature Flag Off (Default) — Weeks 1-2

**Duration:** 2 weeks
**Feature Flag:** `enable_db_sync=false` (default)
**What Happens:**
- DB is initialized but unused
- All reads/writes go to localStorage
- Frontend doesn't know about DB
- Zero impact on users

**Deploy:**
```bash
git push origin claude/cool-feynman-4qdqpm
# GitHub Action runs: alembic upgrade head
# DB tables created, empty
# Feature flag environment defaults to false
```

**Verification:**
- [ ] DB tables exist (run `\dt` in psql)
- [ ] App starts without errors
- [ ] No breaking changes to old API (`/api/*`)
- [ ] localStorage still works

---

### Phase 2: Dual-Write (Canary 10%) — Weeks 2-3

**What Happens:**
- Feature flag: `enable_db_sync=true` for 10% of users
- Frontend: Writes to both localStorage + DB
- Backend: `/api/v2/` endpoints available
- Conflicts: localStorage is source-of-truth during this phase

**Activate:**
```bash
# In main.py or config file:
FEATURE_FLAGS = {
    "enable_db_sync": {
        "enabled": True,
        "rollout_percentage": 10,  # 10% of users
        "rules": [
            {"condition": "is_internal_user", "percentage": 100}  # All internal staff
        ]
    }
}
```

**Dual-Write Logic (Frontend):**
```javascript
// 1. Write to localStorage (fast, synchronous)
localStorage.setItem('df-chat', JSON.stringify(chatData));

// 2. Async POST to DB (don't block UI)
if (window.DEVFORGE_CONFIG.dbEnabled) {
  fetch('/api/v2/conversations', {
    method: 'POST',
    body: JSON.stringify({ name, repository_id })
  }).then(r => r.json())
    .then(conv => {
      // optionally save conv.id for future references
    })
    .catch(err => console.warn('DB sync failed:', err));
}
```

**Monitoring:**
- [ ] Monitor error rates in Rollbar/Sentry
- [ ] Check DB query latency (should be <100ms)
- [ ] Verify message counts match between localStorage and DB
- [ ] No data loss reported by canary users

**Gradual Increase:**
- Day 1-2: 10% (internal staff)
- Day 3-4: 10% (random users)
- Day 5-6: 25% (random users)
- Day 7+: 50% (ready for Phase 3)

---

### Phase 3: DB Primary (50-100%) — Weeks 3-4

**What Happens:**
- Feature flag: Gradually increase to 100%
- Frontend: Read from `/api/v2/`, fallback to localStorage if DB fails
- Backend: DB is source-of-truth, localStorage is cache

**Activate:**
```bash
# Day 1: 50%
FEATURE_FLAGS["enable_db_sync"]["rollout_percentage"] = 50

# Day 2: 75%
FEATURE_FLAGS["enable_db_sync"]["rollout_percentage"] = 75

# Day 3-4: 100%
FEATURE_FLAGS["enable_db_sync"]["rollout_percentage"] = 100
```

**Frontend Read Logic:**
```javascript
async function loadConversations() {
  if (!window.DEVFORGE_CONFIG.dbEnabled) {
    // Old path: read from localStorage
    return JSON.parse(localStorage.getItem('df-chat')).tabs;
  }
  
  try {
    // New path: read from DB
    const resp = await fetch('/api/v2/conversations?limit=100');
    if (resp.ok) return resp.json();
  } catch (e) {
    console.warn('DB failed, falling back to localStorage:', e);
  }
  
  // Fallback
  return JSON.parse(localStorage.getItem('df-chat')).tabs;
}
```

**Monitoring:**
- [ ] Verify 100% of requests routed to DB
- [ ] Check data consistency (DB ≈ localStorage)
- [ ] Monitor database CPU, disk, connections
- [ ] No timeout errors or slow queries

---

### Phase 4: localStorage Deprecation — Weeks 4-6

**What Happens:**
- localStorage becomes read-only (fallback only)
- Users see deprecation warning
- New writes only go to DB
- 30-day warning before full removal

**Warning Message:**
```javascript
if (isLocalStorageDependency) {
  showNotification(
    '⚠️ Your browser cache will be cleared in 30 days. ' +
    'All conversations are now stored securely in your account. ' +
    'No action needed!',
    'warning',
    30000
  );
}
```

**Cleanup:**
```python
# Week 4: Stop writing to localStorage
def save_conversation(conv_data):
    # OLD: localStorage.setItem('df-chat', ...)
    # NEW: Only DB
    db.add(Conversation(...))
    db.commit()
```

**Final Cutover:**
```bash
# Week 6: Remove localStorage read fallback
# Delete all localStorage handling code
# localStorage is no longer used
```

---

## Data Backfill (localStorage → PostgreSQL)

### Step 1: Extract localStorage from Sessions

**File: `scripts/extract_localStorage.py`**

```python
#!/usr/bin/env python3
"""Extract localStorage from active HF Spaces sessions."""

import json
from pathlib import Path
import subprocess

output_dir = Path("./backfill_dumps")
output_dir.mkdir(exist_ok=True)

# Query HF Spaces for active sessions with localStorage
# (Manual for now; would be automated in production)
sessions = [
    # { github_id: 123, github_login: "user1", localStorage: {...} }
]

for session in sessions:
    user_id = session["github_id"]
    filename = output_dir / f"user_{user_id}.json"
    
    with open(filename, "w") as f:
        json.dump(session, f, indent=2)
    
    print(f"Extracted user {session['github_login']}")
```

**Run:**
```bash
export DATABASE_URL="postgresql://..."
python scripts/extract_localStorage.py
```

### Step 2: Validate Extraction

**File: `scripts/validate_backfill.py`**

```python
#!/usr/bin/env python3
"""Validate backfill data before insertion."""

import json
from pathlib import Path

dumps_dir = Path("./backfill_dumps")
stats = {
    "total_users": 0,
    "total_conversations": 0,
    "total_messages": 0,
    "total_snippets": 0,
}

for dump_file in dumps_dir.glob("user_*.json"):
    with open(dump_file) as f:
        dump = json.load(f)
    
    stats["total_users"] += 1
    
    # Count conversations
    chat_data = dump.get("chat_data", {})
    for tab in chat_data.get("tabs", []):
        stats["total_conversations"] += 1
        stats["total_messages"] += len(tab.get("msgs", []))
    
    # Count snippets
    stats["total_snippets"] += len(dump.get("snippets_data", {}).get("snippets", []))

print(f"Backfill Stats:")
for key, val in stats.items():
    print(f"  {key}: {val}")
```

**Run:**
```bash
python scripts/validate_backfill.py
# Output:
# Backfill Stats:
#   total_users: 42
#   total_conversations: 1205
#   total_messages: 18532
#   total_snippets: 342
```

### Step 3: Dry-Run (Read-Only)

```bash
python scripts/backfill_localStorage.py --dry-run
# Verify counts match validation above
# No changes to DB
```

### Step 4: Execute Backfill

**File: `scripts/backfill_localStorage.py`**

```python
#!/usr/bin/env python3
"""Backfill localStorage data into PostgreSQL."""

import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from db.database import SessionLocal
from db.models import User, Conversation, Message, Snippet, UserPreset
import sys

def backfill_user(dump: dict, db, dry_run=False):
    """Backfill single user's data."""
    github_id = dump["github_id"]
    github_login = dump["github_login"]
    
    # Create/get user
    user = db.query(User).filter_by(github_id=github_id).first()
    if not user:
        user = User(
            github_id=github_id,
            github_login=github_login,
            github_name=dump.get("github_name"),
            github_avatar_url=dump.get("github_avatar_url"),
        )
        db.add(user)
        db.flush()
    
    # Backfill conversations
    chat_data = dump.get("chat_data", {})
    for tab in chat_data.get("tabs", []):
        conv = Conversation(
            id=uuid4(),
            user_id=user.id,
            name=tab.get("name", "Chat"),
            created_at=datetime.fromisoformat(tab.get("created_at", "2026-01-01T00:00:00"))
        )
        db.add(conv)
        db.flush()
        
        # Backfill messages
        for msg in tab.get("msgs", []):
            message = Message(
                conversation_id=conv.id,
                role=msg["role"],
                content=msg["content"],
                tokens_used=msg.get("tokens", 0),
                created_at=datetime.now()
            )
            db.add(message)
    
    # Backfill snippets
    for snippet in dump.get("snippets_data", {}).get("snippets", []):
        snip = Snippet(
            user_id=user.id,
            title=snippet["title"],
            language=snippet.get("language"),
            content=snippet["content"],
            created_at=datetime.now()
        )
        db.add(snip)
    
    if not dry_run:
        db.commit()
        print(f"✓ Backfilled user {github_login}")
    else:
        db.rollback()
        print(f"[DRY RUN] Would backfill user {github_login}")

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    db = SessionLocal()
    
    dumps_dir = Path("./backfill_dumps")
    count = 0
    
    for dump_file in sorted(dumps_dir.glob("user_*.json")):
        with open(dump_file) as f:
            dump = json.load(f)
        
        try:
            backfill_user(dump, db, dry_run=dry_run)
            count += 1
        except Exception as e:
            print(f"✗ Failed to backfill {dump_file}: {e}")
    
    print(f"\nBackfill complete: {count} users processed")
    db.close()
```

**Run:**
```bash
# Dry run first
python scripts/backfill_localStorage.py --dry-run

# Execute
python scripts/backfill_localStorage.py
```

---

## Post-Backfill Verification

```bash
# Connect to DB
psql $DATABASE_URL

# Verify row counts
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM messages;
SELECT COUNT(*) FROM snippets;

# Spot-check data
SELECT u.github_login, COUNT(c.id) as conv_count
FROM users u
LEFT JOIN conversations c ON c.user_id = u.id
GROUP BY u.id
LIMIT 10;
```

---

## Rollback Procedures

### If Phase 2 Fails (Canary Issues)

```bash
# Option 1: Disable feature flag
FEATURE_FLAGS["enable_db_sync"]["rollout_percentage"] = 0

# Option 2: Delete bad data (if corruption detected)
psql $DATABASE_URL << EOF
DELETE FROM messages WHERE created_at > NOW() - INTERVAL '1 hour';
DELETE FROM conversations WHERE created_at > NOW() - INTERVAL '1 hour';
VACUUM;
EOF

# Restart app
docker restart devforge-app
```

### If Phase 3 Fails (Full Rollout)

```bash
# Revert to localStorage-only
git revert <commit-hash>
git push origin claude/cool-feynman-4qdqpm

# Disable DB sync entirely
FEATURE_FLAGS["enable_db_sync"]["rollout_percentage"] = 0

# Users will see localStorage data again (no loss)
# DB can remain as historical backup
```

### Full Data Loss Scenario

```bash
# Restore from backup
aws s3 cp s3://devforge-backups/postgres-2026-06-11.sql /tmp/
psql $DATABASE_URL < /tmp/postgres-2026-06-11.sql

# Re-enable sync
FEATURE_FLAGS["enable_db_sync"]["rollout_percentage"] = 10
```

---

## Monitoring During Rollout

### Key Metrics

```bash
# Database connections
SELECT count(*) FROM pg_stat_activity;

# Slow queries
SELECT query, calls, mean_time FROM pg_stat_statements 
WHERE mean_time > 100 ORDER BY mean_time DESC;

# Disk usage
SELECT pg_size_pretty(pg_database_size('devforge'));
```

### Alerts to Setup

1. **DB Connection Pool Exhaustion**
   - Alert if > 25 active connections
   - Action: Scale pool or investigate slow queries

2. **Query Latency**
   - Alert if p95 > 500ms
   - Action: Review slow query log, add indexes

3. **Sync Error Rate**
   - Alert if > 1% of dual-writes fail
   - Action: Check logs, disable feature flag

4. **Data Consistency**
   - Alert if message counts differ > 5%
   - Action: Re-run backfill or manual sync

---

## Rollback Checklist

- [ ] Disable feature flag: `enable_db_sync=false`
- [ ] Monitor error rates for 30 minutes
- [ ] Query DB for data integrity issues
- [ ] Delete corrupted data if needed (with backups)
- [ ] Communicate with affected users
- [ ] Schedule post-mortem
- [ ] Document root cause
- [ ] Deploy fix before re-enabling

---

## Success Criteria

**Phase 1:** ✅ DB initialized, no errors for 7 days
**Phase 2:** ✅ Dual-writes working, <1% error rate, data consistent
**Phase 3:** ✅ 100% routed to DB, no timeouts, DB latency <100ms
**Phase 4:** ✅ localStorage fully deprecated, zero technical debt

**Go/No-Go Checklist:**
- [ ] All migration tests passing
- [ ] Canary users report no issues
- [ ] Monitoring shows healthy metrics
- [ ] Data consistency verified
- [ ] Backup strategy tested
- [ ] Rollback plan documented

---

## FAQ

**Q: What if I lose localStorage while DB sync is disabled?**
A: No data loss—just restart with a fresh localStorage. DB will sync later.

**Q: Can users access old localStorage data after migration?**
A: Yes, during Phase 2-3 they can access via fallback. After Phase 4, only new data in DB.

**Q: How long will backfill take?**
A: ~1 hour for 1M messages. Run during maintenance window.

**Q: What if Postgres goes down?**
A: Frontend falls back to localStorage during Phase 2-3. After Phase 4, feature breaks until DB recovered.

**Q: Can I run both v1 and v2 APIs simultaneously?**
A: Yes! v1 (`/api/*`) stays unchanged. v2 (`/api/v2/*`) is optional. Feature flag controls routing.
