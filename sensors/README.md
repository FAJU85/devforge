# DevForge Sensing System

Comprehensive health monitoring across all layers of DevForge. Automatically detects malfunctions, triggers alerts with full diagnostics, and suggests fixes.

## Six Sensors

### 1. **Backend Sensor** 🔌
- Monitors FastAPI health on port 8000
- Checks API responsiveness
- Auto-attempts restart if down
- **Critical for:** Code generation pipeline

### 2. **Workflow Sensor** 🔐
- Monitors GitHub OAuth flow
- Monitors Hugging Face auth
- Checks token persistence (localStorage)
- **Critical for:** User authentication

### 3. **Frontend Components Sensor** 🎨
- Verifies all UI components present
- Checks GitHub token input is wired
- Monitors Generate tab rendering
- **Critical for:** User interface

### 4. **User Journey Sensor** 🛤️
- End-to-end workflow validation
- Tests: auth → form fill → submit → result
- Checks all critical API endpoints
- **Critical for:** Feature completeness

### 5. **Deployment Sensor** 🚀
- Monitors HF Space sync pipeline
- Checks git workflow triggers
- Verifies deployment status
- **Critical for:** Production readiness

### 6. **Project Components Sensor** 📦
- Verifies directory structure
- Checks required files exist
- Validates dependencies installed
- Checks Python import health
- **Critical for:** Project integrity

## Quick Start

### Run full diagnostic:
```bash
python sensors/monitor.py
```

### Output
```
🔍 DevForge Sensing System - Full Diagnostic Run
===============================================

🔎 Running Backend Sensor...
✅ Backend Sensor: Backend API is running and healthy
   • endpoint: http://localhost:8000
   • status_code: 200

🔎 Running Frontend Components Sensor...
✅ Frontend Components Sensor: All core frontend components present and wired
   • components_verified: ['CodeGeneratorPage', 'GenerateTab', 'GitHub Token Input']

... (all 6 sensors)

📊 SENSING SYSTEM REPORT
===============================================
✅ Healthy: 6 | ⚠️  Warning: 0 | ❌ Critical: 0

Overall Status: HEALTHY

📁 Full report saved to: sensors/latest_report.json
```

## Report Output

Each run generates `sensors/latest_report.json` with:
- Timestamp of scan
- Overall health status
- Individual sensor readings with details
- Issues detected
- Auto-fix attempts

## Integration Points

### In CI/CD
Add to GitHub Actions before deployment:
```yaml
- name: Run DevForge Sensing System
  run: python sensors/monitor.py
```

### In Development
Run before committing to catch issues early:
```bash
# Before git commit
python sensors/monitor.py
```

### On Demand
```bash
# Check if something broke
python sensors/monitor.py
```

## How to Interpret Results

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ Healthy | All checks passed | Continue development |
| ⚠️ Warning | Minor issues detected | Review details, may self-resolve |
| ❌ Critical | Major issues blocking functionality | Fix immediately, check suggested solutions |

## Auto-Fixes Attempted

The system will automatically attempt to:
- Restart backend if down
- Suggest npm install if dependencies missing
- Identify Python import errors

## Adding New Sensors

1. Create new method in `DevForgeSensingSystem`
2. Return `SensorReading` with status, message, details
3. Add to `sensors` list in `run_all_sensors()`

```python
def sense_my_feature(self) -> SensorReading:
    try:
        # Your check here
        return SensorReading(
            sensor_name="My Feature Sensor",
            status="healthy",
            timestamp=datetime.now().isoformat(),
            message="All checks passed",
            details={...}
        )
    except Exception as e:
        return SensorReading(
            sensor_name="My Feature Sensor",
            status="critical",
            timestamp=datetime.now().isoformat(),
            message=f"Feature broken: {str(e)}",
            details={"error": str(e)}
        )
```

## Files

- `monitor.py` - Main sensing orchestrator (6 sensors)
- `latest_report.json` - Latest scan results
- `README.md` - This file

## Requirements

- Python 3.8+
- `requests` library (for HTTP health checks)
- Git (for deployment checks)
- npm (for dependency validation)

## Examples

### Catch broken backend before running tests:
```bash
$ python sensors/monitor.py
❌ Backend Sensor: Backend API not running on port 8000
   🔧 Auto-fix: Backend restart initiated
```

### Verify all components before committing:
```bash
$ python sensors/monitor.py
✅ All 6 sensors healthy - safe to commit
```

### Diagnose deployment issues:
```bash
$ python sensors/monitor.py
⚠️ Deployment Sensor: Sync workflow missing
   • Check: .github/workflows/sync-to-hf.yml exists
```
