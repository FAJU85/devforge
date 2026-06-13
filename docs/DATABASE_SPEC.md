# DevForge Database Specification

## Overview

This document describes the persistent database layer for DevForge, which replaces pure localStorage-based state with a PostgreSQL backend while maintaining backward compatibility.

## Database Architecture

### Connection Strategy
- **Primary DB:** PostgreSQL 13+
- **Connection Pooling:** SQLAlchemy QueuePool (10 connections, max overflow 20)
- **Pool Recycling:** 3600 seconds (stale connection cleanup)
- **Health Check:** `pool_pre_ping=true` (test before use)

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/devforge
DB_POOL_SIZE=10                    # Core pool connections
DB_MAX_OVERFLOW=20                 # Additional overflow connections
DB_POOL_RECYCLE=3600               # Recycle stale connections (seconds)
DB_POOL_PRE_PING=true              # Test connections before use
SQLALCHEMY_ECHO=false              # Log SQL statements
ENCRYPTION_KEY=<32-byte-string>    # For encrypting API keys
```

## Schema Design

### 1. Users Table
Stores GitHub-authenticated users.

```sql
users {
  id: UUID PRIMARY KEY
  github_id: INT UNIQUE NOT NULL                -- GitHub user ID
  github_login: VARCHAR(255) UNIQUE NOT NULL    -- GitHub username
  github_avatar_url: TEXT
  github_name: VARCHAR(255)
  github_email: VARCHAR(255)
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
}
```

**Indexes:**
- `github_id` (unique, for OAuth lookup)
- `github_login` (unique, for username queries)

**Rationale:** 
- GitHub ID is immutable and primary OAuth key
- Login may change, but we track it for admin/debugging

---

### 2. Repositories Table
Tracks GitHub repositories the user has connected.

```sql
repositories {
  id: UUID PRIMARY KEY
  user_id: UUID FK -> users.id (CASCADE)
  owner: VARCHAR(255) NOT NULL        -- GitHub org/user
  name: VARCHAR(255) NOT NULL         -- Repo name
  branch: VARCHAR(255) DEFAULT 'main' -- Current branch
  last_accessed: TIMESTAMP
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
  
  UNIQUE INDEX (user_id, owner, name)
}
```

**Indexes:**
- `(user_id, owner, name)` unique compound
- `user_id` for lookups by user

**Rationale:**
- User + owner + name uniquely identifies a repo
- Tracks last access for sorting in UI
- `branch` caches current branch without API calls

---

### 3. Conversations Table
Chat conversations (tabs in the UI).

```sql
conversations {
  id: UUID PRIMARY KEY
  user_id: UUID FK -> users.id (CASCADE)
  repository_id: UUID FK -> repositories.id (SET NULL)  -- Optional
  name: VARCHAR(255) DEFAULT 'Chat'
  is_active: BOOLEAN DEFAULT TRUE
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
  
  INDEX (user_id, created_at)  -- For listing recent chats
}
```

**Indexes:**
- `(user_id, created_at)` for pagination & sorting

**Rationale:**
- Each tab is a conversation
- `repository_id` optional (can chat without selecting a repo)
- `is_active` for soft-delete or archived chats
- `created_at` for sorting by recency

---

### 4. Messages Table
Chat messages within conversations.

```sql
messages {
  id: UUID PRIMARY KEY
  conversation_id: UUID FK -> conversations.id (CASCADE)
  role: VARCHAR(50) NOT NULL           -- 'user', 'assistant'
  content: TEXT NOT NULL               -- Full message content
  tokens_used: INT DEFAULT 0           -- Token consumption tracking
  created_at: TIMESTAMP DEFAULT NOW()
  
  INDEX (conversation_id, created_at)  -- For paginated retrieval
}
```

**Indexes:**
- `(conversation_id, created_at)` for message pagination

**Rationale:**
- Role determines display (user vs. assistant)
- `tokens_used` for billing/analytics
- Content stored as-is (no compression, preserves formatting)

---

### 5. ConversationFiles Table
Files selected in a conversation for context.

```sql
conversation_files {
  id: UUID PRIMARY KEY
  conversation_id: UUID FK -> conversations.id (CASCADE)
  file_path: VARCHAR(1024) NOT NULL
  file_size: INT
  created_at: TIMESTAMP DEFAULT NOW()
}
```

**Rationale:**
- Track which files were used in each conversation
- `file_size` for token count estimation
- Cascade delete when conversation deleted

---

### 6. Snippets Table
User's saved code snippets (similar to localStorage snippets).

```sql
snippets {
  id: UUID PRIMARY KEY
  user_id: UUID FK -> users.id (CASCADE)
  title: VARCHAR(255) NOT NULL
  language: VARCHAR(50)                -- 'python', 'typescript', etc.
  content: TEXT NOT NULL
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
}
```

**Rationale:**
- Simple storage for saved code snippets
- `language` for syntax highlighting hints
- Sortable by created_at or alphabetic on frontend

---

### 7. UserPresets Table
Saved instruction presets (rules + skills + model config).

```sql
user_presets {
  id: UUID PRIMARY KEY
  user_id: UUID FK -> users.id (CASCADE)
  preset_name: VARCHAR(255) NOT NULL
  instructions: TEXT
  rules: TEXT
  skills: JSON DEFAULT []              -- Array of skill names
  ai_model: VARCHAR(255)               -- 'haiku', 'sonnet', 'opus', etc.
  provider: VARCHAR(50)                -- 'anthropic', 'groq', 'hf'
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
  
  UNIQUE INDEX (user_id, preset_name)
}
```

**Rationale:**
- Presets bundle: instructions + rules + model choice
- `skills` as JSON array for flexible additions
- User can have multiple presets and switch between them

---

### 8. UserSecrets Table
Encrypted API keys and credentials.

```sql
user_secrets {
  id: UUID PRIMARY KEY
  user_id: UUID FK -> users.id (CASCADE)
  secret_type: VARCHAR(50) NOT NULL   -- 'anthropic_key', 'groq_key', 'hf_token'
  secret_value_encrypted: VARCHAR(2048) NOT NULL  -- Fernet-encrypted value
  created_at: TIMESTAMP DEFAULT NOW()
  updated_at: TIMESTAMP DEFAULT NOW()
  
  UNIQUE INDEX (user_id, secret_type)
}
```

**Rationale:**
- Fernet (symmetric) encryption for secrets at-rest
- One secret per type per user (easy lookup)
- Encrypted value is ~2KB (base64-encoded ciphertext)
- `updated_at` for rotation tracking

**Encryption:**
- Uses `cryptography.fernet` (AES-128)
- Key derived from `ENCRYPTION_KEY` env var or SHA256 of dev phrase
- Decrypt only on retrieval, never store plaintext

---

### 9. UserSessions Table
API session tokens (optional, for token-based auth beyond OAuth).

```sql
user_sessions {
  id: UUID PRIMARY KEY
  user_id: UUID FK -> users.id (CASCADE)
  token_hash: VARCHAR(255) UNIQUE NOT NULL  -- SHA256(token)
  expires_at: TIMESTAMP NOT NULL
  created_at: TIMESTAMP DEFAULT NOW()
  
  INDEX (token_hash)
}
```

**Rationale:**
- For API clients or long-lived sessions
- Store hash, not plaintext token (security best practice)
- `expires_at` for cleanup/invalidation

---

## Data Flow: localStorage ↔ PostgreSQL

### Phase 1: Feature Flag Disabled (Default)
- Frontend: Read/write localStorage only
- Backend: DB initialized but unused
- No performance impact
- Easy rollback

### Phase 2: Dual-Write (Feature Flag 10-50%)
- Frontend:
  1. Write to localStorage (fast, synchronous)
  2. Async POST to `/api/v2/` endpoints
- Backend:
  - Write to DB (asynchronous, failures don't block UI)
  - Return DB record ID for future references
- Conflicts: localStorage is source-of-truth during this phase

### Phase 3: DB-First (Feature Flag 50-100%)
- Frontend:
  1. Check `X-DB-Enabled` header from `/api/config`
  2. If DB enabled: read from `/api/v2/` endpoints
  3. Fallback to localStorage if DB unavailable
  4. Keep localStorage in sync for offline support
- Backend:
  - All reads come from DB
  - Return DB state to frontend

### Phase 4: localStorage Deprecation
- Frontend: localStorage as read-only cache (30-day warning)
- Backend: Single source of truth (DB)
- Cleanup: Remove localStorage writes (keep reads for offline)

---

## API v2 Endpoints (Database-Backed)

### Conversations
```
GET    /api/v2/conversations
POST   /api/v2/conversations
GET    /api/v2/conversations/{id}
PUT    /api/v2/conversations/{id}
DELETE /api/v2/conversations/{id}
```

### Messages
```
GET    /api/v2/conversations/{conversation_id}/messages?limit=50&offset=0
POST   /api/v2/conversations/{conversation_id}/messages
DELETE /api/v2/messages/{id}
```

### Repositories
```
GET    /api/v2/repositories
POST   /api/v2/repositories
PUT    /api/v2/repositories/{id}
DELETE /api/v2/repositories/{id}
```

### Snippets
```
GET    /api/v2/snippets
POST   /api/v2/snippets
PUT    /api/v2/snippets/{id}
DELETE /api/v2/snippets/{id}
```

### Presets
```
GET    /api/v2/presets
POST   /api/v2/presets
PUT    /api/v2/presets/{id}
DELETE /api/v2/presets/{id}
```

### Secrets
```
GET    /api/v2/secrets/{type}
POST   /api/v2/secrets
DELETE /api/v2/secrets/{type}
```

*(Full endpoint specs in API_SPEC.md)*

---

## Indexes & Query Optimization

| Table | Index | Reason |
|-------|-------|--------|
| users | (github_id) | OAuth lookup |
| repositories | (user_id, owner, name) | Unique constraint |
| conversations | (user_id, created_at) | List & sort by recency |
| messages | (conversation_id, created_at) | Paginate messages |
| user_presets | (user_id, preset_name) | Unique constraint |
| user_secrets | (user_id, secret_type) | Unique constraint |
| user_sessions | (token_hash) | Validate session token |

**Total: 9 core tables, 10 indexes**

---

## Backfill Strategy (localStorage → PostgreSQL)

### Step 1: Extract localStorage
- Query: All active browser sessions
- Parse: `df-chat`, `df-enhance`, `df-snippets`, `df-presets`, `df-prompt-history`
- Dump to JSON files (one per user)

### Step 2: Validate
- Count messages in localStorage vs. expected
- Verify schema compatibility
- Dry-run INSERT without COMMIT

### Step 3: Backfill
```python
# scripts/backfill_localStorage.py
for user in extracted_users:
    # Create user record (GitHub ID must exist)
    # Create conversations from tabs
    # Create messages from message history
    # Create snippets, presets
    # Log migration stats
```

### Step 4: Verification
- Count records post-migration
- Spot-check random conversations
- Monitor error rates for 24 hours

### Rollback
- Keep 30-day localStorage backup
- DB DELETE (cascade) if needed
- Users can export localStorage as .json

---

## Performance & Limits

### Connection Pooling
- **Pool Size:** 10 (default)
- **Overhead:** ~50MB (idle connections)
- **Max Concurrent:** 30 (10 + 20 overflow)
- **Timeout:** 30 seconds (query timeout recommended in PostgreSQL)

### Data Limits
- **Max conversation history:** Unlimited (paginated on retrieval)
- **Max file path length:** 1024 chars
- **Max encrypted secret:** 2048 chars (base64 overhead ~1.33x)
- **Max preset JSON:** 64KB (skills array)

### Expected Performance
| Operation | Latency | Notes |
|-----------|---------|-------|
| Create conversation | <50ms | Insert + return |
| Fetch 50 messages | <100ms | With indexes |
| List 100 conversations | <200ms | Sorted by created_at |
| Search conversations | <500ms | Full-text search (optional future) |
| Decrypt secret | <10ms | Fernet overhead minimal |

---

## Monitoring & Maintenance

### Health Check Endpoint
```
GET /api/v2/health
Returns: { "db": "ok|error", "latency_ms": 5 }
```

### Metrics to Track
- Connection pool utilization
- Slow query log (>500ms)
- Deadlocks (PostgreSQL pg_stat_statements)
- Disk usage (conversation size)

### Backup Strategy
- **Frequency:** Daily (automated)
- **Retention:** 30 days
- **Test restores:** Weekly

### Cleanup
- Archive conversations inactive >90 days (optional)
- Remove expired sessions nightly
- Vacuum analyze monthly (PostgreSQL maintenance)

---

## Security Considerations

### Access Control
- Authenticate via GitHub OAuth or session token
- Row-level security: Users can only see their own data (enforced at application layer)
- API tokens: Hash stored, plaintext never logged

### Encryption
- Secrets encrypted at rest (Fernet)
- Secrets decrypted only on retrieval
- Connection to DB: Use `sslmode=require` in production

### SQL Injection Prevention
- Use parameterized queries (SQLAlchemy ORM)
- Validate UUIDs and enums
- No dynamic SQL in migrations

### Data Retention
- Users can request data export (`GET /api/v2/export`)
- GDPR: Support data deletion (cascade delete via users table)
- Conversation content: No automatic purge (user controls retention)

---

## Testing

### Unit Tests (`tests/test_db.py`)
```python
def test_create_user():
    user = User(github_id=123, github_login="testuser")
    db.add(user)
    db.commit()
    assert user.id is not None

def test_cascade_delete_conversations():
    # Delete user → conversations deleted automatically
```

### Integration Tests (`tests/test_db_api.py`)
```python
def test_create_conversation_endpoint(client, user_token):
    resp = client.post(
        "/api/v2/conversations",
        json={"name": "Test"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 201
```

### Migration Tests (`tests/test_migrations.py`)
```python
def test_migration_001_creates_tables():
    # Upgrade and verify all tables exist
    # Downgrade and verify rollback works
```

---

## Future Enhancements

1. **Full-Text Search:** Add tsvector columns for conversation search
2. **Soft-Delete:** Add `deleted_at` column instead of hard delete
3. **Activity Logs:** Track who edited what and when
4. **Conversation Sharing:** Add `shared_with` column for read-only access
5. **Analytics:** Track token usage, model performance, user behavior
6. **Read Replicas:** Scale reads without impacting writes

---

## Rollout Checklist

- [ ] Database provisioned (Heroku Postgres, AWS RDS, or Railway)
- [ ] Run Alembic migrations: `alembic upgrade head`
- [ ] Backfill localStorage data
- [ ] Deploy with feature flag: `enable_db_sync=false`
- [ ] Monitor error rates for 24h
- [ ] Enable canary: `enable_db_sync=10%`
- [ ] Gradual rollout: 10% → 50% → 100%
- [ ] Deprecate localStorage (30-day warning)
- [ ] Full cutover complete
