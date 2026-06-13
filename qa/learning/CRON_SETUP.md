# QA Learning Cron Job Setup Guide

Automatically keep your learned patterns database fresh by running `npm run qa:learn` on a schedule.

## Quick Start

### Option 1: Node.js Cron (Recommended for Development)

Run the built-in cron job in your terminal or background:

```bash
# Every 30 minutes (default)
npm run qa:cron

# Every hour
npm run qa:cron:hourly

# Every day
npm run qa:cron:daily

# Custom interval (in milliseconds)
npm run qa:cron -- --interval 7200000   # 2 hours
```

Keep this running in a terminal or background process while developing.

### Option 2: System Cron (Linux/macOS)

For production deployments, use your system's cron scheduler:

```bash
# Edit your crontab
crontab -e

# Add one of these lines:
# Every 30 minutes
*/30 * * * * cd /path/to/devforge && npm run qa:learn

# Every hour
0 * * * * cd /path/to/devforge && npm run qa:learn

# Every day at 2 AM
0 2 * * * cd /path/to/devforge && npm run qa:learn

# Every 6 hours
0 */6 * * * cd /path/to/devforge && npm run qa:learn
```

Replace `/path/to/devforge` with your actual project path.

### Option 3: PM2 Daemon (Production with Monitoring)

For persistent background execution:

```bash
# Install PM2 globally
npm install -g pm2

# Start the cron job as a daemon
pm2 start npm --name "qa-cron" -- run qa:cron:hourly

# View logs
pm2 logs qa-cron

# Restart on system reboot
pm2 startup
pm2 save

# Stop
pm2 stop qa-cron

# Remove
pm2 delete qa-cron
```

### Option 4: Docker Container (Production)

Add to your Dockerfile:

```dockerfile
# Run cron job in background while keeping container alive
CMD npm run qa:cron:hourly & npm start
```

Or use a separate cron container in your docker-compose:

```yaml
services:
  devforge:
    # ... your normal config

  qa-cron:
    image: node:18-alpine
    working_dir: /app
    volumes:
      - .:/app
    command: npm run qa:cron:hourly
    depends_on:
      - devforge
```

## How It Works

The cron job:

1. **Checks for new failures** in the `failures/` directory
2. **Runs learning** if failures found (`npm run qa:learn`)
3. **Updates patterns** in `learned_patterns.json`
4. **Logs results** with timestamps

Example output:

```
[2026-06-13T01:28:26.504Z] ✓ Cron job started
[2026-06-13T01:28:26.504Z]   Interval: 30m
[2026-06-13T01:28:26.504Z]   Next run: in 30m
[2026-06-13T01:28:26.504Z]   Last learning: 20 minutes ago
🔄 Starting pattern learning...
   Found 28 failure(s) to process
✓ Learning complete: 62 patterns, 28 failures marked
```

## Integration with CI/CD

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
- name: Learn patterns
  run: npm run qa:learn
  if: always()  # Run even if tests fail

- name: Upload learned patterns
  uses: actions/upload-artifact@v4
  with:
    name: learned-patterns
    path: qa/learning/learned_patterns.json
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
learn_patterns:
  stage: post_test
  script:
    - npm run qa:learn
  artifacts:
    paths:
      - qa/learning/learned_patterns.json
  when: always  # Run even if tests fail
```

## Monitoring & Alerts

### Slack Notification Example

Create a wrapper script `scripts/cron-with-slack.js`:

```javascript
const { execSync } = require('child_process');

try {
  execSync('npm run qa:learn', { stdio: 'inherit' });
  // Send success to Slack
} catch (err) {
  // Send error to Slack
  console.error(`Learning failed: ${err.message}`);
}
```

### Cloud Scheduler (Google Cloud)

```bash
gcloud scheduler jobs create app-engine qa-learn \
  --schedule="0 */6 * * *" \
  --http-method=POST \
  --uri=https://your-app.com/api/qa/learn
```

## Troubleshooting

### Cron job not running?

Check logs:
```bash
# Node.js cron
npm run qa:cron  # Run in foreground to see output

# System cron
grep CRON /var/log/syslog  # Linux
log stream --predicate 'process == "cron"'  # macOS

# PM2
pm2 logs qa-cron
pm2 monit
```

### No patterns being learned?

1. Check failure count: `npm run qa:failures:stats`
2. Verify patterns file exists: `ls -la qa/learning/learned_patterns.json`
3. Check file permissions: `chmod 644 qa/learning/learned_patterns.json`
4. Run learning manually: `npm run qa:learn`

### High CPU/Memory usage?

- Reduce interval: `qa:cron:daily` instead of `qa:cron`
- Limit failure retention: `npm run qa:failures:clear` periodically
- Monitor with: `top`, `htop`, or `pm2 monit`

## Best Practices

1. **Run daily** for most projects (balance between freshness and overhead)
2. **Run hourly** during active development
3. **Run on-demand** in CI/CD after major test runs
4. **Clean up old failures** monthly: `npm run qa:failures:clear`
5. **Monitor dashboard** at `npm run qa:dashboard` to verify learning

## Disable Cron Job

To stop the cron job:

```bash
# If running in terminal: Ctrl+C
# If PM2: pm2 stop qa-cron
# If system cron: crontab -e (remove the line)
```

## Next Steps

- View live dashboard: `npm run qa:dashboard`
- Check pattern statistics: `npm run qa:failures:stats`
- Export patterns for analysis: `cat qa/learning/learned_patterns.json | jq`
