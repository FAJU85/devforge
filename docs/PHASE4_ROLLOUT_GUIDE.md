# Phase 4: Canary Rollout Operations Guide

## Overview

This guide covers the 6-week canary rollout from 0% → 100% of users on PostgreSQL.

**Timeline:**
- Week 1: Feature flag OFF (Phase 1 state)
- Week 2: 10% canary (internal staff)
- Week 3: 25% early adopters
- Week 4: 50% half rollout
- Week 5: 75% most users
- Week 6: 100% full rollout + deprecation planning

---

## Pre-Rollout Checklist

### ✅ Mandatory Before Starting

- [ ] Database backups configured (automated daily)
- [ ] Rollbar/Sentry error monitoring enabled
- [ ] PostHog analytics ready
- [ ] All Phase 3 tests passing locally
- [ ] Backfill scripts tested with dummy data
- [ ] Feature flag environment variables documented
- [ ] Monitoring dashboards created (Datadog, CloudWatch, or custom)
- [ ] Team briefing completed (what to watch for)
- [ ] Rollback procedure documented and tested
- [ ] On-call rotation established for 6 weeks

### ✅ Helpful But Optional

- [ ] Automated alerting rules created
- [ ] User communication templates prepared (email, banner)
- [ ] Load testing done on staging environment
- [ ] Performance baseline established (historical metrics)
- [ ] Database query optimization completed
- [ ] Connection pooling tuned for peak load

---

## Canary Stages Configuration

### Stage 1: Week 1 (0% — Phase 1 State)

**Configuration:**
```bash
export ENABLE_DB_SYNC=false
export DB_SYNC_ROLLOUT_PERCENTAGE=0
```

**What's happening:**
- Feature flag disabled
- All data still in localStorage
- API v2 endpoints available but unused
- Zero user impact

**What to monitor:**
- API latency (baseline)
- Error rate (baseline)
- Rollbar/Sentry (look for any regressions)

**Exit criteria:**
- All metrics stable
- No regression from Phase 3
- Ready for canary?

---

### Stage 2: Week 2 (10% — Canary)

**Configuration:**
```bash
export ENABLE_DB_SYNC=true
export DB_SYNC_ROLLOUT_PERCENTAGE=10
```

**Users included:**
- Internal staff (devs, designers, PMs)
- Early adopters (opt-in beta testers)
- ~10% of active users

**What's happening:**
- Database persistence enabled
- Dual-write (localStorage + DB)
- v2 API endpoints handling real data
- Feature flag header returned: `X-DB-Enabled: true|false`

**What to monitor:**
```
✓ API latency p95 < 150ms (target)
✓ Error rate < 0.1% (target)
✓ DB connection pool < 60% utilized
✓ Data consistency > 99.9%
✓ Message count matches (DB ≈ localStorage)
✓ No data loss detected
```

**Daily checks:**
- Morning: Review overnight metrics
- Midday: Check error rate in Rollbar
- End of day: Verify data consistency
- Check if any users reported issues

**Health endpoint:**
```bash
curl http://localhost:7860/api/v2/health/detailed

# Expected response:
{
  "overall_healthy": true,
  "api": {"api_responding": true, "api_latency_ok": true, ...},
  "database": {"db_responding": true, "db_latency_ok": true, ...},
  "data": {"data_consistent": true, "no_data_loss": true}
}
```

**Metrics endpoint:**
```bash
curl http://localhost:7860/api/v2/metrics

# Shows real-time metrics:
{
  "api_latency_p95_ms": 45.23,
  "error_rate_percent": 0.05,
  "db_connection_pool_utilization_percent": 35,
  "data_consistency_match_percent": 99.95,
  ...
}
```

**Exit criteria (after 1-2 days):**
- ✅ All canary metrics green
- ✅ No data loss detected
- ✅ Zero new errors in Rollbar
- ✅ User feedback positive (if collected)
- Ready for 25%?

**Rollback trigger:**
```
IMMEDIATE ROLLBACK if:
- Error rate > 1%
- Latency p95 > 500ms
- Data loss > 0.1%
- Database unavailable > 5 minutes
```

---

### Stage 3: Week 3 (25% — Early Adopters)

**Configuration:**
```bash
export DB_SYNC_ROLLOUT_PERCENTAGE=25
```

**Users included:**
- All from Stage 2
- Additional 15% early adopters

**Targets:**
```
✓ API latency p95 < 150ms
✓ Error rate < 0.15%
✓ DB connection pool < 70%
✓ Data consistency > 99.8%
```

**What to monitor:**
- Same as Stage 2, plus:
  - Database CPU usage
  - Slow query log (queries > 500ms)
  - Connection pool growth
  - Message throughput (msgs/sec)

**Daily routine:**
- Export metrics: `python scripts/export_metrics.py`
- Review dashboard (Datadog/CloudWatch)
- Spot-check data consistency (random samples)
- Check team Slack for user reports

**Exit criteria:**
- Same as Stage 2
- Ready for 50%?

---

### Stage 4: Week 4 (50% — Half Rollout)

**Configuration:**
```bash
export DB_SYNC_ROLLOUT_PERCENTAGE=50
```

**Users included:**
- 50% of all active users

**Targets:**
```
✓ API latency p95 < 200ms (slightly relaxed)
✓ Error rate < 0.2%
✓ DB connection pool < 80%
✓ Data consistency > 99.5%
```

**What's different:**
- Significant database load increase
- Connection pool utilization climbing
- More real-world edge cases emerge
- Customer feedback loop important

**Monitoring intensity:**
- Reduce to "moderate" (no longer "intensive")
- Still daily checks
- Can shift to 8 AM + 6 PM checks instead of continuous

**Exit criteria:**
- All metrics within targets
- No unexpected behavior under 50% load
- Database scaling not needed (yet)
- Ready for 75%?

---

### Stage 5: Week 5 (75% — Most Users)

**Configuration:**
```bash
export DB_SYNC_ROLLOUT_PERCENTAGE=75
```

**Users included:**
- 75% of all active users
- Only conservative users still on localStorage

**Targets:**
```
✓ API latency p95 < 250ms
✓ Error rate < 0.25%
✓ DB connection pool < 85%
✓ Data consistency > 99.0%
```

**What's different:**
- Heaviest load week (except 100%)
- Stress-test the database
- Last chance to optimize before full rollout
- Prepare for 100% (deprecation planning)

**Exit criteria:**
- All metrics OK
- Database scaling not needed
- Ready for full rollout?

---

### Stage 6: Week 6 (100% — Full Rollout + Deprecation)

**Configuration:**
```bash
export DB_SYNC_ROLLOUT_PERCENTAGE=100
```

**Users included:**
- All active users
- No one on localStorage (feature flag detection only)

**Targets:**
```
✓ API latency p95 < 300ms
✓ Error rate < 0.3%
✓ DB connection pool < 90%
✓ Data consistency > 98.0% (some tolerance)
```

**What's different:**
- 100% of traffic on DB
- Baseline for future comparison
- Begin localStorage deprecation (30-day warning)
- Monitor steady state

**Deprecation plan:**
```
Week 6: Show in-app warning
  "Your conversation data is now safely stored in your account.
   We're preparing to retire browser cache support in 30 days.
   No action needed!"

Week 9: Remove localStorage writes
  - Keep localStorage reads for offline support
  - All new data goes to DB only
  - Migration complete

Week 12: Remove localStorage entirely
  - Sunset browser cache feature
  - Offline support via sync queue (future)
```

---

## Monitoring Dashboard Setup

### Key Metrics to Track

```
Real-time (update every 1 min):
├─ API Latency (p50, p95, p99)
├─ Error Rate (%)
├─ Request Count (req/sec)
├─ DB Connection Pool (%)
├─ DB Query Latency (avg, p95)
└─ Feature Flag Distribution (%)

Hourly:
├─ Data Consistency (%)
├─ Message Throughput (convs/hour, msgs/hour)
├─ User Activity (active users, new conversations)
└─ Error Types (breakdown by endpoint)

Daily:
├─ Database Growth (GB)
├─ Slow Query Log (queries > 500ms)
├─ Rollbar Error Summary
├─ Customer Feedback (support tickets)
└─ Cost Metrics (DB calls, API invocations)
```

### Example Monitoring Queries

**PostgreSQL queries:**
```sql
-- Current connection pool usage
SELECT 
  datname, 
  usename, 
  count(*) as connections
FROM pg_stat_activity
GROUP BY datname, usename;

-- Slow queries
SELECT 
  mean_exec_time, 
  query
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC;

-- Table sizes
SELECT 
  schemaname, 
  tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Conversation/message counts
SELECT 
  'conversations' as entity, 
  COUNT(*) as count
FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages;
```

**API metrics endpoint:**
```bash
# Every minute, fetch and aggregate
curl http://localhost:7860/api/v2/metrics > metrics_$(date +%s).json

# After 24 hours, analyze
python scripts/analyze_metrics.py metrics_*.json
```

---

## Incident Response Procedures

### If Error Rate Spikes > 1%

**Immediate (0-5 min):**
1. Confirm alert is real (check Rollbar/Sentry)
2. Identify affected endpoint (filter by path)
3. Note if affecting DB users or all users

**Short term (5-30 min):**
1. Check recent code changes (git log)
2. Review database metrics (latency, connections)
3. Look for correlation with API endpoint or user segment
4. Check GitHub issues / customer reports

**Decision point:**
- If isolated to small cohort: Monitor closely, don't rollback
- If widespread: Proceed to rollback

### If Latency Spikes > 500ms p95

**Immediate:**
1. Check database connection pool utilization
2. Check for slow queries (pg_stat_statements)
3. Check if specific endpoint affected

**Short term:**
1. Increase DB connection pool size (temporary)
2. Run ANALYZE on tables (statistics update)
3. Add index to slow query (if safe)

**If doesn't resolve in 30 min:**
- Rollback to previous stage

### If Data Loss Detected

**Immediate:**
1. STOP ALL WRITES (pause DB sync)
2. Alert team in Slack #oncall
3. Restore from latest backup (if needed)

**Investigation:**
1. Compare DB message count vs localStorage
2. Identify when loss occurred
3. Check backfill logs (if running)

**Recovery:**
1. Restore from backup
2. Identify root cause
3. Fix code
4. Rollback to previous stage
5. Run backfill again

### Rollback Procedure

**If decision to rollback (Step 1-2):**
```bash
# 1. Disable feature flag immediately
export ENABLE_DB_SYNC=false

# 2. Restart service
docker restart devforge

# 3. Monitor for stability
curl http://localhost:7860/api/v2/health/detailed

# 4. Post-mortem within 24 hours
# 5. Fix root cause
# 6. Re-test before re-enabling
```

**Expected outcome:**
- All traffic routed to localStorage
- DB remains intact (no data lost)
- Users unaffected (fallback works)

---

## Metrics Export & Analysis

### Daily Snapshot

```bash
# At end of each day
python scripts/export_metrics.py --output metrics_$(date +%Y-%m-%d).json

# Upload to cloud storage for backup
aws s3 cp metrics_$(date +%Y-%m-%d).json s3://devforge-metrics/

# Generate daily report
python scripts/generate_daily_report.py metrics_$(date +%Y-%m-%d).json
```

### Weekly Review

Every Friday end-of-day:

1. **Export weekly metrics**
   ```bash
   python scripts/export_metrics.py --start=monday --output weekly_report.json
   ```

2. **Generate trend analysis**
   ```bash
   python scripts/analyze_trends.py weekly_report.json
   ```

3. **Go/No-Go decision**
   - Can we advance to next stage?
   - Any issues to address?
   - Any optimizations needed?

4. **Team sync**
   - 30 min meeting
   - Review metrics
   - Discuss blockers
   - Plan next week

---

## Communication Plan

### Internal (Engineering Team)

**Daily:**
- Slack #devforge-rollout channel updates (10 AM + 4 PM)
- Format: "✅ All metrics green" or "⚠️ Latency spike detected"

**Weekly:**
- Team sync Friday 4 PM (30 min)
- Metrics review + go/no-go decision

### External (Users)

**Week 2-5:**
- No communication (invisible rollout)

**Week 6:**
- Show in-app banner (30-day deprecation notice)
- Email to all users (newsletter)
- Update FAQ on website

**After Week 6:**
- Continue showing deprecation warning
- Remove localStorage support in 30 days

---

## Rollout Success Criteria

### At 10% (Week 2)
- ✅ No data loss
- ✅ Error rate < 0.1%
- ✅ Latency p95 < 150ms
- ✅ 0 rollback needs

### At 25% (Week 3)
- ✅ Data consistency > 99.8%
- ✅ All canary metrics stable
- ✅ No new error patterns
- ✅ Database scaling adequate

### At 50% (Week 4)
- ✅ Connection pool < 80%
- ✅ No timeout errors
- ✅ Real-world edge cases handled
- ✅ Ready for 75%

### At 75% (Week 5)
- ✅ All metrics healthy under load
- ✅ No performance degradation
- ✅ Deprecation plan ready
- ✅ Ready for 100%

### At 100% (Week 6)
- ✅ All users on DB
- ✅ localStorage deprecated
- ✅ Baseline established
- ✅ Ready for post-launch phase

---

## Troubleshooting

### "Latency suddenly increased"

```bash
# 1. Check database metrics
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"

# 2. Check connection pool
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Run ANALYZE (update statistics)
psql $DATABASE_URL -c "ANALYZE;"

# 4. Check for missing indexes
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
```

### "Data consistency mismatch detected"

```bash
# 1. Count messages in DB
psql $DATABASE_URL -c "SELECT COUNT(*) FROM messages;"

# 2. Compare with localStorage (requires client-side code)
# 3. Check backfill logs (if running)
# 4. Identify first message with discrepancy
# 5. Investigate specific conversation
```

### "Database running out of disk space"

```bash
# 1. Check disk usage
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('devforge'));"

# 2. Check table sizes
psql $DATABASE_URL -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size DESC;"

# 3. Options:
#    a. Add more disk (fastest)
#    b. Archive old conversations (if implemented)
#    c. Implement retention policy
```

---

## Post-Rollout (Week 6+)

### Database Maintenance

```bash
# Weekly
ANALYZE;  # Update statistics
VACUUM;   # Clean up deleted rows

# Monthly
REINDEX;  # Rebuild indexes
VACUUM FULL;  # Aggressively clean
```

### localStorage Deprecation Timeline

```
Week 6:   In-app warning shown
Week 9:   Disable localStorage writes
Week 12:  Remove localStorage entirely
```

### Long-term Monitoring

- Move from "intensive" to "basic" monitoring
- Keep alerts on error rate and latency
- Monthly review of database size/growth
- Quarterly performance optimization

---

## Support & Escalation

**Tier 1 (5 AM - 5 PM):**
- Engineering lead on-call
- Slack #devforge-oncall
- ~30 min response time

**Tier 2 (5 PM - 5 AM):**
- On-call engineer (rotating)
- Slack #devforge-oncall
- PagerDuty escalation after 30 min

**Contacts:**
- Tech lead: [contact]
- DB admin: [contact]
- Devops: [contact]
- Product: [contact]

---

## Checklist for Go Live

- [ ] All Phase 3 tests passing
- [ ] Backups configured and tested
- [ ] Monitoring dashboards ready
- [ ] Team briefed
- [ ] Rollback procedure documented
- [ ] On-call rotation set
- [ ] Communication templates ready
- [ ] Feature flag environment variables set
- [ ] Health endpoints working
- [ ] Metrics collection working

**Ready to start Week 2 (10% canary)? ✅**

