# DevForge Sensing System Architecture

## Overview

The DevForge Sensing System provides comprehensive health monitoring across all six layers of the application stack. It automatically detects malfunctions, triggers alerts with detailed diagnostics, and suggests actionable fixes.

**Goal:** Keep DevForge in a healthy, deployable state at all times by providing real-time visibility into system health.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   SENSING ORCHESTRATOR                      │
│              (DevForgeSensingSystem in monitor.py)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐    ┌──────▼──────┐   ┌─────▼─────┐
    │ Monitor │    │  Dashboard  │   │    CLI    │
    │  (Real- │    │  (Visualize)│   │  (sense)  │
    │  time   │    │             │   │ (wrapper) │
    │ checks) │    └─────────────┘   └───────────┘
    └────┬────┘
         │
    ┌────┴────────────────────────────────────┐
    │                                          │
┌───▼────┐ ┌──────────┐ ┌────────────┐   ┌──┴──────┐
│Backend │ │Workflow  │ │Frontend    │   │User     │
│Sensor  │ │Sensor    │ │Components  │   │Journey  │
└────────┘ └──────────┘ │Sensor      │   │Sensor   │
                        └────────────┘   └─────────┘
                             │
                        ┌────▼────┐  ┌──────────────┐
                        │Deployment│  │Project       │
                        │Sensor    │  │Components    │
                        └──────────┘  │Sensor        │
                                      └──────────────┘
```

### Component Layers

#### 1. **Sensing Orchestrator** (`monitor.py`)
- Central coordinator of all 6 sensors
- Runs all checks sequentially
- Collects `SensorReading` objects
- Generates comprehensive report
- Saves to `latest_report.json`

#### 2. **Six Independent Sensors**

Each sensor:
- Runs independently with isolated error handling
- Returns standardized `SensorReading` dataclass
- Can attempt auto-fixes (e.g., restart backend)
- Provides detailed diagnostics

**Sensors:**
1. **Backend Sensor** - API health on port 8000
2. **Workflow Sensor** - Auth flows (GitHub/HF)
3. **Frontend Components Sensor** - UI component integrity
4. **User Journey Sensor** - End-to-end feature flow
5. **Deployment Sensor** - HF Space sync pipeline
6. **Project Components Sensor** - Project structure & dependencies

#### 3. **Dashboard** (`dashboard.py`)
- Reads latest report
- Displays health summary
- Shows detailed findings
- Suggests fixes
- Tracks trends over time

#### 4. **CLI Wrapper** (`sense.py`)
- Unified entry point
- Orchestrates monitor + dashboard
- Simple commands for different use cases

---

## SensorReading Data Model

```python
@dataclass
class SensorReading:
    sensor_name: str           # e.g., "Backend Sensor"
    status: str                # "healthy", "warning", "critical"
    timestamp: str             # ISO format
    message: str               # Human-readable summary
    details: Dict[str, Any]    # Structured diagnostic data
    auto_fix_attempted: bool   # Did we try to fix it?
    fix_status: str            # Result of fix attempt
```

### Status Levels

| Status | Meaning | Example |
|--------|---------|---------|
| `healthy` | Everything works | "Backend API running and responsive" |
| `warning` | Minor issues, may self-resolve | "Auth unreachable (backend down)" |
| `critical` | Blocks functionality | "Backend API not running" |

---

## Sensor Details

### 1. Backend Sensor 🔌

**What it checks:**
- FastAPI server running on port 8000
- `/health` endpoint responsive
- API can start and accept requests

**Auto-fixes:**
- Attempts to start backend if down
- Waits 2 seconds for startup

**Critical for:**
- Code generation pipeline
- Model search functionality
- PR creation workflow

**Sample output:**
```
❌ Backend Sensor: Backend API not running on port 8000
🔧 Auto-fix: Backend restart initiated
```

---

### 2. Workflow Sensor 🔐

**What it checks:**
- GitHub OAuth endpoint reachable
- Hugging Face auth endpoint reachable
- Token persistence (localStorage) working

**Critical for:**
- User authentication
- OAuth flow completion
- Session management

**Sample output:**
```
⚠️ Workflow Sensor: Auth workflow has 2 issues
   • Cannot reach GitHub auth endpoint
   • Cannot reach HF auth endpoint
```

---

### 3. Frontend Components Sensor 🎨

**What it checks:**
- Frontend server on port 3000 responsive
- Key component files exist:
  - `components/generate/CodeGeneratorPage.tsx`
  - `components/layout/GenerateTab.tsx`
- GitHub token input wired correctly
- No rendering errors

**Critical for:**
- UI availability
- User interface integrity
- Form functionality

**Sample output:**
```
✅ Frontend Components Sensor: All core frontend components present and wired
   • components_verified: ['CodeGeneratorPage', 'GenerateTab', 'GitHub Token Input']
```

---

### 4. User Journey Sensor 🛤️

**What it checks:**
- Complete feature workflow:
  1. User authenticates
  2. User fills form (repo, file, instruction)
  3. User selects models
  4. User submits (generates)
  5. Results returned

**Validates these endpoints:**
- `GET /api/models/discover` - Model search
- `POST /api/generate/code-parallel-stream` - Code generation
- `POST /api/apply-pr` - PR creation

**Critical for:**
- Feature completeness
- End-to-end workflow
- User experience

**Sample output:**
```
❌ User Journey Sensor: End-to-end workflow blocked: 3 endpoints have issues
   • blocked_endpoints:
     - Cannot reach /api/models/discover (backend down)
     - Cannot reach /api/generate/code-parallel-stream (backend down)
     - Cannot reach /api/apply-pr (backend down)
```

---

### 5. Deployment Sensor 🚀

**What it checks:**
- HF Space sync workflow exists (`.github/workflows/sync-to-hf.yml`)
- Git history accessible
- Recent commits present
- Deployment pipeline intact

**Critical for:**
- Production readiness
- Deployment automation
- HF Space updates

**Sample output:**
```
✅ Deployment Sensor: HF Space deployment pipeline operational
   • sync_workflow: sync-to-hf.yml present
   • git_history: Accessible
   • deployment_url: https://huggingface.co/spaces/vooom/devforge
```

---

### 6. Project Components Sensor 📦

**What it checks:**
- Required directories exist:
  - `components/` (frontend)
  - `api/` (backend routes)
  - `.github/workflows/` (CI/CD)
- Required files:
  - `package.json` (npm config)
  - `main.py` (FastAPI entry)
  - `.gitignore` (version control)
  - `CLAUDE.md` (project docs)
- `node_modules/` installed
- Python environment importable

**Critical for:**
- Project integrity
- Development environment
- Dependency management

**Sample output:**
```
✅ Project Components Sensor: Project structure and dependencies verified
   • directories_verified: ['components', 'api', '.github/workflows']
   • files_verified: ['package.json', 'main.py', '.gitignore', 'CLAUDE.md']
   • node_modules: Installed
   • python_environment: Healthy
```

---

## Report Structure

Every diagnostic run generates `sensors/latest_report.json`:

```json
{
  "timestamp": "2026-06-17T11:27:44.395831",
  "overall_status": "healthy|warning|critical",
  "summary": {
    "healthy": 6,
    "warning": 0,
    "critical": 0,
    "total": 6
  },
  "readings": [
    {
      "sensor_name": "Backend Sensor",
      "status": "healthy",
      "message": "Backend API is running and healthy",
      "details": {
        "endpoint": "http://localhost:8000",
        "status_code": 200
      },
      "auto_fix_attempted": false,
      "fix_status": ""
    },
    ...
  ]
}
```

---

## Usage Workflows

### Workflow 1: Quick Health Check
```bash
python sensors/sense.py
```
- Runs all sensors
- Shows summary dashboard
- Exits with appropriate code (0 = healthy, 1 = issues)

### Workflow 2: Full Diagnostics
```bash
python sensors/sense.py monitor
```
- Same as above but shows full sensor output

### Workflow 3: View Dashboard Only
```bash
python sensors/sense.py dashboard --fixes
```
- Shows health summary + suggested fixes
- Useful after services started

### Workflow 4: Details on Specific Sensor
```bash
python sensors/sense.py dashboard --details Backend
```
- Deep dive into specific sensor
- Useful for debugging

### Workflow 5: Health Trends
```bash
python sensors/sense.py dashboard --trends
```
- Shows health over last 10 scans
- Useful for identifying patterns

### Workflow 6: Pre-Commit Check
```bash
# Before committing
python sensors/sense.py

# Only commit if healthy
if [ $? -eq 0 ]; then
  git commit ...
fi
```

---

## Integration Points

### In Development
```bash
# Before committing
python sensors/sense.py

# If issues found, fix them first
```

### In CI/CD (GitHub Actions)
```yaml
- name: Run DevForge Sensing System
  run: python sensors/sense.py monitor
  
- name: Fail if critical issues
  run: |
    if grep -q '"critical"' sensors/latest_report.json; then
      exit 1
    fi
```

### Pre-Deployment
```bash
# Before pushing to HF Space
python sensors/sense.py

# Ensure all systems healthy before deploy
```

### Post-Deployment
```bash
# After deploying to HF Space
python sensors/sense.py

# Verify deployed version is healthy
```

---

## Adding New Sensors

1. Add method to `DevForgeSensingSystem`:
```python
def sense_my_feature(self) -> SensorReading:
    """Monitor my feature."""
    try:
        # Your checks here
        if everything_ok:
            return SensorReading(
                sensor_name="My Feature Sensor",
                status="healthy",
                timestamp=datetime.now().isoformat(),
                message="Everything is working",
                details={"key": "value"}
            )
        else:
            return SensorReading(
                sensor_name="My Feature Sensor",
                status="critical",
                timestamp=datetime.now().isoformat(),
                message="Something broke",
                details={"issue": "description"}
            )
    except Exception as e:
        return SensorReading(
            sensor_name="My Feature Sensor",
            status="critical",
            timestamp=datetime.now().isoformat(),
            message=f"Sensor failed: {e}",
            details={"error": str(e)}
        )
```

2. Register in `run_all_sensors()`:
```python
sensors = [
    ("My Feature Sensor", self.sense_my_feature),
    ...
]
```

---

## Auto-Fix Logic

Some sensors attempt automatic remediation:

### Backend Sensor
- If backend down: attempts `subprocess.Popen(["python", "main.py"])`
- Waits 2 seconds for startup
- Retests connectivity

### Future Auto-Fixes
- Restart frontend (npm run dev)
- Install dependencies (npm install)
- Pull latest code (git pull)

---

## Dashboard Features

### Summary View
```
DevForge Health Status: ✅ HEALTHY
==================================
Healthy:  6/6
Warnings: 0/6
Critical: 0/6
Last scan: 2026-06-17T11:30:44
```

### Detailed View
Shows all sensor readings with:
- Status and message
- Auto-fix attempts
- Detailed diagnostic data

### Fix Suggestions
Context-aware fixes:
- "Backend not running" → Run `python main.py`
- "Frontend not running" → Run `npm run dev`
- "Dependencies missing" → Run `npm install`

### Health Trends
Shows last 10 scans:
```
✅ 11:27 | Health: 6/6
⚠️ 10:15 | Health: 4/6
❌ 09:00 | Health: 1/6
```

---

## Error Handling

Each sensor is wrapped in try/except:
- Sensor crashes don't stop orchestrator
- Returns "critical" status with error details
- Orchestrator continues with remaining sensors

Example:
```
❌ My Feature Sensor crashed: Division by zero
   Sensor crashed: Division by zero
```

---

## Report History

Reports are saved with timestamps:
```
sensors/
├── monitor.py
├── dashboard.py
├── sense.py
├── README.md
├── latest_report.json          # Most recent
└── reports/
    ├── report_20260617_112744.json
    ├── report_20260617_101530.json
    └── ...
```

Dashboard can show trends from report history.

---

## Exit Codes

```python
sys.exit(0)  # All healthy
sys.exit(1)  # Issues detected (warning or critical)
```

Use in CI/CD:
```bash
python sensors/sense.py monitor
echo "Exit code: $?"
```

---

## Monitoring Best Practices

1. **Run before committing:** Catch issues early
2. **Run before deploying:** Ensure safe deployments
3. **Check trends:** Identify intermittent issues
4. **Review details:** Understand root causes
5. **Fix reported issues:** Keep system healthy

---

## Files

- `monitor.py` - Sensing orchestrator (6 sensors)
- `dashboard.py` - Visualization & trend analysis
- `sense.py` - Unified CLI wrapper
- `__init__.py` - Package definition
- `README.md` - User guide
- `latest_report.json` - Current health snapshot
- `reports/` - Historical reports

---

## Example: Full Workflow

```bash
# 1. Start development environment
npm run dev &
python main.py &

# 2. Run sensing system
python sensors/sense.py

# Output:
# ✅ HEALTHY - All 6 sensors passing

# 3. Make changes
# ... edit code ...

# 4. Pre-commit check
python sensors/sense.py
# ✅ HEALTHY

# 5. Commit
git commit -m "Feature: ..."

# 6. Push and deploy
git push

# 7. Post-deployment check
python sensors/sense.py
# ✅ HEALTHY

# Done! System is healthy end-to-end.
```

---

## Future Enhancements

- [ ] Real-time monitoring daemon
- [ ] Webhook alerts (Slack/Discord)
- [ ] Metrics dashboard (Grafana)
- [ ] Historical metrics (InfluxDB)
- [ ] Performance profiling
- [ ] Load testing sensors
- [ ] Security audit sensor
- [ ] Code quality sensor
- [ ] API rate limit monitoring
- [ ] Database health monitoring
