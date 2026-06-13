# Installing QA Suite Extended - Complete Guide

This guide installs all AI agents, browser automation, and web task understanding tools into the DevForge QA Suite.

## 📦 What Gets Installed

### AI & LLM Integration
- ✅ **Vercel AI SDK** - LLM framework
- ✅ **Anthropic Claude SDK** - Claude API access
- ✅ **OpenAI SDK** - GPT integration

### Browser Automation
- ✅ **Playwright** - Modern browser automation
- ✅ **Selenium** - WebDriver automation
- ✅ **Puppeteer** - Headless browser control
- ✅ **Stagehand** - Natural language browser commands

### Web Task Understanding
- ✅ **Browser Use** - AI browser agent framework
- ✅ **Gorilla** - LLM API orchestration
- ✅ **WebArena** - Web task environment
- ✅ **Mind2Web** - Web task dataset

### Datasets
- ✅ **RepliQA** - 10K+ test specifications
- ✅ **Mind2Web** - 2100+ web tasks
- ✅ **WebArena** - 812 benchmark tasks

## 🚀 Quick Install (One Command)

### Option 1: Automated Setup (Recommended)

```bash
cd /home/user/devforge
bash scripts/install-qa-extended.sh
```

**Time**: 10-15 minutes
**What happens**:
1. Installs npm packages
2. Installs Python dependencies
3. Clones tool repositories
4. Downloads datasets
5. Creates configuration
6. Tests installations

### Option 2: Manual Step-by-Step

#### Step 1: npm Dependencies

```bash
cd /home/user/devforge

# Install AI SDK
npm install ai@latest

# Install browser automation
npm install @browserbasehq/stagehand@latest
npm install puppeteer@latest
npm install playwright@latest

# Install utilities
npm install axios dotenv cors express-cors
```

#### Step 2: Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core + extended
pip install -r requirements-phase1.txt
pip install -r requirements-phase1-extended.txt

# Install specific packages
pip install anthropic playwright selenium pillow opencv-python datasets huggingface-hub
```

#### Step 3: Clone Tools

```bash
# Create tools directory
mkdir -p tools
cd tools

# Clone Browser Use
git clone https://github.com/browser-use/browser-use.git

# Clone Gorilla
git clone https://github.com/shishirpatil/gorilla.git

# Clone WebArena
git clone https://github.com/web-arena-x/webarena.git

cd ..
```

#### Step 4: Download Datasets

```bash
# Create data directory
mkdir -p data/datasets

# Download RepliQA
python3 << 'EOF'
from datasets import load_dataset
dataset = load_dataset("ServiceNow/repliqa", split="train", streaming=True)
# Data will be cached by HuggingFace
EOF

# Download WebArena
cd tools/webarena
python -m webarena.instance_manager --mode install
cd ../..
```

#### Step 5: Configure

```bash
# Copy and edit configuration
cp storage/config/.env.example .env.qa-extended

# Add API keys
echo "ANTHROPIC_API_KEY=your_key_here" >> .env.qa-extended
echo "OPENAI_API_KEY=your_key_here" >> .env.qa-extended
```

## 📝 Configuration

### .env.qa-extended Settings

```bash
# AI Configuration
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Browser Configuration
BROWSER_TYPE=chromium          # chromium, firefox, webkit
HEADLESS=true
BROWSER_TIMEOUT=30000

# Agent Configuration
AGENT_MAX_STEPS=50
AGENT_TIMEOUT=300
CONCURRENT_AGENTS=5

# Paths
REPLIQA_DATA_DIR=./data/datasets/repliqa
MIND2WEB_DATA_DIR=./data/datasets/mind2web
WEBARENA_SITES_DIR=./tools/webarena/env_base/sites

# API Ports
AGENT_API_PORT=8001
BROWSER_API_PORT=8002
TASK_API_PORT=8003
```

## 🎯 Verify Installation

### Test Node Packages

```bash
npm list ai @browserbasehq/stagehand puppeteer
```

### Test Python Installation

```bash
source venv/bin/activate

python3 << 'EOF'
import anthropic
import playwright
import selenium
print("✓ All Python packages installed")
EOF
```

### Test Playwright Browsers

```bash
npx playwright install
npx playwright test --list
```

### Test Specific Modules

```bash
# Browser Agent
python ml/agents/browser_agent.py

# Test Agent
python ml/agents/test_generator_agent.py

# Bug Detection
python ml/agents/bug_detector_agent.py
```

## 💻 Using the Tools

### 1. Browser Agent (Autonomous Web Control)

```python
from ml.agents import BrowserAgent
import asyncio

async def main():
    agent = BrowserAgent()
    await agent.start()
    
    # Simple task
    await agent.navigate("https://example.com")
    result = await agent.execute_task("Click the signup button")
    
    await agent.stop()

asyncio.run(main())
```

### 2. Test Generation Agent

```python
from ml.agents import TestGenerationAgent

agent = TestGenerationAgent()
test_code = agent.generate_test(
    description="Test login with valid credentials",
    target_url="http://localhost:3000"
)
print(test_code)
```

### 3. Bug Detection Agent

```python
from ml.agents import BugDetectionAgent

agent = BugDetectionAgent()
bugs = agent.detect_bugs(
    url="http://localhost:3000",
    test_cases=["login", "signup", "logout"]
)
for bug in bugs:
    print(f"Bug found: {bug['description']}")
```

### 4. Gorilla API Orchestration

```python
from ml.gorilla import APIOrchestrator

orchestrator = APIOrchestrator()

# Discover and call APIs
result = orchestrator.call_function(
    api="github",
    function="create_issue",
    args={"repo": "devforge", "title": "Test Bug"}
)
```

### 5. WebArena Environment

```python
from tools.webarena import WebArenaEnv

env = WebArenaEnv()
env.start()

# Run agents on web tasks
for task in env.tasks[:5]:
    result = agent.execute_task(task['description'])
    env.log_result(task['id'], result)

env.stop()
```

## 📚 API Endpoints (After Installation)

```bash
# Browser automation
POST   /api/browser/navigate
POST   /api/browser/click
POST   /api/browser/fill
POST   /api/browser/screenshot
GET    /api/browser/elements

# Agents
POST   /api/agents/execute-task
POST   /api/agents/generate-test
POST   /api/agents/detect-bugs

# Tasks
POST   /api/tasks/execute
GET    /api/tasks/{id}/status
GET    /api/tasks/{id}/result

# Stats
GET    /api/stats/agents
GET    /api/stats/browser
GET    /api/stats/tasks
```

## 🔧 Troubleshooting

### npm Packages Not Installing

```bash
# Clear cache
npm cache clean --force

# Reinstall
npm install --no-save

# Or specific package
npm install ai@latest --save
```

### Python Package Conflicts

```bash
# Use specific versions
pip install anthropic==0.7.0
pip install playwright==1.40.0

# Check installed versions
pip list | grep -E "anthropic|playwright|selenium"
```

### Playwright Browser Issues

```bash
# Install all browsers
npx playwright install

# Verify installation
npx playwright test --list

# Check specific browser
npx playwright install chromium
```

### API Key Issues

```bash
# Test API key validity
python3 << 'EOF'
import os
from anthropic import Anthropic

api_key = os.getenv('ANTHROPIC_API_KEY')
if api_key:
    client = Anthropic(api_key=api_key)
    msg = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=10, messages=[{"role": "user", "content": "Hi"}])
    print("✓ API key valid")
else:
    print("✗ API key not set")
EOF
```

### WebArena Setup Issues

```bash
# Check system requirements (Linux recommended)
uname -s

# Manual setup
cd tools/webarena
python -m webarena.instance_manager --mode install --force

# Start services
python -m webarena.instance_manager --mode start
```

## 📊 Project Structure After Installation

```
devforge/
├── ml/
│   ├── agents/
│   │   ├── browser_agent.py
│   │   ├── test_generator_agent.py
│   │   ├── bug_detector_agent.py
│   │   ├── web_task_agent.py
│   │   └── __init__.py
│   └── gorilla_integration.py
│
├── api/
│   ├── agents_server.py         # Agent API endpoints
│   ├── browser_server.py        # Browser control API
│   └── task_server.py           # Task execution API
│
├── tools/
│   ├── browser-use/             # Browser Use framework
│   ├── gorilla/                 # API orchestration
│   └── webarena/                # Web environment
│
├── data/
│   └── datasets/
│       ├── repliqa/             # Test specs
│       ├── mind2web/            # Web tasks
│       └── webarena/            # Web benchmarks
│
├── scripts/
│   └── install-qa-extended.sh   # Installation script
│
└── examples/
    └── agents/
        ├── browser_example.py
        ├── test_generation_example.py
        └── web_task_example.py
```

## 🎓 Examples & Tutorials

See `examples/agents/` for:
- `browser_example.py` - Autonomous web navigation
- `test_generation_example.py` - Generate tests from natural language
- `web_task_example.py` - Execute web tasks
- `api_orchestration_example.py` - Call multiple APIs with Gorilla

## 📈 Performance Tips

1. **Reuse Browser Instance**
   ```python
   agent = BrowserAgent()
   await agent.start()
   # Reuse for multiple tasks
   for task in tasks:
       await agent.execute_task(task)
   await agent.stop()
   ```

2. **Batch API Calls**
   ```python
   # Instead of one call per task, batch them
   results = orchestrator.batch_calls([...])
   ```

3. **Cache Results**
   ```python
   # Cache task results in database
   db.insert_task_result(task_id, result)
   ```

4. **Use Concurrent Agents**
   ```python
   # Run multiple agents in parallel
   import asyncio
   tasks = [agent.execute_task(t) for t in tasks]
   results = await asyncio.gather(*tasks)
   ```

## 🔐 Security Notes

1. **Never commit API keys**
   - Use `.env` file
   - Add to `.gitignore`
   - Use environment variables

2. **Validate user input**
   - Sanitize URLs
   - Validate selectors
   - Check task descriptions

3. **Rate limit API calls**
   - Implement backoff
   - Cache responses
   - Monitor usage

4. **Secure browser automation**
   - Run in sandbox
   - Disable external plugins
   - Timeout long tasks

## 📞 Support

- **Browser Use**: https://github.com/browser-use/browser-use
- **Gorilla**: https://github.com/shishirpatil/gorilla
- **WebArena**: https://github.com/web-arena-x/webarena
- **Vercel AI SDK**: https://sdk.vercel.ai/
- **Anthropic**: https://www.anthropic.com/docs

## ✅ Installation Checklist

- [ ] npm packages installed
- [ ] Python dependencies installed
- [ ] Tool repositories cloned
- [ ] Datasets downloaded
- [ ] Configuration created (.env.qa-extended)
- [ ] API keys added
- [ ] Installations tested
- [ ] Examples reviewed
- [ ] Ready to use!

## 🎉 You're All Set!

Your QA Suite now has:
- ✅ AI-powered browser automation
- ✅ Autonomous web task execution
- ✅ Test generation from natural language
- ✅ Bug detection via web interaction
- ✅ API orchestration with Gorilla
- ✅ Web task datasets

**Next Steps**:
1. Run examples: `python examples/agents/browser_example.py`
2. Start API server: `python api/phase1_server.py`
3. Launch agent server: `node api/agents_server.js`
4. Explore documentation: `PHASE1_EXTENDED_README.md`
