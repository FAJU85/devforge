#!/usr/bin/env python3
"""
Phase 8.6: Agent Orchestration API Routes
REST API endpoints for multi-agent workflows
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
import asyncio

from api.services.agent_orchestration_service import agent_orchestration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


# Request/Response Models
class FineTuningRequest(BaseModel):
    """Fine-tuning workflow request"""
    task_type: str = Field(..., description="Task type: bug_detection, code_optimization, performance_prediction")
    model: str = Field(default="gpt-3.5-turbo", description="Model to fine-tune")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Fine-tuning parameters")
    target_metric: Optional[str] = Field(default="accuracy", description="Target metric to optimize")


class OptimizationRequest(BaseModel):
    """Optimization workflow request"""
    load_test_id: str = Field(..., description="Load test ID to analyze")
    metrics_target: Optional[Dict[str, float]] = Field(default={}, description="Target metrics")
    constraints: Optional[Dict[str, Any]] = Field(default={}, description="Optimization constraints")


class WorkflowResponse(BaseModel):
    """Workflow response"""
    workflow_id: str
    workflow_type: str
    status: str
    created_at: str
    estimated_duration_seconds: Optional[int] = None


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow_id: str
    workflow_type: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    agent_count: int
    message_count: int
    error_message: Optional[str] = None


class AgentMessage(BaseModel):
    """Agent message in conversation"""
    agent_id: str
    agent_name: str
    message_type: str
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class WorkflowResultsResponse(BaseModel):
    """Workflow results response"""
    workflow_id: str
    workflow_type: str
    initial_request: Dict[str, Any]
    final_result: Optional[Dict[str, Any]] = None
    agent_states: Dict[str, Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str] = None


class ActiveWorkflowsResponse(BaseModel):
    """Active workflows list"""
    total_count: int
    workflows: List[Dict[str, Any]]


# Routes

@router.post(
    "/orchestrate/fine-tune",
    response_model=WorkflowResponse,
    summary="Trigger fine-tuning workflow",
    description="Start a multi-agent workflow to fine-tune a model"
)
async def trigger_fine_tuning(
    request: FineTuningRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger fine-tuning workflow

    The FineTuningOrchestrator will:
    1. List available models
    2. Prepare training dataset
    3. Start fine-tuning job
    4. CodeReviewerAgent reviews training code
    5. Validate fine-tuned model
    6. Deploy model to production
    """
    try:
        # Create workflow
        workflow = agent_orchestration_service.create_workflow(
            "fine_tuning",
            request.dict()
        )

        # Execute workflow in background
        background_tasks.add_task(
            agent_orchestration_service.execute_fine_tuning_workflow,
            request.dict()
        )

        return WorkflowResponse(
            workflow_id=workflow.workflow_id,
            workflow_type="fine_tuning",
            status="queued",
            created_at=workflow.created_at.isoformat(),
            estimated_duration_seconds=3600
        )

    except Exception as e:
        logger.error(f"Error triggering fine-tuning workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/orchestrate/optimize",
    response_model=WorkflowResponse,
    summary="Trigger optimization workflow",
    description="Start multi-agent workflow to optimize performance"
)
async def trigger_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger optimization workflow

    The workflow coordinates:
    1. LoadTestAnalyzer: Analyzes load test results
    2. PerformanceAdvisor: Recommends optimizations
    3. CodeReviewerAgent: Reviews optimization code
    """
    try:
        # Create workflow
        workflow = agent_orchestration_service.create_workflow(
            "optimization",
            request.dict()
        )

        # Execute workflow in background
        background_tasks.add_task(
            agent_orchestration_service.execute_optimization_workflow,
            request.dict()
        )

        return WorkflowResponse(
            workflow_id=workflow.workflow_id,
            workflow_type="optimization",
            status="queued",
            created_at=workflow.created_at.isoformat(),
            estimated_duration_seconds=300
        )

    except Exception as e:
        logger.error(f"Error triggering optimization workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/orchestrate/{workflow_id}",
    response_model=WorkflowStatusResponse,
    summary="Get workflow status",
    description="Get current status of a workflow"
)
async def get_workflow_status(workflow_id: str):
    """
    Get workflow status

    Returns current status, progress, and agent states
    """
    try:
        status = agent_orchestration_service.get_workflow_status(workflow_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        return WorkflowStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/orchestrate/{workflow_id}/results",
    response_model=WorkflowResultsResponse,
    summary="Get workflow results",
    description="Get final results and conversation history"
)
async def get_workflow_results(workflow_id: str):
    """
    Get workflow results

    Returns:
    - Initial request parameters
    - Final recommendations and results
    - Full conversation history between agents
    - Agent analysis states
    """
    try:
        results = agent_orchestration_service.get_workflow_results(workflow_id)
        if "error" in results:
            raise HTTPException(status_code=404, detail=results["error"])

        return WorkflowResultsResponse(**results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=ActiveWorkflowsResponse,
    summary="Get all active workflows",
    description="List all active agent workflows"
)
async def get_all_workflows(
    status: Optional[str] = Query(None, description="Filter by status: running, completed")
):
    """
    Get all active workflows

    Returns list of all workflows with their status
    """
    try:
        workflows = agent_orchestration_service.get_all_workflows()

        if status:
            workflows = [w for w in workflows if w["status"] == status]

        return ActiveWorkflowsResponse(
            total_count=len(workflows),
            workflows=workflows
        )

    except Exception as e:
        logger.error(f"Error getting workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/cleanup",
    summary="Clean up old workflows",
    description="Remove workflows older than specified hours"
)
async def cleanup_workflows(hours: int = Query(24, description="Remove workflows older than N hours")):
    """
    Clean up old workflows

    Removes workflows that have been completed for more than N hours
    """
    try:
        cleared_count = agent_orchestration_service.clear_old_workflows(hours)

        return {
            "success": True,
            "cleared_count": cleared_count,
            "message": f"Cleared {cleared_count} workflows older than {hours} hours"
        }

    except Exception as e:
        logger.error(f"Error cleaning up workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/models",
    summary="List available models",
    description="List models available for fine-tuning"
)
async def list_available_models():
    """
    List available models

    Returns list of models that can be fine-tuned
    """
    from api.agents.agent_tools import FineTuningTools

    try:
        models = FineTuningTools.list_available_models()
        return models
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Agent system health check",
    description="Check health of agent orchestration system"
)
async def health_check():
    """
    Health check for agent system

    Returns status of all agent components
    """
    try:
        active_workflows = len(agent_orchestration_service.get_all_workflows())

        return {
            "status": "healthy",
            "timestamp": str(__import__('datetime').datetime.utcnow().isoformat()),
            "active_workflows": active_workflows,
            "agents_available": list(agent_orchestration_service.agent_classes.keys()),
            "version": "1.0.0"
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


logger.info("Agent routes initialized")
