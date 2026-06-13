# Phase 8.6: Agent System Quick Start

## Overview

Phase 8.6 implements a sophisticated multi-agent system for DevForge that coordinates optimization tasks through collaborative agents. Four specialized agents work together to:

1. **FineTuningOrchestrator** - Manage model fine-tuning workflows
2. **LoadTestAnalyzer** - Analyze performance bottlenecks
3. **PerformanceAdvisor** - Recommend optimizations
4. **CodeReviewerAgent** - Review code for quality/security

## Quick Start

### Installation

1. Ensure FastAPI dependencies are installed:
```bash
pip install fastapi uvicorn pydantic
```

2. Import the agent routes in your main API:
```python
from api.routes.agents import router as agent_routes
app.include_router(agent_routes)
```

3. Import the orchestration service:
```python
from api.services.agent_orchestration_service import agent_orchestration_service
```

### Starting Workflows

#### Fine-Tuning Workflow

```bash
curl -X POST http://localhost:8000/api/agents/orchestrate/fine-tune \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "bug_detection",
    "model": "gpt-3.5-turbo",
    "parameters": {
      "learning_rate": 0.00002,
      "batch_size": 32,
      "num_epochs": 3
    }
  }'
```

Response:
```json
{
  "workflow_id": "wf_abc123def456",
  "workflow_type": "fine_tuning",
  "status": "queued",
  "created_at": "2024-06-13T10:30:00",
  "estimated_duration_seconds": 3600
}
```

#### Optimization Workflow

```bash
curl -X POST http://localhost:8000/api/agents/orchestrate/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "load_test_id": "lt_latest",
    "metrics_target": {
      "p95_latency_ms": 300,
      "throughput_rps": 1000
    }
  }'
```

Response:
```json
{
  "workflow_id": "wf_xyz789abc012",
  "workflow_type": "optimization",
  "status": "queued",
  "created_at": "2024-06-13T10:30:00",
  "estimated_duration_seconds": 300
}
```

### Checking Workflow Status

```bash
curl http://localhost:8000/api/agents/orchestrate/wf_abc123def456
```

Response:
```json
{
  "workflow_id": "wf_abc123def456",
  "workflow_type": "fine_tuning",
  "status": "completed",
  "created_at": "2024-06-13T10:30:00",
  "completed_at": "2024-06-13T11:45:00",
  "duration_seconds": 4500,
  "agent_count": 2,
  "message_count": 8
}
```

### Getting Workflow Results

```bash
curl http://localhost:8000/api/agents/orchestrate/wf_abc123def456/results
```

Response includes:
- Initial request parameters
- Final recommendations/results
- Full agent conversation history
- Agent analysis states

### List Active Workflows

```bash
curl http://localhost:8000/api/agents/status
```

### Health Check

```bash
curl http://localhost:8000/api/agents/health
```

## Using the Frontend Components

### AgentOrchestrator Component

Main control panel for triggering workflows:

```typescript
import { AgentOrchestrator } from '@/components/agents/AgentOrchestrator';

export function MyDashboard() {
  return (
    <AgentOrchestrator
      onWorkflowCreated={(id, type) => {
        console.log(`Workflow ${id} created (${type})`);
      }}
    />
  );
}
```

### AgentWorkflow Component

Visualize workflow progress in real-time:

```typescript
import { AgentWorkflow } from '@/components/agents/AgentWorkflow';

export function WorkflowViewer({ workflowId }: { workflowId: string }) {
  return <AgentWorkflow workflowId={workflowId} />;
}
```

### useAgentWorkflow Hook

Programmatic workflow management:

```typescript
import { useAgentWorkflow } from '@/hooks/useAgentWorkflow';

export function MyComponent() {
  const { 
    startFineTuning,
    startOptimization,
    activeWorkflow,
    isLoading,
    error
  } = useAgentWorkflow({
    autoPolling: true,
    pollingInterval: 2000
  });

  const handleStartTraining = async () => {
    const workflowId = await startFineTuning({
      task_type: 'bug_detection',
      model: 'gpt-3.5-turbo'
    });
    console.log(`Started workflow: ${workflowId}`);
  };

  return (
    <div>
      <button onClick={handleStartTraining} disabled={isLoading}>
        Start Training
      </button>
      {error && <p>Error: {error}</p>}
      {activeWorkflow && (
        <p>Workflow {activeWorkflow.workflow_id}: {activeWorkflow.status}</p>
      )}
    </div>
  );
}
```

## Architecture

### Agent Classes

All agents inherit from `BaseAgent` and implement:

- `async think(input_text: str) -> str` - Process input
- `async act(action: str, params: dict) -> any` - Execute tools

### Example: Creating Custom Agent

```python
from api.agents.agent_definitions import BaseAgent, AgentRole, ToolDefinition

class MyCustomAgent(BaseAgent):
    def __init__(self):
        tools = [
            ToolDefinition(
                name="my_tool",
                description="Does something useful",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
                handler=self.my_tool_handler
            )
        ]
        super().__init__(
            agent_id="my_custom_agent",
            name="MyCustomAgent",
            role=AgentRole.ANALYZER,
            description="My custom agent",
            tools=tools,
            system_prompt="You are a helpful agent..."
        )

    async def think(self, input_text: str) -> str:
        # Custom thinking logic
        return f"Analyzing: {input_text}"

    async def act(self, action: str, params: dict) -> Any:
        if action == "my_tool":
            return self.my_tool_handler(**params)
        raise ValueError(f"Unknown action: {action}")

    @staticmethod
    def my_tool_handler(**params) -> dict:
        # Custom tool implementation
        return {"result": "success"}
```

## Workflow Execution

### Fine-Tuning Workflow Steps

1. **FineTuningOrchestrator** lists available models
2. Prepares training dataset
3. Starts fine-tuning job
4. **CodeReviewerAgent** reviews training code
5. Validates fine-tuned model
6. Deploys to production

### Optimization Workflow Steps

1. **LoadTestAnalyzer** retrieves test results
2. Analyzes latency patterns
3. Identifies bottlenecks
4. **PerformanceAdvisor** recommends optimizations
   - Caching strategies
   - Database indexes
   - Query patterns
   - Scaling approach
5. **CodeReviewerAgent** reviews optimization code
6. Returns prioritized recommendations

## Key Files

- **Agent Definitions**: `api/agents/agent_definitions.py`
- **Agent Implementations**: `api/agents/phase8_agents.py`
- **Agent Tools**: `api/agents/agent_tools.py`
- **Orchestration Service**: `api/services/agent_orchestration_service.py`
- **API Routes**: `api/routes/agents.py`
- **Frontend Store**: `src/stores/agentStore.ts`
- **Frontend Hook**: `src/hooks/useAgentWorkflow.ts`
- **Frontend Components**: `src/components/agents/`

## Configuration

### Environment Variables

```bash
# Agent system
AGENT_MAX_WORKFLOWS=100
AGENT_CLEANUP_INTERVAL_HOURS=24

# Fine-tuning
FINE_TUNING_TIMEOUT_MINUTES=60

# Optimization
OPTIMIZATION_TIMEOUT_MINUTES=5
```

### Workflow Customization

In `api/services/agent_orchestration_service.py`:

```python
# Adjust workflow parameters
async def execute_fine_tuning_workflow(self, request: Dict[str, Any]):
    # Custom fine-tuning steps
    pass

async def execute_optimization_workflow(self, request: Dict[str, Any]):
    # Custom optimization steps
    pass
```

## Testing

### Run Agent Tests

```bash
# Test definitions
pytest tests/agents/test_agent_definitions.py -v

# Test orchestration
pytest tests/agents/test_agent_orchestration.py -v

# All agent tests
pytest tests/agents/ -v
```

### Example Test

```python
@pytest.mark.asyncio
async def test_fine_tuning_workflow(orchestration_service):
    request = {
        "task_type": "bug_detection",
        "model": "gpt-3.5-turbo"
    }
    
    workflow = await orchestration_service.execute_fine_tuning_workflow(request)
    
    assert workflow.final_result is not None
    assert "model_id" in workflow.final_result
```

## Troubleshooting

### Workflow Stuck in "running" Status

Check logs:
```bash
tail -f logs/agents.log
```

Kill stuck workflow and cleanup:
```bash
curl -X DELETE http://localhost:8000/api/agents/cleanup?hours=0
```

### Agent Not Responding

Increase timeout in tool definition:
```python
ToolDefinition(..., timeout_seconds=60)
```

### Memory Issues

Reduce max workflows:
```python
AGENT_MAX_WORKFLOWS = 10  # from 100
```

## Performance

- Fine-tuning workflow: ~2.5-4.5 hours
- Optimization workflow: ~10-20 seconds
- Max concurrent workflows: 100
- Memory per workflow: ~50MB

## Integration with Phase 8

The agent system integrates with all Phase 8 components:

- **8.1 Bug Detection**: Fine-tuning uses bug detection dataset
- **8.2 Caching**: Recommendations improve cache strategy
- **8.3 Database**: Suggestions improve indexes and queries
- **8.4 Load Testing**: Analyzes Phase 8.4 load test results
- **8.5 Monitoring**: Uses Phase 8.5 metrics for decisions

## Next Steps

1. Deploy agent system to staging
2. Run sample workflows
3. Monitor performance and metrics
4. Integrate with frontend dashboard
5. Set up monitoring and alerts

## Documentation

For detailed documentation, see:
- `PHASE8_6_AUTOGEN_AGENTS.md` - Complete architecture guide
- `api/agents/agent_definitions.py` - Class documentation
- `api/agents/phase8_agents.py` - Agent implementation details
- `api/routes/agents.py` - API endpoint documentation

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review PHASE8_6_AUTOGEN_AGENTS.md
3. Examine agent logs
4. Check test files for usage examples
