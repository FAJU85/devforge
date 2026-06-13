# Phase 8.6: AutoGen Multi-Agent Enhancement for DevForge

## Overview

Phase 8.6 implements a sophisticated multi-agent system using autonomous agents to orchestrate Phase 8 optimization tasks. The system enables complex workflows where multiple specialized agents communicate, analyze data, and reach decisions collaboratively.

## Architecture

### Agent System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Orchestrator                     │
│  (Manages workflow lifecycle and agent communication)        │
└─────────────────────────────────────────────────────────────┘
        │
        ├─────────────────┬──────────────────┬──────────────────┐
        │                 │                  │                  │
    ┌───▼──────┐   ┌─────▼──────┐  ┌──────▼───┐  ┌──────▼────┐
    │ Fine-Tuning│   │LoadTest   │  │Performance│  │Code      │
    │Orchestrator│   │Analyzer   │  │Advisor    │  │Reviewer  │
    └───┬──────┘   └─────┬──────┘  └──────┬───┘  └──────┬────┘
        │                 │                │              │
        └─────────────────┴────────────────┴──────────────┘
                    Agent Conversation Bus
                    (Message Exchange)
```

### Key Components

#### 1. Agent Definitions (`api/agents/agent_definitions.py`)

**BaseAgent Class**
- Base class for all agents
- Manages conversation history
- Tracks agent state
- Provides interface for thinking and acting

**Core Enums**
- `AgentRole`: ORCHESTRATOR, ANALYZER, ADVISOR, REVIEWER
- `MessageType`: QUERY, RESPONSE, ANALYSIS, RECOMMENDATION, DECISION, ERROR
- `AgentStatus`: IDLE, THINKING, ACTING, WAITING, COMPLETE, ERROR

**Key Classes**
- `ToolDefinition`: Schema for agent tools
- `AgentMessage`: Messages in agent conversation
- `AgentState`: Agent execution state
- `ConversationManager`: Manages agent conversations
- `WorkflowOrchestrator`: Coordinates workflows

#### 2. Specialized Agents (`api/agents/phase8_agents.py`)

**FineTuningOrchestrator**
- Role: ORCHESTRATOR
- Responsible for model fine-tuning workflows
- Tools:
  - `list_available_models()`: Get available models
  - `prepare_training_dataset(task_type)`: Prepare dataset
  - `start_fine_tuning(model, dataset, params)`: Start job
  - `validate_model(model_id)`: Run validation
  - `deploy_model(model_id)`: Deploy to production

**LoadTestAnalyzer**
- Role: ANALYZER
- Analyzes load testing results
- Tools:
  - `get_load_test_results(test_id)`: Retrieve metrics
  - `analyze_latency(metrics)`: Analyze response times
  - `identify_bottlenecks(metrics)`: Find performance issues
  - `compare_runs(run1_id, run2_id)`: Compare test runs
  - `generate_report(analysis)`: Generate detailed report

**PerformanceAdvisor**
- Role: ADVISOR
- Recommends optimizations
- Tools:
  - `analyze_cache_strategy(queries)`: Cache recommendations
  - `suggest_indexes(slow_queries)`: Index suggestions
  - `review_query_patterns(queries)`: Query optimization
  - `recommend_scaling(metrics, load)`: Scaling strategy

**CodeReviewerAgent**
- Role: REVIEWER
- Reviews code for quality and security
- Tools:
  - `review_code(code_snippet)`: Quality assessment
  - `check_security(code)`: Security analysis
  - `suggest_refactoring(code)`: Improvement suggestions

#### 3. Agent Tools (`api/agents/agent_tools.py`)

Grouped by functionality:
- **FineTuningTools**: Model selection, training, validation, deployment
- **LoadTestingTools**: Metrics analysis, bottleneck identification, reporting
- **OptimizationTools**: Caching, indexing, query patterns, scaling
- **CodeReviewTools**: Code quality, security, refactoring

#### 4. Orchestration Service (`api/services/agent_orchestration_service.py`)

**AgentOrchestrationService**
- Creates and manages workflows
- Executes fine-tuning workflow
- Executes optimization workflow
- Maintains workflow state
- Provides status and results retrieval

**Workflow Types**
1. **Fine-Tuning Workflow**
   - Creates FineTuningOrchestrator and CodeReviewerAgent
   - Steps: List models → Prepare dataset → Start job → Review code → Validate → Deploy

2. **Optimization Workflow**
   - Creates LoadTestAnalyzer, PerformanceAdvisor, CodeReviewerAgent
   - Steps: Get results → Analyze latency → Find bottlenecks → Generate recommendations → Code review

## Workflows

### Fine-Tuning Workflow

```
Step 1: FineTuningOrchestrator lists available models
         ↓
Step 2: Prepares training dataset based on task_type
         ↓
Step 3: Starts fine-tuning job with parameters
         ↓
Step 4: CodeReviewerAgent reviews training code
         ↓
Step 5: Validates fine-tuned model against benchmarks
         ↓
Step 6: Deploys model to production with gradual rollout
         ↓
        Returns job_id, endpoint, validation results
```

**Example Request:**
```json
{
  "task_type": "bug_detection",
  "model": "gpt-3.5-turbo",
  "parameters": {
    "learning_rate": 2e-5,
    "batch_size": 32,
    "num_epochs": 3
  },
  "target_metric": "accuracy"
}
```

**Example Response:**
```json
{
  "workflow_id": "wf_abc123def456",
  "workflow_type": "fine_tuning",
  "status": "queued",
  "created_at": "2024-06-13T10:30:00",
  "estimated_duration_seconds": 3600
}
```

### Optimization Workflow

```
Step 1: LoadTestAnalyzer retrieves load test results
         ↓
Step 2: Analyzes latency patterns (p50, p95, p99)
         ↓
Step 3: Identifies bottlenecks and performance issues
         ↓
Step 4: Generates analysis report
         ↓
Step 5: PerformanceAdvisor recommends caching strategy
         ↓
Step 6: Suggests database indexes
         ↓
Step 7: Recommends scaling approach
         ↓
Step 8: CodeReviewerAgent reviews optimization code
         ↓
        Returns recommendations, priority actions
```

**Example Request:**
```json
{
  "load_test_id": "lt_latest",
  "metrics_target": {
    "p95_latency_ms": 300,
    "throughput_rps": 1000
  },
  "constraints": {
    "max_cost_increase": 0.2,
    "max_deployment_time_hours": 2
  }
}
```

**Example Response:**
```json
{
  "workflow_id": "wf_xyz789abc012",
  "workflow_type": "optimization",
  "status": "queued",
  "created_at": "2024-06-13T10:30:00",
  "estimated_duration_seconds": 300
}
```

## API Endpoints

### Fine-Tuning Workflow

```
POST /api/agents/orchestrate/fine-tune
- Start fine-tuning workflow
- Request: FineTuningRequest
- Response: WorkflowResponse
```

### Optimization Workflow

```
POST /api/agents/orchestrate/optimize
- Start optimization workflow
- Request: OptimizationRequest
- Response: WorkflowResponse
```

### Workflow Status

```
GET /api/agents/orchestrate/{workflow_id}
- Get workflow status and progress
- Response: WorkflowStatusResponse
- Status: "queued", "running", "completed", "failed"
```

### Workflow Results

```
GET /api/agents/orchestrate/{workflow_id}/results
- Get final results and full conversation history
- Response: WorkflowResultsResponse
- Returns: initial_request, final_result, agent_states, messages
```

### Active Workflows

```
GET /api/agents/status
- List all active workflows
- Query param: status (optional: "running", "completed")
- Response: ActiveWorkflowsResponse
```

### Cleanup

```
DELETE /api/agents/cleanup
- Clean up old workflows
- Query param: hours (default: 24)
```

### Health Check

```
GET /api/agents/health
- Check agent system health
- Response: health status, active workflows, available agents
```

## Frontend Components

### AgentOrchestrator Component

Main control panel for triggering workflows.

**Props:**
```typescript
interface Props {
  onWorkflowCreated?: (workflowId: string, type: string) => void;
}
```

**Features:**
- Fine-tuning form with model/parameter selection
- Optimization form with load test selection
- Display of available models and costs
- Error handling and loading states

**Usage:**
```typescript
<AgentOrchestrator onWorkflowCreated={(id, type) => {
  console.log(`Workflow ${id} created (type: ${type})`);
}} />
```

### AgentWorkflow Component

Visualizes workflow progress and agent communication.

**Props:**
```typescript
interface Props {
  workflowId?: string;
}
```

**Features:**
- Real-time workflow status
- Agent state visualization
- Agent conversation display
- Results summary
- Error messages

**Usage:**
```typescript
<AgentWorkflow workflowId="wf_abc123" />
```

### useAgentWorkflow Hook

Hook for managing agent workflows in React components.

**Features:**
- Start fine-tuning workflows
- Start optimization workflows
- Poll workflow status
- Retrieve results
- Manage workflow state

**Usage:**
```typescript
const {
  startFineTuning,
  startOptimization,
  activeWorkflow,
  workflows,
  isLoading,
  error
} = useAgentWorkflow({
  autoPolling: true,
  pollingInterval: 2000
});

// Start fine-tuning
const workflowId = await startFineTuning({
  task_type: 'bug_detection',
  model: 'gpt-3.5-turbo'
});
```

### Agent Store (Zustand)

Centralized state management for agent workflows.

**State:**
- `workflows`: Map of all workflows
- `activeWorkflowId`: Currently selected workflow
- `isLoading`: Loading state
- `error`: Error messages

**Actions:**
- `createWorkflow()`: Create new workflow
- `updateWorkflow()`: Update workflow state
- `addMessage()`: Add message to conversation
- `setActiveWorkflow()`: Select workflow
- `pollWorkflow()`: Poll for updates

## Integration with Phase 8

The agent system integrates seamlessly with existing Phase 8 components:

### Phase 8.1 Bug Detection
- Fine-tuning workflow uses bug detection dataset
- Code reviewer provides feedback on training code
- Results feed into bug detection service

### Phase 8.4 Load Testing
- Optimization workflow uses load test results
- LoadTestAnalyzer examines Phase 8.4 metrics
- Recommendations improve Phase 8.1-8.3 services

### Phase 8.2 Caching
- PerformanceAdvisor recommends caching strategies
- Recommendations applied to cache_service.py
- Cache hit rates inform advisor decisions

### Phase 8.3 Database Optimization
- PerformanceAdvisor suggests indexes and query rewrites
- Results applied to db_optimization_service.py
- Query analysis improves database performance

### Phase 8.5 Monitoring
- Prometheus metrics inform advisor decisions
- Real-time metrics used in agent analysis
- Agent actions monitored for performance impact

## Configuration

### Environment Variables

```bash
# Agent Configuration
AGENT_MAX_WORKFLOWS=100
AGENT_CLEANUP_INTERVAL_HOURS=24
AGENT_POLLING_TIMEOUT_SECONDS=300

# Fine-Tuning
FINE_TUNING_API_KEY=your_api_key
FINE_TUNING_TIMEOUT_MINUTES=60

# Load Testing
LOAD_TEST_API_URL=http://load-test-service:8080

# Code Review
CODE_REVIEW_STRICTNESS=high  # low, medium, high
```

### Workflow Configuration

Fine-tuning defaults:
- Learning rate: 2e-5
- Batch size: 32
- Epochs: 3
- Validation split: 0.1

Optimization defaults:
- Latency target: 300ms (p95)
- Throughput target: 1000 rps
- Cache hit target: 40%

## Performance Characteristics

### Workflow Execution Times

**Fine-Tuning Workflow:**
- Model listing: <100ms
- Dataset preparation: ~5 minutes
- Fine-tuning: ~2-4 hours (actual training)
- Validation: ~30 minutes
- Deployment: ~5-10 minutes
- **Total: ~2.5-4.5 hours**

**Optimization Workflow:**
- Load test analysis: <1 second
- Latency analysis: <500ms
- Bottleneck identification: <1 second
- Recommendation generation: <2 seconds
- Code review: ~5 seconds
- **Total: ~10-20 seconds**

### Resource Usage

- Memory per agent: ~100MB
- Memory per workflow: ~50MB
- Max concurrent workflows: 100
- Max conversation history: 10,000 messages

## Monitoring and Logging

### Agent Logging

All agent actions are logged:
```
[workflow_id] Step 1: Listing available models
[workflow_id] Step 2: Preparing training dataset
[workflow_id] Step 3: Starting fine-tuning job
```

### Metrics

Exposed via `/api/agents/health`:
- Active workflow count
- Completed workflow count
- Average workflow duration
- Error rates by agent type

### Debugging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View agent conversation:
```bash
curl http://localhost:8000/api/agents/orchestrate/{workflow_id}/results
```

## Security Considerations

### Tool Authorization

- `deploy_model`: Requires explicit approval (requires_approval=True)
- All other tools execute without approval
- Tool execution timeouts: 30 seconds default

### Agent Isolation

- Agents run in isolated Python processes
- No direct filesystem access
- All data passed through structured APIs
- Tool outputs validated before use

### Audit Trail

- All agent messages logged with timestamps
- Complete conversation history stored
- User actions traceable
- Workflow state changes recorded

## Testing

### Unit Tests

```bash
# Test agent definitions
pytest tests/agents/test_agent_definitions.py

# Test agent tools
pytest tests/agents/test_agent_tools.py

# Test orchestration service
pytest tests/services/test_agent_orchestration.py
```

### Integration Tests

```bash
# Test fine-tuning workflow
pytest tests/agents/test_fine_tuning_workflow.py

# Test optimization workflow
pytest tests/agents/test_optimization_workflow.py
```

### Load Testing

```bash
# Test concurrent workflows
k6 run tests/load/agent_workflows.js --vus 10 --duration 5m
```

## Deployment

### Prerequisites

- Python 3.11+
- FastAPI running
- PostgreSQL for workflow history
- Redis for caching (optional)

### Installation

1. Install agent dependencies:
```bash
pip install -r requirements-agents.txt
```

2. Register routes in main API:
```python
from api.routes.agents import router as agent_routes
app.include_router(agent_routes)
```

3. Initialize orchestration service:
```python
from api.services.agent_orchestration_service import agent_orchestration_service
```

4. Run cleanup task:
```python
# Schedule cleanup every 24 hours
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    agent_orchestration_service.clear_old_workflows,
    'interval',
    hours=24
)
scheduler.start()
```

### Production Configuration

1. **Persistence**: Use PostgreSQL for workflow history
2. **Scaling**: Deploy agents as microservices
3. **Monitoring**: Enable Prometheus metrics
4. **Rate Limiting**: Implement per-user workflow limits
5. **Authentication**: Require API tokens for workflow creation

## Troubleshooting

### Workflow stuck in "running" status

Check agent logs for errors:
```bash
tail -f logs/agents.log
```

Check workflow details:
```bash
curl http://localhost:8000/api/agents/orchestrate/{workflow_id}/results
```

### Agent not responding

Increase timeout in agent config:
```python
ToolDefinition(..., timeout_seconds=60)
```

### Memory issues with long workflows

Implement message pruning:
```python
# Keep only last 1000 messages
conversation.messages = conversation.messages[-1000:]
```

## Future Enhancements

1. **Multi-turn Dialogue**: Extended agent conversations with clarification
2. **Human-in-the-Loop**: Agent recommendations require human approval
3. **Auto-tuning**: Agents adjust parameters based on results
4. **Collaborative Planning**: Agents create detailed plans before execution
5. **Learning**: Agents improve based on historical results
6. **Tool Chain**: Agents create sequences of tool calls (AutoGen-style)
7. **Structured Output**: Agent responses in JSON schema format
8. **Tool Validation**: Pre-flight checks before tool execution

## File Structure

```
api/
├── agents/
│   ├── __init__.py
│   ├── agent_definitions.py      # Base classes and structures
│   ├── agent_tools.py             # Tool implementations
│   └── phase8_agents.py            # Specific agents
├── routes/
│   └── agents.py                   # API endpoints
├── services/
│   └── agent_orchestration_service.py  # Orchestration logic
src/
├── components/agents/
│   ├── AgentOrchestrator.tsx       # Control panel
│   └── AgentWorkflow.tsx            # Workflow visualization
├── hooks/
│   └── useAgentWorkflow.ts          # React hook
└── stores/
    └── agentStore.ts               # Zustand store
tests/
├── agents/
│   ├── test_agent_definitions.py
│   ├── test_agent_tools.py
│   ├── test_phase8_agents.py
│   ├── test_fine_tuning_workflow.py
│   └── test_optimization_workflow.py
└── services/
    └── test_agent_orchestration.py
```

## Summary

Phase 8.6 implements a production-ready multi-agent system that:

✓ Coordinates complex optimization workflows
✓ Enables agent communication and collaboration
✓ Provides full audit trail and transparency
✓ Integrates seamlessly with Phase 8.1-8.5
✓ Offers rich frontend visualization
✓ Scales to multiple concurrent workflows
✓ Implements proper error handling and recovery
✓ Follows security best practices
✓ Supports monitoring and observability

The system is ready for immediate deployment and use in optimizing DevForge's performance.
