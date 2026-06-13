# Phase 1 Extended: AI Agent & Browser Automation Integration

This adds advanced AI agent capabilities and browser automation to Phase 1.

## Tools Being Integrated

### 1. **Vercel AI SDK** (https://ai-sdk.dev/)
- Framework for building AI-powered applications
- LLM integration (Claude, OpenAI, etc.)
- Streaming support
- Tool use framework

### 2. **Browser Use** (https://github.com/browser-use/browser-use)
- Framework for AI agents to control browsers
- Selenium/Playwright integration
- Vision capabilities
- Chain-of-thought execution

### 3. **Stagehand** (@browserbasehq/stagehand)
- Browser automation library
- Reliable element detection
- Natural language commands
- Web automation at scale

### 4. **Gorilla** (https://github.com/shishirpatil/gorilla)
- LLM API chain, retrieval, orchestration
- API function calling
- Chain composition
- API discovery

### 5. **Mind2Web** (https://osu-nlp-group.github.io/Mind2Web/)
- Web task understanding dataset
- 2,100+ web-based tasks
- Natural language to web actions
- Training data for agents

### 6. **WebArena** (https://github.com/web-arena-x/webarena)
- Web-based environment for agent evaluation
- 5 realistic websites
- 812 web-based tasks
- Benchmark for autonomous agents

### 7. **RepliQA Dataset** (https://huggingface.co/datasets/ServiceNow/repliqa)
- Test specifications from ServiceNow
- 10,000+ test examples
- Natural language to test code
- Test case generation training

## Installation Instructions

### Step 1: Install Node.js Dependencies

```bash
# Navigate to project root
cd /home/user/devforge

# Install AI SDK and browser automation tools
npm install ai
npm install @browserbasehq/stagehand
npm install puppeteer           # Alternative browser automation
npm install playwright          # Already installed, but ensure latest
npm install axios              # HTTP client for API calls
```

### Step 2: Install Python Dependencies

```bash
# Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install extended requirements
pip install -r requirements-phase1-extended.txt
```

### Step 3: Clone/Download Datasets and Tools

```bash
# Create workspace directories
mkdir -p data/datasets
mkdir -p tools
cd tools

# Clone Gorilla
git clone https://github.com/shishirpatil/gorilla.git
cd gorilla
pip install -e .
cd ..

# Clone Browser Use
git clone https://github.com/browser-use/browser-use.git
cd browser-use
pip install -e .
cd ..

# Clone WebArena
git clone https://github.com/web-arena-x/webarena.git
cd webarena
pip install -e .
cd ..

cd ..

# Download datasets
python ml/download_datasets.py  # We'll create this script
```

### Step 4: Configuration

Create `.env.extended` with:

```bash
# AI SDK Configuration
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Browser Configuration
BROWSER_TYPE=chromium  # or firefox, webkit
HEADLESS=true
DEBUG=false

# Gorilla Configuration
GORILLA_API_URL=http://localhost:8001

# WebArena Configuration
WEBARENA_SITES_DIR=./data/webarena/sites
MIND2WEB_DATA_DIR=./data/mind2web

# Agent Configuration
AGENT_MAX_STEPS=50
AGENT_TIMEOUT=300
```

## Architecture

```
devforge/
├── api/
│   ├── phase1_server.py          # Core API
│   ├── agent_server.py           # NEW: AI Agent API
│   └── browser_api.py            # NEW: Browser Control API
│
├── ml/
│   ├── clients.py                # Core clients
│   ├── agents/                   # NEW: AI Agent implementations
│   │   ├── browser_agent.py     # Browser automation agent
│   │   ├── test_agent.py        # Test generation agent
│   │   ├── bug_agent.py         # Bug detection agent
│   │   └── web_agent.py         # Web task agent
│   ├── download_datasets.py      # NEW: Dataset downloader
│   └── task_executor.py          # NEW: Task execution engine
│
├── tools/
│   ├── gorilla/                  # API orchestration
│   ├── browser-use/              # Browser automation
│   └── webarena/                 # Web environment
│
├── data/
│   ├── datasets/
│   │   ├── repliqa/             # Test specifications
│   │   ├── mind2web/            # Web tasks
│   │   └── webarena/            # Web environment
│   └── models/
│
└── requirements-phase1-extended.txt
```

## Capabilities Added

### 1. **AI-Powered Test Generation**
```python
from ml.agents import TestGenerationAgent

agent = TestGenerationAgent()
test_code = await agent.generate_test(
    description="Test login flow with email validation",
    framework="playwright"
)
```

### 2. **Autonomous Browser Control**
```python
from ml.agents import BrowserAgent

agent = BrowserAgent()
result = await agent.execute_task(
    task="Find and click the 'Sign Up' button, then fill in the form"
)
```

### 3. **Web Task Understanding**
```python
from ml.agents import WebTaskAgent

agent = WebTaskAgent()
steps = await agent.understand_task(
    "Change password on GitHub settings"
)
# Returns list of executable steps
```

### 4. **Bug Detection via Web Interaction**
```python
from ml.agents import BugDetectionAgent

agent = BugDetectionAgent()
bugs = await agent.detect_bugs(
    url="http://localhost:3000",
    test_cases=[...]
)
```

### 5. **API Function Calling (Gorilla)**
```python
from ml.gorilla import APIOrchestrator

orchestrator = APIOrchestrator()
result = await orchestrator.call_function(
    api="github",
    function="create_issue",
    args={"repo": "devforge", "title": "Bug report"}
)
```

## API Endpoints (Extended)

### AI Agent Endpoints
- `POST /api/agents/generate-test` - Generate test cases
- `POST /api/agents/execute-task` - Execute web tasks
- `POST /api/agents/detect-bugs` - Detect bugs via automation
- `POST /api/agents/understand-task` - Parse natural language tasks

### Browser Control Endpoints
- `POST /api/browser/navigate` - Navigate to URL
- `POST /api/browser/click` - Click element
- `POST /api/browser/fill` - Fill form field
- `POST /api/browser/screenshot` - Take screenshot
- `GET /api/browser/elements` - Get page elements

### Task Execution Endpoints
- `POST /api/tasks/execute` - Execute custom tasks
- `GET /api/tasks/{id}/status` - Check task status
- `GET /api/tasks/{id}/result` - Get task result
- `POST /api/tasks/batch` - Execute batch tasks

## Environment Setup

### Prerequisites
- Node.js 18+
- Python 3.8+
- Chrome/Chromium installed
- API keys (Anthropic/OpenAI)

### Quick Setup
```bash
# Run full setup including extended tools
bash scripts/phase1-extended-setup.sh
```

## Usage Examples

### Example 1: Generate Test from Natural Language
```python
from ml.agents import TestGenerationAgent
from ml.clients import DevForgeClient

client = DevForgeClient()
client.connect_all()

agent = TestGenerationAgent()
test = await agent.generate_test(
    description="User login with email validation",
    target_url="http://localhost:3000"
)

# Store in database
test_id = client.postgres.insert_test_case(
    name=test['name'],
    code=test['code'],
    framework='playwright'
)
```

### Example 2: Autonomous Bug Detection
```python
from ml.agents import BrowserAgent

agent = BrowserAgent()

# Navigate and interact
await agent.navigate("http://localhost:3000")
await agent.click("button#login")
await agent.fill("input#email", "test@example.com")
await agent.fill("input#password", "wrong-password")
await agent.click("button#submit")

# Take screenshot of error
screenshot = await agent.screenshot()

# Analyze with bug detector
bugs = await agent.detect_bugs()
```

### Example 3: Web Task Execution
```python
from ml.agents import WebTaskAgent

agent = WebTaskAgent()

# Understand natural language task
task = "Create a new GitHub issue in devforge with title 'Bug: Login fails' and assign to @user"
steps = await agent.understand_task(task)

# Execute steps
results = await agent.execute_steps(steps)
```

### Example 4: Using Gorilla for API Calls
```python
from ml.gorilla import APIOrchestrator

orchestrator = APIOrchestrator()

# Discover APIs
apis = await orchestrator.discover_apis("create issue")

# Call API
result = await orchestrator.call_function(
    api="github",
    function="create_issue",
    args={
        "owner": "faju85",
        "repo": "devforge",
        "title": "Test Bug Report",
        "body": "This is a test bug"
    }
)
```

## Dataset Integration

### RepliQA Integration
```python
from ml.dataset_loader import RepliQALoader

loader = RepliQALoader()
loader.download()
specs = loader.process()

# Use for test generation training
for spec in specs:
    test = generate_test(spec['description'])
```

### Mind2Web Integration
```python
from ml.dataset_loader import Mind2WebLoader

loader = Mind2WebLoader()
tasks = loader.load()

# Train web task understanding
for task in tasks:
    steps = understand_task(task['query'])
    validate_steps(steps, task['expected_steps'])
```

### WebArena Integration
```python
from tools.webarena import WebArenaEnv

env = WebArenaEnv()
env.start()

# Test agents on web tasks
for task in env.tasks:
    agent = BrowserAgent()
    result = agent.execute_task(task['description'])
    score = evaluate_result(result, task['expected'])
    env.log_result(task['id'], score)

env.stop()
```

## Testing

Run extended tests:
```bash
# Test AI agents
npm run test:agents

# Test browser automation
npm run test:browser

# Test task execution
npm run test:tasks

# Test API integration
npm run test:api-extended
```

## Performance Monitoring

Monitor agent performance:
```bash
# View agent metrics
curl http://localhost:8000/api/stats/agents

# Check browser automation status
curl http://localhost:8000/api/browser/status

# View task execution stats
curl http://localhost:8000/api/stats/tasks
```

## Troubleshooting

### Browser Not Found
```bash
# Ensure Chromium is installed
npx playwright install chromium

# Or use system browser
export BROWSER_PATH=/usr/bin/chromium
```

### API Key Issues
```bash
# Verify API keys in .env
cat .env | grep API_KEY

# Test API connection
python -c "
from ml.agents import TestAgent
agent = TestAgent()
print(agent.api_status())
"
```

### Dataset Download Failures
```bash
# Download manually
python ml/download_datasets.py --verbose

# Check downloaded files
ls -lh data/datasets/
```

## Next Steps

1. **Install Tools**: Run extended setup script
2. **Test Agents**: Run agent tests
3. **Train Models**: Use datasets to train agents
4. **Deploy Agents**: Start agent server
5. **Monitor Performance**: Track metrics

## Documentation

- AI SDK: https://sdk.vercel.ai/
- Browser Use: https://github.com/browser-use/browser-use
- WebArena: https://github.com/web-arena-x/webarena
- Gorilla: https://github.com/shishirpatil/gorilla
- Mind2Web: https://osu-nlp-group.github.io/Mind2Web/
