# DevForge Sensing System - Quick Start

## What Is It?

A real-time health monitoring system that watches all 6 layers of DevForge:
1. **Backend** - FastAPI server on port 8000
2. **Workflow** - GitHub/HF authentication  
3. **Frontend** - UI components on port 3000
4. **User Journey** - End-to-end feature flow
5. **Deployment** - HF Space sync pipeline
6. **Project** - Code structure & dependencies

**Problem it solves:** Know immediately when something breaks, without waiting for error reports.

---

## Installation

Already installed! Just run:

```bash
python sensors/sense.py
```

---

## Common Commands

### 1. Quick Health Check (Most Common)
```bash
python sensors/sense.py
```
**Output:**
```
DevForge Health Status: ✅ HEALTHY
==================================
Healthy:  6/6
Warnings: 0/6
Critical: 0/6
Last scan: 2026-06-17T11:30:44
```

### 2. See What's Broken
```bash
python sensors/sense.py dashboard --fixes
```
Shows problems + how to fix them.

### 3. Deep Dive on Specific Issue
```bash
python sensors/sense.py dashboard --details Backend
```
Shows all details for Backend Sensor.

### 4. Track Health Over Time
```bash
python sensors/sense.py dashboard --trends
```
Shows last 10 scans to identify patterns.

### 5. Full Diagnostic (For CI/CD)
```bash
python sensors/sense.py monitor
```
Runs all sensors, saves detailed JSON report.

---

## How to Read Results

### Green (✅ Healthy)
```
✅ Backend Sensor: Backend API is running and healthy
```
**Action:** Everything works, no action needed.

### Yellow (⚠️ Warning)
```
⚠️ Workflow Sensor: Auth workflow has 2 issues
   • Cannot reach GitHub auth endpoint
   • Cannot reach HF auth endpoint
```
**Action:** May self-resolve (e.g., backend restarting). Monitor if persists.

### Red (❌ Critical)
```
❌ Backend Sensor: Backend API not running on port 8000
🔧 Auto-fix: Backend restart initiated
```
**Action:** Blocks functionality. System attempted fix. If still broken:
```bash
python main.py
```

---

## Before You Commit

```bash
# 1. Run sensing
python sensors/sense.py

# 2. Is it healthy? If yes → commit
if [ $? -eq 0 ]; then
  git commit -m "..."
  git push
fi

# 3. If not healthy, fix issues first
python sensors/sense.py dashboard --fixes
```

---

## Before You Deploy

```bash
# 1. Ensure everything runs locally
npm run dev &
python main.py &

# 2. Run sensing
python sensors/sense.py

# 3. Should see all ✅ healthy

# 4. If all healthy → safe to deploy
git push origin main
```

---

## Typical Issues & Fixes

### ❌ Backend Sensor: Backend API not running on port 8000
```bash
# Fix:
python main.py
```

### ❌ Frontend Components Sensor: Frontend not running on port 3000
```bash
# Fix:
npm run dev
```

### ⚠️ Project Components Sensor: node_modules not installed
```bash
# Fix:
npm install
```

### ⚠️ Workflow Sensor: Auth workflow has issues
```bash
# Usually means backend is down
python main.py

# Or both services are down
npm run dev &
python main.py &
```

### ❌ User Journey Sensor: End-to-end workflow blocked
```bash
# Check backend is running (most common cause)
python main.py

# If still broken, run full diagnostics:
python sensors/sense.py monitor

# Review sensors/latest_report.json for details
```

---

## What Each Sensor Checks

| Sensor | Checks | Healthy If |
|--------|--------|-----------|
| Backend | FastAPI running, API responsive | Port 8000 responds to requests |
| Workflow | GitHub auth, HF auth, token storage | Auth endpoints reachable |
| Frontend | UI components wired, no render errors | Port 3000 responds, all components present |
| User Journey | Full feature workflow works | All critical API endpoints reachable |
| Deployment | HF sync workflow, git history | sync-to-hf.yml present, git accessible |
| Project | Directories exist, files present, deps installed | All required files/dirs/modules found |

---

## Files Generated

```
sensors/
├── latest_report.json          # Current health snapshot
└── reports/                    # Historical reports
    ├── report_20260617_112744.json
    └── ...
```

Open `latest_report.json` to see raw sensor data:
```json
{
  "timestamp": "2026-06-17T11:30:44",
  "overall_status": "healthy",
  "summary": { "healthy": 6, "warning": 0, "critical": 0 },
  "readings": [...]
}
```

---

## Common Workflows

### Scenario 1: Morning Dev Session
```bash
# Start services
npm run dev &
python main.py &

# Check health
python sensors/sense.py

# If all ✅ → you're good to work!
```

### Scenario 2: Something Broke
```bash
# Run sensing to diagnose
python sensors/sense.py

# See what sensor failed
# Run suggested fix

# Recheck
python sensors/sense.py
```

### Scenario 3: Pre-Commit Checklist
```bash
# Before committing:
python sensors/sense.py

# Should see all ✅
# Then: git commit && git push
```

### Scenario 4: Pre-Deployment
```bash
# Pull latest
git pull origin main

# Start local env
npm run dev &
python main.py &

# Verify healthy
python sensors/sense.py

# Deploy if all ✅
```

---

## For CI/CD Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Run DevForge Sensing System
  run: python sensors/sense.py monitor

- name: Fail if critical issues
  run: |
    python sensors/dashboard.py --summary
    if grep -q '"critical"' sensors/latest_report.json; then
      echo "❌ Critical issues detected!"
      exit 1
    fi
```

---

## Advanced Usage

### See All Sensor Details
```bash
python sensors/sense.py dashboard --full
```

### Focus on Specific Sensor
```bash
python sensors/sense.py dashboard --details Frontend
```

### See Which Fixes Were Attempted
```bash
grep "auto_fix_attempted" sensors/latest_report.json
```

### Raw JSON Report
```bash
cat sensors/latest_report.json | python -m json.tool
```

---

## Troubleshooting

### "No sensor reports found"
```bash
# Run monitor first to generate report
python sensors/sense.py monitor
```

### "Backend takes too long to import"
```bash
# main.py has slow imports
# Check for heavy dependencies being loaded at startup

# Or Python environment issue:
python -c "import main"  # See error details
```

### "Some sensors timeout"
```bash
# Increase timeout in monitor.py line 45:
# timeout=2  # Increase to 5 or 10 for slow systems
```

---

## Key Insights

**The Sensing System answers:**
- ✅ Is the backend running?
- ✅ Is the frontend running?
- ✅ Can I log in?
- ✅ Can I use the app end-to-end?
- ✅ Is my project structure intact?
- ✅ Is deployment pipeline ready?

**In 10 seconds.**

---

## Learning More

- **Full architecture:** See `SENSING_ARCHITECTURE.md`
- **Sensor details:** See `sensors/README.md`
- **Report format:** Check `sensors/latest_report.json`
- **Add custom sensors:** See `SENSING_ARCHITECTURE.md` → "Adding New Sensors"

---

## One-Command Health Check

```bash
python sensors/sense.py && echo "✅ Ready to go!" || echo "❌ Fix issues first"
```

---

## Summary

| Task | Command |
|------|---------|
| Quick check | `python sensors/sense.py` |
| See fixes | `python sensors/sense.py dashboard --fixes` |
| Deep dive | `python sensors/sense.py dashboard --details Backend` |
| Full report | `python sensors/sense.py monitor` |
| Trends | `python sensors/sense.py dashboard --trends` |

**That's it!** The sensing system is designed to be simple and fast.
