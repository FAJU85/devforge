#!/usr/bin/env python3
"""
Agent Orchestration REST API Server
Exposes all AI agents via HTTP endpoints
Integrates with Phase 1 infrastructure
"""

import os
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from ml.agents import (
    BrowserAgent,
    TestGenerationAgent,
    BugDetectionAgent,
    WebTaskAgent
)

# Initialize FastAPI app
app = FastAPI(
    title="DevForge Agent Orchestration API",
    description="REST API for AI-powered web automation and testing agents",
    version="2.0.0"
)

# In-memory task storage (in production, use PostgreSQL)
tasks_db: Dict[str, Dict] = {}
agents_sessions: Dict[str, Any] = {}


class AgentType(str, Enum):
    """Available agent types"""
    BROWSER = "browser"
    TEST_GENERATOR = "test_generator"
    BUG_DETECTOR = "bug_detector"
    WEB_TASK = "web_task"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Request/Response Models

class BrowserTaskRequest(BaseModel):
    """Request to execute a browser task"""
    description: str
    url: Optional[str] = None
    max_steps: Optional[int] = 50


class TestGenerationRequest(BaseModel):
    """Request to generate tests"""
    description: str
    url: Optional[str] = None
    framework: str = "pytest"
    context: Optional[Dict] = None


class BugDetectionRequest(BaseModel):
    """Request to detect bugs"""
    url: str
    test_cases: Optional[List[str]] = None
    max_interactions: int = 10


class WebTaskRequest(BaseModel):
    """Request to execute a web task"""
    description: str
    start_url: Optional[str] = None
    context: Optional[Dict] = None
    max_steps: Optional[int] = 50


class TaskResponse(BaseModel):
    """Response with task details"""
    task_id: str
    status: str
    agent_type: str
    created_at: str
    result: Optional[Dict] = None


class TaskStatusResponse(BaseModel):
    """Response with current task status"""
    task_id: str
    status: str
    progress: int  # 0-100
    result: Optional[Dict] = None


# Health check endpoint

@app.get("/health")
async def health_check():
    """Check API health"""
    return {
        "status": "healthy",
        "service": "Agent Orchestration API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# Browser Agent Endpoints

@app.post("/api/agents/browser/task")
async def execute_browser_task(request: BrowserTaskRequest, background_tasks: BackgroundTasks):
    """Execute a task with the Browser Agent"""
    task_id = str(uuid.uuid4())

    task_info = {
        "task_id": task_id,
        "agent_type": "browser",
        "status": TaskStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "request": request.dict(),
        "result": None
    }

    tasks_db[task_id] = task_info

    # Execute in background
    background_tasks.add_task(
        _execute_browser_agent,
        task_id,
        request
    )

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        agent_type="browser",
        created_at=task_info["created_at"]
    )


async def _execute_browser_agent(task_id: str, request: BrowserTaskRequest):
    """Execute browser agent task (background)"""
    try:
        tasks_db[task_id]["status"] = TaskStatus.RUNNING

        agent = BrowserAgent()
        await agent.start()

        result = await agent.execute_task(
            task_description=request.description,
            max_iterations=request.max_steps
        )

        await agent.stop()

        tasks_db[task_id]["status"] = TaskStatus.COMPLETED
        tasks_db[task_id]["result"] = result

    except Exception as e:
        tasks_db[task_id]["status"] = TaskStatus.FAILED
        tasks_db[task_id]["result"] = {"error": str(e)}


@app.get("/api/agents/browser/screenshot/{task_id}")
async def get_browser_screenshot(task_id: str):
    """Get screenshot from browser task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]
    result = task.get("result", {})

    if "screenshot" not in result:
        raise HTTPException(status_code=404, detail="No screenshot available")

    return JSONResponse({
        "task_id": task_id,
        "screenshot": result["screenshot"]
    })


# Test Generation Endpoints

@app.post("/api/agents/test-generator/generate")
async def generate_test(request: TestGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a test using the Test Generator Agent"""
    task_id = str(uuid.uuid4())

    task_info = {
        "task_id": task_id,
        "agent_type": "test_generator",
        "status": TaskStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "request": request.dict(),
        "result": None
    }

    tasks_db[task_id] = task_info

    background_tasks.add_task(
        _execute_test_generator,
        task_id,
        request
    )

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        agent_type="test_generator",
        created_at=task_info["created_at"]
    )


async def _execute_test_generator(task_id: str, request: TestGenerationRequest):
    """Execute test generator task (background)"""
    try:
        tasks_db[task_id]["status"] = TaskStatus.RUNNING

        agent = TestGenerationAgent()
        result = agent.generate_test(
            description=request.description,
            target_url=request.url,
            framework=request.framework,
            context=request.context
        )

        tasks_db[task_id]["status"] = TaskStatus.COMPLETED
        tasks_db[task_id]["result"] = result

    except Exception as e:
        tasks_db[task_id]["status"] = TaskStatus.FAILED
        tasks_db[task_id]["result"] = {"error": str(e)}


@app.post("/api/agents/test-generator/suite")
async def generate_test_suite(request: Dict, background_tasks: BackgroundTasks):
    """Generate a complete test suite"""
    task_id = str(uuid.uuid4())

    task_info = {
        "task_id": task_id,
        "agent_type": "test_generator",
        "status": TaskStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "request": request,
        "result": None
    }

    tasks_db[task_id] = task_info

    background_tasks.add_task(
        _execute_test_suite_generator,
        task_id,
        request
    )

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        agent_type="test_generator",
        created_at=task_info["created_at"]
    )


async def _execute_test_suite_generator(task_id: str, request: Dict):
    """Execute test suite generator task (background)"""
    try:
        tasks_db[task_id]["status"] = TaskStatus.RUNNING

        agent = TestGenerationAgent()
        result = agent.generate_test_suite(
            feature_description=request.get("feature_description", ""),
            test_scenarios=request.get("test_scenarios", []),
            framework=request.get("framework", "pytest")
        )

        tasks_db[task_id]["status"] = TaskStatus.COMPLETED
        tasks_db[task_id]["result"] = result

    except Exception as e:
        tasks_db[task_id]["status"] = TaskStatus.FAILED
        tasks_db[task_id]["result"] = {"error": str(e)}


# Bug Detection Endpoints

@app.post("/api/agents/bug-detector/scan")
async def scan_for_bugs(request: BugDetectionRequest, background_tasks: BackgroundTasks):
    """Scan a website for bugs"""
    task_id = str(uuid.uuid4())

    task_info = {
        "task_id": task_id,
        "agent_type": "bug_detector",
        "status": TaskStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "request": request.dict(),
        "result": None
    }

    tasks_db[task_id] = task_info

    background_tasks.add_task(
        _execute_bug_detector,
        task_id,
        request
    )

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        agent_type="bug_detector",
        created_at=task_info["created_at"]
    )


async def _execute_bug_detector(task_id: str, request: BugDetectionRequest):
    """Execute bug detection task (background)"""
    try:
        tasks_db[task_id]["status"] = TaskStatus.RUNNING

        agent = BugDetectionAgent()
        await agent.start()

        result = await agent.detect_bugs(
            url=request.url,
            test_cases=request.test_cases,
            max_interactions=request.max_interactions
        )

        await agent.stop()

        tasks_db[task_id]["status"] = TaskStatus.COMPLETED
        tasks_db[task_id]["result"] = result

    except Exception as e:
        tasks_db[task_id]["status"] = TaskStatus.FAILED
        tasks_db[task_id]["result"] = {"error": str(e)}


@app.get("/api/agents/bug-detector/{task_id}/report")
async def get_bug_report(task_id: str, format: str = "json"):
    """Get bug detection report"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]

    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not yet completed")

    # In a real implementation, we would call agent.export_report(format)
    return JSONResponse({
        "task_id": task_id,
        "format": format,
        "report": task.get("result", {})
    })


# Web Task Endpoints

@app.post("/api/agents/web-task/execute")
async def execute_web_task(request: WebTaskRequest, background_tasks: BackgroundTasks):
    """Execute a web task"""
    task_id = str(uuid.uuid4())

    task_info = {
        "task_id": task_id,
        "agent_type": "web_task",
        "status": TaskStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "request": request.dict(),
        "result": None
    }

    tasks_db[task_id] = task_info

    background_tasks.add_task(
        _execute_web_task,
        task_id,
        request
    )

    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        agent_type="web_task",
        created_at=task_info["created_at"]
    )


async def _execute_web_task(task_id: str, request: WebTaskRequest):
    """Execute web task (background)"""
    try:
        tasks_db[task_id]["status"] = TaskStatus.RUNNING

        agent = WebTaskAgent()
        await agent.start()

        result = await agent.execute_task(
            task_description=request.description,
            start_url=request.start_url,
            context=request.context,
            max_iterations=request.max_steps
        )

        await agent.stop()

        # Convert TaskResult to dict
        result_dict = {
            "task_id": result.task_id,
            "status": result.status,
            "description": result.description,
            "steps_executed": result.steps_executed,
            "output": result.output,
            "errors": result.errors
        }

        tasks_db[task_id]["status"] = TaskStatus.COMPLETED
        tasks_db[task_id]["result"] = result_dict

    except Exception as e:
        tasks_db[task_id]["status"] = TaskStatus.FAILED
        tasks_db[task_id]["result"] = {"error": str(e)}


# Task Management Endpoints

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and result"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks_db[task_id]

    # Calculate progress
    progress = 0
    if task["status"] == TaskStatus.COMPLETED:
        progress = 100
    elif task["status"] == TaskStatus.RUNNING:
        progress = 50
    elif task["status"] == TaskStatus.FAILED:
        progress = 0

    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"].value,
        progress=progress,
        result=task.get("result")
    )


@app.get("/api/tasks")
async def list_tasks(agent_type: Optional[str] = None, status: Optional[str] = None):
    """List all tasks with optional filtering"""
    tasks = []

    for task_id, task in tasks_db.items():
        # Apply filters
        if agent_type and task["agent_type"] != agent_type:
            continue
        if status and task["status"] != status:
            continue

        tasks.append({
            "task_id": task_id,
            "agent_type": task["agent_type"],
            "status": task["status"].value,
            "created_at": task["created_at"]
        })

    return {"tasks": tasks, "count": len(tasks)}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")

    del tasks_db[task_id]

    return {"message": "Task deleted", "task_id": task_id}


# Agent Management Endpoints

@app.get("/api/agents")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            {
                "name": "BrowserAgent",
                "type": "browser",
                "description": "Autonomous web browser control with AI reasoning",
                "endpoint": "/api/agents/browser/task"
            },
            {
                "name": "TestGenerationAgent",
                "type": "test_generator",
                "description": "Generate tests from natural language descriptions",
                "endpoint": "/api/agents/test-generator/generate"
            },
            {
                "name": "BugDetectionAgent",
                "type": "bug_detector",
                "description": "Detect bugs through intelligent web interaction",
                "endpoint": "/api/agents/bug-detector/scan"
            },
            {
                "name": "WebTaskAgent",
                "type": "web_task",
                "description": "Execute general web automation tasks",
                "endpoint": "/api/agents/web-task/execute"
            }
        ]
    }


@app.get("/api/agents/{agent_type}/info")
async def get_agent_info(agent_type: str):
    """Get information about a specific agent"""
    agent_info = {
        "browser": {
            "name": "BrowserAgent",
            "description": "Autonomous web browser control",
            "capabilities": [
                "Navigate to URLs",
                "Click elements",
                "Fill forms",
                "Take screenshots",
                "Execute complex tasks with AI reasoning"
            ],
            "request_format": "BrowserTaskRequest"
        },
        "test_generator": {
            "name": "TestGenerationAgent",
            "description": "Generate test code from natural language",
            "capabilities": [
                "Generate single test cases",
                "Generate complete test suites",
                "Support multiple frameworks",
                "Refine tests based on feedback"
            ],
            "request_format": "TestGenerationRequest"
        },
        "bug_detector": {
            "name": "BugDetectionAgent",
            "description": "Detect bugs through web interaction",
            "capabilities": [
                "Scan websites for bugs",
                "Perform intelligent interactions",
                "Generate detailed reports",
                "Categorize bugs by severity"
            ],
            "request_format": "BugDetectionRequest"
        },
        "web_task": {
            "name": "WebTaskAgent",
            "description": "Execute web automation tasks",
            "capabilities": [
                "Execute web workflows",
                "Handle dynamic content",
                "Extract information",
                "Batch task execution"
            ],
            "request_format": "WebTaskRequest"
        }
    }

    if agent_type not in agent_info:
        raise HTTPException(status_code=404, detail="Agent type not found")

    return agent_info[agent_type]


# Statistics Endpoints

@app.get("/api/stats")
async def get_stats():
    """Get API statistics"""
    total_tasks = len(tasks_db)
    completed = sum(1 for t in tasks_db.values() if t["status"] == TaskStatus.COMPLETED)
    failed = sum(1 for t in tasks_db.values() if t["status"] == TaskStatus.FAILED)
    running = sum(1 for t in tasks_db.values() if t["status"] == TaskStatus.RUNNING)

    return {
        "total_tasks": total_tasks,
        "completed": completed,
        "failed": failed,
        "running": running,
        "pending": total_tasks - completed - failed - running
    }


@app.get("/api/stats/agents")
async def get_agent_stats():
    """Get statistics by agent type"""
    stats = {}

    for agent_type in [e.value for e in AgentType]:
        count = sum(1 for t in tasks_db.values() if t["agent_type"] == agent_type)
        stats[agent_type] = count

    return stats


# Root endpoint

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "DevForge Agent Orchestration API",
        "version": "2.0.0",
        "documentation": "/docs",
        "agents": "/api/agents",
        "tasks": "/api/tasks",
        "health": "/health"
    }


if __name__ == "__main__":
    port = int(os.getenv("AGENT_API_PORT", 8001))
    print(f"Starting Agent Orchestration API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
