# Backfill Scripts — localStorage to PostgreSQL Migration

These scripts help migrate user data from browser localStorage to PostgreSQL during the feature flag rollout.

## Overview

The backfill process has 3 stages:

1. **Extract** — Export localStorage data from active sessions (manual + export script)
2. **Validate** — Check data consistency before migration
3. **Backfill** — Migrate data to PostgreSQL (with dry-run support)

## Prerequisites

```bash
pip install -r requirements-db.txt

export DATABASE_URL="postgresql://devforge:devforge@localhost:5432/devforge"
```

## Step 1: Extract localStorage Dump

### Manual Export (Current Method)

For HuggingFace Spaces or web deployments:

```javascript
// Run this in browser console to export a user's localStorage
const dump = {
  github_id: <from API>,
  github_login: <from API>,
  github_name: <from API>,
  github_avatar_url: <from API>,
  chat_data: JSON.parse(localStorage.getItem("df-chat") || "{}"),
  enhance_data: JSON.parse(localStorage.getItem("df-enhance") || "{}"),
  snippets_data: JSON.parse(localStorage.getItem("df-snippets") || "{}"),
  presets_data: JSON.parse(localStorage.getItem("df-presets") || "{}"),
};

// Save to file
const blob = new Blob([JSON.stringify(dump)], {type: "application/json"});
const url = URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = `user_${dump.github_id}.json`;
a.click();
```

### Automated Export Script (Production)

For production use, create a script to extract all users:

```bash
# TODO: Implement automated extraction
# Would use session data + GitHub API to extract all active users
```

## Step 2: Validate Dump File

Before running backfill, validate the exported data:

```bash
python scripts/validate_backfill.py dumps/user_12345.json
```

**Output:**
```
Validating: dumps/user_12345.json

============================================================
DUMP FILE STATISTICS
============================================================
Total users:            1
Total conversations:    5
Total messages:         42
Total snippets:         8
Total presets:          3

✓ Dump file is valid and ready for backfill
```

### Multi-User Dump

To backfill multiple users at once, create an array:

```bash
cat > dumps/all_users.json << 'EOF'
[
  {
    "github_id": 12345,
    "github_login": "user1",
    "chat_data": { ... },
    ...
  },
  {
    "github_id": 67890,
    "github_login": "user2",
    "chat_data": { ... },
    ...
  }
]
EOF

python scripts/validate_backfill.py dumps/all_users.json
```

## Step 3: Dry-Run Backfill

Always test with `--dry-run` first:

```bash
python scripts/backfill_localStorage.py --dry-run dumps/all_users.json
```

**Output:**
```
Loaded 2 users from dump

[DRY RUN] Backfilled user user1
[DRY RUN] Backfilled user user2

============================================================
BACKFILL STATISTICS
============================================================
Users created:          2
Conversations created:  10
Messages created:       150
Snippets created:       20
Presets created:        5
Errors:                 0

[DRY RUN] No data was modified. Run without --dry-run to execute.
```

### What Dry-Run Does

- ✅ Validates all data
- ✅ Creates database records
- ✅ Reports statistics
- ✅ Rolls back all changes (no data persisted)
- ✅ Safe to run multiple times

## Step 4: Execute Backfill

Once dry-run succeeds, run the actual migration:

```bash
python scripts/backfill_localStorage.py dumps/all_users.json
```

**Output:**
```
Loaded 2 users from dump

✓ Backfilled user user1
✓ Backfilled user user2

============================================================
BACKFILL STATISTICS
============================================================
Users created:          2
Conversations created:  10
Messages created:       150
Snippets created:       20
Presets created:        5
Errors:                 0

✓ Backfill complete!
```

### Verify in Database

```bash
psql $DATABASE_URL << 'EOF'
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM messages;

-- Check specific user
SELECT * FROM users WHERE github_login = 'user1';
SELECT COUNT(*) FROM conversations WHERE user_id = (SELECT id FROM users WHERE github_login = 'user1');
EOF
```

## Error Handling

### Duplicate User

If a user already exists in the database:

```bash
# Script will skip creation and reuse existing user
# All data will be added to their existing conversations
```

### Invalid Data

If dump file has invalid records:

```bash
# Dry-run will show errors:
# [DRY RUN] Backfilled user user1
# Errors:                 2
# 
# Errors:
#   - User user2: Missing required field
#   - Conversation in user1: Invalid message structure

# Fix dump file and retry
```

### Database Connection Error

```bash
# Ensure DATABASE_URL is set
export DATABASE_URL="postgresql://user:pass@host:5432/devforge"

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# If still fails, check:
# 1. PostgreSQL is running
# 2. Database exists
# 3. Credentials are correct
# 4. Network connection is available
```

## Rollback

### Rollback After Backfill

If issues occur after backfill:

```bash
# Option 1: Delete specific user's data
psql $DATABASE_URL << 'EOF'
DELETE FROM users WHERE github_login = 'user1';
-- Cascade delete: conversations, messages, snippets, presets removed automatically
VACUUM;
EOF

# Option 2: Restore from backup
aws s3 cp s3://backups/postgres-2026-06-11.sql /tmp/
psql $DATABASE_URL < /tmp/postgres-2026-06-11.sql

# Option 3: Disable feature flag and restart
export ENABLE_DB_SYNC=false
docker restart devforge
```

## Performance Notes

### Timing

- **1 user, 10 convs, 100 msgs:** ~100ms
- **100 users, 1000 convs, 10K msgs:** ~5s
- **1000 users, 10K convs, 100K msgs:** ~60s

### Batch Size

For very large datasets, process in batches:

```bash
# Split dump into chunks
split -l 100 dumps/all_users.json dumps/batch_

# Process each batch
for batch in dumps/batch_*; do
  python scripts/backfill_localStorage.py --dry-run "$batch"
  python scripts/backfill_localStorage.py "$batch"
done
```

### Database Optimization

```bash
# After backfill, optimize database
psql $DATABASE_URL << 'EOF'
ANALYZE;
VACUUM ANALYZE;
REINDEX;
EOF
```

## Monitoring During Backfill

```bash
# In another terminal, monitor progress
watch -n 2 "psql $DATABASE_URL -c 'SELECT COUNT(*) FROM users; SELECT COUNT(*) FROM messages;'"
```

## Troubleshooting

### Script Won't Run

```bash
# Make executable
chmod +x scripts/backfill_localStorage.py

# Run with python3 explicitly
python3 scripts/backfill_localStorage.py --dry-run dumps/test.json
```

### Import Errors

```bash
# Ensure you're in the devforge directory
cd /path/to/devforge

# Verify virtualenv (if using one)
which python
```

### Encoding Issues

If dump file has non-UTF-8 characters:

```bash
# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 dumps/user.json > dumps/user_utf8.json
```

## FAQ

**Q: Can I backfill while feature flag is off?**
A: Yes! The scripts work independently of the feature flag. Data will be in DB but unused until flag is enabled.

**Q: What if a user has 100K messages?**
A: Should still work, but test with dry-run first. May take 30-60s for single user.

**Q: Can I backfill in production?**
A: Yes, but:
1. Run during low-traffic hours
2. Ensure database backups exist
3. Monitor CPU/memory during backfill
4. Have rollback plan ready

**Q: Will localStorage data be deleted?**
A: No! Scripts only READ from localStorage. Original data remains in browser cache.

**Q: What about data added after backfill?**
A: Covered by Phase 2 (dual-write). New data goes to both localStorage + DB.

## Next Steps

After backfill completes:

1. ✅ Enable feature flag for 10% of users
   ```bash
   export DB_SYNC_ROLLOUT_PERCENTAGE=10
   ```

2. ✅ Monitor for 24-48 hours
   - Check Rollbar/Sentry for errors
   - Verify data consistency (DB vs localStorage)
   - Check API latency

3. ✅ Gradually increase rollout
   - 10% → 25% → 50% → 100%
   - Each step should run for 1-2 days

4. ✅ Deprecate localStorage
   - Show 30-day warning to users
   - Remove localStorage writes
   - Keep reads for offline support

---

For more info, see:
- `docs/DATABASE_SPEC.md` — Schema design
- `docs/MIGRATION_GUIDE.md` — Full rollout strategy
- `docs/API_V2_SPEC.md` — API endpoints
