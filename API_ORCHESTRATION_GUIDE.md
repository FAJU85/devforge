# API Orchestration Guide

## Overview

DevForge provides three REST APIs for agent orchestration:

1. **Agent Orchestration API** (Port 8001) - High-level task execution
2. **Browser Control API** (Port 8002) - Low-level browser automation
3. **Task Orchestrator** (Port 8003) - Coordinates task execution with infrastructure

## Starting the APIs

### Automated Startup

```bash
bash scripts/start-agents-api.sh
```

This script will:
- Activate the Python virtual environment
- Load configuration from `.env.qa-extended`
- Start all three API servers
- Verify they're responding
- Display service URLs and examples

### Manual Startup

```bash
# Activate virtual environment
source venv/bin/activate

# Start each API in separate terminals
python api/agents_server.py          # Port 8001
python api/browser_server.py         # Port 8002
python api/task_orchestrator.py      # Port 8003
```

### Configuration

Set environment variables in `.env.qa-extended`:

```bash
AGENT_API_PORT=8001
BROWSER_API_PORT=8002
TASK_API_PORT=8003

ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

AGENT_MAX_STEPS=50
AGENT_TIMEOUT=300
HEADLESS=true
```

## Agent Orchestration API (Port 8001)

High-level interface for executing agent tasks asynchronously.

### Base URL
```
http://localhost:8001
```

### Endpoints

#### Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "service": "Agent Orchestration API",
  "version": "2.0.0"
}
```

#### List Available Agents
```http
GET /api/agents

Response:
{
  "agents": [
    {
      "name": "BrowserAgent",
      "type": "browser",
      "description": "Autonomous web browser control",
      "endpoint": "/api/agents/browser/task"
    },
    ...
  ]
}
```

#### Get Agent Information
```http
GET /api/agents/{agent_type}/info

Parameters:
- agent_type: "browser", "test_generator", "bug_detector", "web_task"

Response:
{
  "name": "BrowserAgent",
  "description": "Autonomous web browser control",
  "capabilities": [...],
  "request_format": "BrowserTaskRequest"
}
```

### Browser Agent Tasks

#### Execute Browser Task
```http
POST /api/agents/browser/task

Request:
{
  "description": "Navigate to example.com and take a screenshot",
  "url": "https://example.com",
  "max_steps": 50
}

Response:
{
  "task_id": "uuid",
  "status": "pending",
  "agent_type": "browser",
  "created_at": "2026-06-13T12:00:00"
}
```

#### Get Browser Screenshot
```http
GET /api/agents/browser/screenshot/{task_id}

Response:
{
  "task_id": "uuid",
  "screenshot": "base64_encoded_image"
}
```

### Test Generation Tasks

#### Generate a Test
```http
POST /api/agents/test-generator/generate

Request:
{
  "description": "Test login with valid credentials",
  "url": "http://localhost:3000/login",
  "framework": "pytest",
  "context": {
    "username_field": "#username",
    "password_field": "#password"
  }
}

Response:
{
  "task_id": "uuid",
  "status": "pending",
  "agent_type": "test_generator"
}
```

#### Generate Test Suite
```http
POST /api/agents/test-generator/suite

Request:
{
  "feature_description": "User authentication",
  "test_scenarios": [
    "User can register",
    "User can login",
    "User can logout"
  ],
  "framework": "pytest"
}

Response:
{
  "task_id": "uuid",
  "status": "pending"
}
```

### Bug Detection Tasks

#### Scan for Bugs
```http
POST /api/agents/bug-detector/scan

Request:
{
  "url": "https://example.com",
  "test_cases": [
    "Load homepage",
    "Check for broken links",
    "Test form submission"
  ],
  "max_interactions": 10
}

Response:
{
  "task_id": "uuid",
  "status": "pending"
}
```

#### Get Bug Report
```http
GET /api/agents/bug-detector/{task_id}/report?format=json

Response:
{
  "task_id": "uuid",
  "format": "json",
  "report": {
    "bugs_found": 3,
    "bugs": [
      {
        "id": "BUG-001",
        "severity": "high",
        "description": "..."
      }
    ]
  }
}
```

### Web Task Execution

#### Execute Web Task
```http
POST /api/agents/web-task/execute

Request:
{
  "description": "Search for machine learning and click first result",
  "start_url": "https://google.com",
  "max_steps": 50
}

Response:
{
  "task_id": "uuid",
  "status": "pending"
}
```

### Task Management

#### Get Task Status
```http
GET /api/tasks/{task_id}

Response:
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {...}
}
```

#### List Tasks
```http
GET /api/tasks?agent_type=browser&status=completed

Response:
{
  "tasks": [
    {
      "task_id": "uuid",
      "agent_type": "browser",
      "status": "completed",
      "created_at": "2026-06-13T12:00:00"
    }
  ],
  "count": 1
}
```

#### Delete Task
```http
DELETE /api/tasks/{task_id}

Response:
{
  "message": "Task deleted",
  "task_id": "uuid"
}
```

### Statistics

#### Get Statistics
```http
GET /api/stats

Response:
{
  "total_tasks": 10,
  "completed": 8,
  "failed": 1,
  "running": 0,
  "pending": 1
}
```

#### Get Agent Statistics
```http
GET /api/stats/agents

Response:
{
  "browser": 5,
  "test_generator": 2,
  "bug_detector": 2,
  "web_task": 1
}
```

## Browser Control API (Port 8002)

Low-level interface for direct browser control (no task creation).

### Base URL
```
http://localhost:8002
```

### Session Management

#### Start Session
```http
POST /api/browser/session/start

Response:
{
  "status": "success",
  "message": "Browser session started"
}
```

#### End Session
```http
POST /api/browser/session/end

Response:
{
  "status": "success",
  "message": "Browser session ended"
}
```

#### Get Session Status
```http
GET /api/browser/session

Response:
{
  "status": "active",
  "browser_ready": true
}
```

### Navigation

#### Navigate to URL
```http
POST /api/browser/navigate

Request:
{
  "url": "https://example.com",
  "timeout": 30000
}

Response:
{
  "status": "success",
  "url": "https://example.com"
}
```

#### Get Current URL
```http
GET /api/browser/url

Response:
{
  "status": "success",
  "url": "https://example.com"
}
```

#### Get Page Title
```http
GET /api/browser/title

Response:
{
  "status": "success",
  "title": "Example Domain"
}
```

### Screenshots & Content

#### Take Screenshot
```http
GET /api/browser/screenshot

Response:
{
  "status": "success",
  "screenshot": "base64_encoded_image"
}
```

#### Get Page Content
```http
GET /api/browser/content

Response:
{
  "status": "success",
  "content": {
    "title": "Example",
    "url": "https://example.com",
    "elements": [...]
  }
}
```

### Element Interaction

#### Click Element
```http
POST /api/browser/click

Request:
{
  "selector": "button.submit",
  "timeout": 5000
}

Response:
{
  "status": "success",
  "selector": "button.submit"
}
```

#### Fill Form Field
```http
POST /api/browser/fill

Request:
{
  "selector": "input#username",
  "text": "testuser",
  "timeout": 5000
}

Response:
{
  "status": "success",
  "selector": "input#username"
}
```

#### Fill Multiple Fields
```http
POST /api/browser/fill-form

Request:
{
  "input#username": "testuser",
  "input#password": "password123",
  "select#country": "US"
}

Response:
{
  "status": "success",
  "results": [
    {"selector": "input#username", "success": true},
    {"selector": "input#password", "success": true},
    {"selector": "select#country", "success": true}
  ]
}
```

### Content Extraction

#### Extract Content
```http
POST /api/browser/extract

Request:
{
  "selector": ".product"
}

Response:
{
  "status": "success",
  "elements": [...],
  "count": 5
}
```

### JavaScript Execution

#### Evaluate JavaScript
```http
POST /api/browser/evaluate

Request:
{
  "code": "return document.title;"
}

Response:
{
  "status": "success",
  "result": "Example Domain"
}
```

## Task Orchestrator (Port 8003)

Coordinates task execution with Phase 1 infrastructure.

### Base URL
```
http://localhost:8003
```

### Create Task
```http
POST /api/orchestrator/task

Request:
{
  "task_type": "browser_automation",
  "description": "Navigate and capture",
  "priority": "high",
  "params": {
    "url": "https://example.com"
  },
  "metadata": {
    "user_id": "user123",
    "project": "qa"
  }
}

Response:
{
  "task_id": "uuid",
  "status": "pending"
}
```

### Get Task
```http
GET /api/orchestrator/task/{task_id}

Response:
{
  "task_id": "uuid",
  "task_type": "browser_automation",
  "status": "completed",
  "description": "Navigate and capture",
  "created_at": "2026-06-13T12:00:00",
  "started_at": "2026-06-13T12:00:01",
  "completed_at": "2026-06-13T12:00:30",
  "result": {...},
  "error": null
}
```

### List Tasks
```http
GET /api/orchestrator/tasks?task_type=browser_automation&status=completed

Response:
{
  "tasks": [...],
  "count": 5
}
```

### Batch Execution
```http
POST /api/orchestrator/batch

Request:
{
  "tasks": [
    {
      "task_type": "browser_automation",
      "description": "Task 1",
      "params": {...}
    },
    {
      "task_type": "test_generation",
      "description": "Task 2",
      "params": {...}
    }
  ],
  "parallel": false
}

Response:
{
  "batch_id": "uuid",
  "task_ids": ["uuid1", "uuid2"],
  "count": 2
}
```

### Statistics
```http
GET /api/orchestrator/stats

Response:
{
  "total_tasks": 10,
  "status": {
    "completed": 8,
    "failed": 1,
    "running": 0,
    "pending": 1
  },
  "by_type": {
    "browser_automation": 5,
    "test_generation": 3,
    "bug_detection": 2
  },
  "by_priority": {
    "high": 3,
    "medium": 5,
    "low": 2
  }
}
```

## Python Client

Use the `OrchestratorClient` for easy Python integration:

```python
from ml.orchestrator_client import OrchestratorClient

# Create client
client = OrchestratorClient()

# Execute a test generation task synchronously
result = client.generate_test_sync(
    description="Test login with valid credentials",
    url="http://localhost:3000/login"
)

print(f"Test generated: {result['result']['test_name']}")
```

### Common Operations

```python
from ml.orchestrator_client import get_client

client = get_client()

# Browser automation
task_id = client.browser_navigate("https://example.com")
task = client.wait_for_task(task_id)

# Test generation
result = client.generate_test_sync(
    "Test user registration",
    "http://localhost:3000/register"
)

# Bug detection
result = client.scan_bugs_sync("https://example.com")

# Web task execution
result = client.execute_task_sync(
    "Search for AI and click first result",
    "https://google.com"
)

# List all tasks
tasks = client.list_tasks(task_type="browser_automation")

# Get statistics
stats = client.get_stats()
```

## cURL Examples

### Browser Task
```bash
curl -X POST http://localhost:8001/api/agents/browser/task \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Navigate to Google",
    "url": "https://google.com"
  }'
```

### Test Generation
```bash
curl -X POST http://localhost:8001/api/agents/test-generator/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Test login functionality",
    "framework": "pytest"
  }'
```

### Bug Scanning
```bash
curl -X POST http://localhost:8001/api/agents/bug-detector/scan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

### Check Task Status
```bash
curl http://localhost:8001/api/tasks/{task_id}
```

## Error Handling

All APIs return consistent error responses:

```json
{
  "detail": "Error message"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad request
- `404` - Not found
- `500` - Server error
- `503` - Service unavailable

## Performance Tips

1. **Use Asynchronous Execution**: Don't wait for task completion unless necessary
2. **Batch Tasks**: Use batch endpoints for multiple operations
3. **Set Appropriate Timeouts**: Match timeouts to task complexity
4. **Monitor Statistics**: Track API usage and task distribution
5. **Use Task Filtering**: Filter results by type, status, or priority

## Troubleshooting

### APIs Not Responding
```bash
# Check if services are running
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Restart services
bash scripts/start-agents-api.sh
```

### Task Failing
```bash
# Get task details
curl http://localhost:8001/api/tasks/{task_id}

# Check error message in response
```

### Browser Issues
```bash
# Check browser session
curl http://localhost:8002/api/browser/session

# Start new session if needed
curl -X POST http://localhost:8002/api/browser/session/start
```

## Integration with Phase 1

The APIs can be integrated with Phase 1 infrastructure:

```python
from ml.clients import DevForgeClient
from ml.orchestrator_client import OrchestratorClient

# Use Phase 1 for storage
forge_client = DevForgeClient()

# Use orchestrator for tasks
orch_client = OrchestratorClient()

# Execute task
task_id = orch_client.generate_test_sync(...)

# Store result
forge_client.postgres_client.insert_test_result({
    "task_id": task_id,
    "result": result
})
```

---

**Version**: 2.0.0  
**Last Updated**: June 2026
