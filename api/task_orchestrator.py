#!/usr/bin/env python3
"""
Task Orchestrator - Coordinates agents and Phase 1 infrastructure
Manages task execution, logging, and results storage
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

from ml.agents import (
    BrowserAgent,
    TestGenerationAgent,
    BugDetectionAgent,
    WebTaskAgent
)

app = FastAPI(
    title="DevForge Task Orchestrator",
    description="Coordinates agents and Phase 1 infrastructure",
    version="2.0.0"
)

# Task storage (in production, use PostgreSQL via ml.clients)
tasks_registry: Dict[str, Dict] = {}


class TaskType(str, Enum):
    """Task types"""
    BROWSER_AUTOMATION = "browser_automation"
    TEST_GENERATION = "test_generation"
    BUG_DETECTION = "bug_detection"
    WEB_TASK = "web_task"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OrchestratorTaskRequest(BaseModel):
    """Request to orchestrate a task"""
    task_type: TaskType
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    params: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class BatchTaskRequest(BaseModel):
    """Request to execute batch tasks"""
    tasks: List[OrchestratorTaskRequest]
    parallel: bool = False


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Task Orchestrator",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/orchestrator/task")
async def create_task(request: OrchestratorTaskRequest, background_tasks: BackgroundTasks):
    """Create and orchestrate a task"""
    task_id = str(uuid.uuid4())

    task_record = {
        "task_id": task_id,
        "task_type": request.task_type.value,
        "description": request.description,
        "priority": request.priority.value,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "params": request.params,
        "metadata": request.metadata or {},
        "result": None,
        "error": None
    }

    tasks_registry[task_id] = task_record

    # Execute task in background based on type
    if request.task_type == TaskType.BROWSER_AUTOMATION:
        background_tasks.add_task(
            execute_browser_automation,
            task_id,
            request.params
        )
    elif request.task_type == TaskType.TEST_GENERATION:
        background_tasks.add_task(
            execute_test_generation,
            task_id,
            request.params
        )
    elif request.task_type == TaskType.BUG_DETECTION:
        background_tasks.add_task(
            execute_bug_detection,
            task_id,
            request.params
        )
    elif request.task_type == TaskType.WEB_TASK:
        background_tasks.add_task(
            execute_web_task,
            task_id,
            request.params
        )

    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"Task {task_id} created and queued"
    }


async def execute_browser_automation(task_id: str, params: Dict):
    """Execute browser automation task"""
    task = tasks_registry[task_id]
    task["status"] = "running"
    task["started_at"] = datetime.utcnow().isoformat()

    try:
        agent = BrowserAgent()
        await agent.start()

        result = await agent.execute_task(
            task_description=params.get("description", ""),
            max_iterations=params.get("max_steps", 50)
        )

        await agent.stop()

        task["result"] = result
        task["status"] = "completed"

    except Exception as e:
        task["error"] = str(e)
        task["status"] = "failed"

    finally:
        task["completed_at"] = datetime.utcnow().isoformat()


async def execute_test_generation(task_id: str, params: Dict):
    """Execute test generation task"""
    task = tasks_registry[task_id]
    task["status"] = "running"
    task["started_at"] = datetime.utcnow().isoformat()

    try:
        agent = TestGenerationAgent()

        if params.get("suite"):
            result = agent.generate_test_suite(
                feature_description=params.get("description", ""),
                test_scenarios=params.get("scenarios", []),
                framework=params.get("framework", "pytest")
            )
        else:
            result = agent.generate_test(
                description=params.get("description", ""),
                target_url=params.get("url"),
                framework=params.get("framework", "pytest"),
                context=params.get("context")
            )

        task["result"] = result
        task["status"] = "completed"

    except Exception as e:
        task["error"] = str(e)
        task["status"] = "failed"

    finally:
        task["completed_at"] = datetime.utcnow().isoformat()


async def execute_bug_detection(task_id: str, params: Dict):
    """Execute bug detection task"""
    task = tasks_registry[task_id]
    task["status"] = "running"
    task["started_at"] = datetime.utcnow().isoformat()

    try:
        agent = BugDetectionAgent()
        await agent.start()

        result = await agent.detect_bugs(
            url=params.get("url", ""),
            test_cases=params.get("test_cases"),
            max_interactions=params.get("max_interactions", 10)
        )

        await agent.stop()

        task["result"] = result
        task["status"] = "completed"

    except Exception as e:
        task["error"] = str(e)
        task["status"] = "failed"

    finally:
        task["completed_at"] = datetime.utcnow().isoformat()


async def execute_web_task(task_id: str, params: Dict):
    """Execute web task"""
    task = tasks_registry[task_id]
    task["status"] = "running"
    task["started_at"] = datetime.utcnow().isoformat()

    try:
        agent = WebTaskAgent()
        await agent.start()

        result = await agent.execute_task(
            task_description=params.get("description", ""),
            start_url=params.get("start_url"),
            context=params.get("context"),
            max_iterations=params.get("max_steps", 50)
        )

        await agent.stop()

        result_dict = {
            "task_id": result.task_id,
            "status": result.status,
            "steps": result.steps_executed,
            "output": result.output,
            "errors": result.errors
        }

        task["result"] = result_dict
        task["status"] = "completed"

    except Exception as e:
        task["error"] = str(e)
        task["status"] = "failed"

    finally:
        task["completed_at"] = datetime.utcnow().isoformat()


@app.get("/api/orchestrator/task/{task_id}")
async def get_task(task_id: str):
    """Get task status and result"""
    if task_id not in tasks_registry:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_registry[task_id]

    return {
        "task_id": task_id,
        "task_type": task["task_type"],
        "status": task["status"],
        "description": task["description"],
        "priority": task["priority"],
        "created_at": task["created_at"],
        "started_at": task["started_at"],
        "completed_at": task["completed_at"],
        "result": task["result"],
        "error": task["error"]
    }


@app.get("/api/orchestrator/tasks")
async def list_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    """List tasks with filtering"""
    tasks = []

    for task_id, task in tasks_registry.items():
        if task_type and task["task_type"] != task_type:
            continue
        if status and task["status"] != status:
            continue
        if priority and task["priority"] != priority:
            continue

        tasks.append({
            "task_id": task_id,
            "task_type": task["task_type"],
            "status": task["status"],
            "priority": task["priority"],
            "created_at": task["created_at"]
        })

    return {
        "tasks": tasks,
        "count": len(tasks)
    }


@app.post("/api/orchestrator/batch")
async def execute_batch(request: BatchTaskRequest, background_tasks: BackgroundTasks):
    """Execute a batch of tasks"""
    task_ids = []

    for task_request in request.tasks:
        task_id = str(uuid.uuid4())

        task_record = {
            "task_id": task_id,
            "task_type": task_request.task_type.value,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }

        tasks_registry[task_id] = task_record
        task_ids.append(task_id)

        # Add to background tasks
        if task_request.task_type == TaskType.BROWSER_AUTOMATION:
            background_tasks.add_task(
                execute_browser_automation,
                task_id,
                task_request.params
            )

    return {
        "batch_id": str(uuid.uuid4()),
        "task_ids": task_ids,
        "count": len(task_ids),
        "parallel": request.parallel
    }


@app.delete("/api/orchestrator/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in tasks_registry:
        raise HTTPException(status_code=404, detail="Task not found")

    del tasks_registry[task_id]

    return {
        "status": "success",
        "message": f"Task {task_id} deleted"
    }


@app.get("/api/orchestrator/stats")
async def get_stats():
    """Get orchestrator statistics"""
    total = len(tasks_registry)
    completed = sum(1 for t in tasks_registry.values() if t["status"] == "completed")
    failed = sum(1 for t in tasks_registry.values() if t["status"] == "failed")
    running = sum(1 for t in tasks_registry.values() if t["status"] == "running")
    pending = total - completed - failed - running

    # Stats by type
    by_type = {}
    for task in tasks_registry.values():
        task_type = task["task_type"]
        if task_type not in by_type:
            by_type[task_type] = 0
        by_type[task_type] += 1

    # Stats by priority
    by_priority = {}
    for task in tasks_registry.values():
        priority = task.get("priority", "medium")
        if priority not in by_priority:
            by_priority[priority] = 0
        by_priority[priority] += 1

    return {
        "total_tasks": total,
        "status": {
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending
        },
        "by_type": by_type,
        "by_priority": by_priority
    }


@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "DevForge Task Orchestrator",
        "version": "2.0.0",
        "description": "Coordinates agents and Phase 1 infrastructure",
        "endpoints": {
            "health": "/health",
            "create_task": "POST /api/orchestrator/task",
            "get_task": "GET /api/orchestrator/task/{task_id}",
            "list_tasks": "GET /api/orchestrator/tasks",
            "batch_tasks": "POST /api/orchestrator/batch",
            "statistics": "GET /api/orchestrator/stats"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("TASK_API_PORT", 8003))
    print(f"Starting Task Orchestrator on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
