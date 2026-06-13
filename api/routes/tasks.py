#!/usr/bin/env python3
"""
Task Routes
Handles task creation, status tracking, and real-time updates
"""

from fastapi import APIRouter, HTTPException, Cookie, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from api.services.task_service import task_service, TaskStatus
from api.services.repository_service import repository_service
from api.services.auth_service import auth_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    """Create task request"""
    task_type: str = Field(..., min_length=1, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScanRepositoryRequest(BaseModel):
    """Scan repository request"""
    token: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    repo: str = Field(..., min_length=1)


async def get_current_user(session_token: str = Cookie(None)):
    """Dependency to get current user from session"""
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = auth_service.get_user_from_session(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get task status

    Args:
        task_id: Task ID

    Returns:
        Task information
    """
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "result": task.result,
        "error": task.error,
        "metadata": task.metadata,
    }


@router.get("")
async def list_user_tasks(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List user's tasks

    Returns:
        List of tasks
    """
    user_id = str(user.get("id", ""))
    tasks = task_service.get_user_tasks(user_id)

    return {
        "tasks": [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "created_at": task.created_at,
            }
            for task in tasks
        ]
    }


@router.post("/scan-repository")
async def scan_repository(
    request: ScanRepositoryRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Start repository scan task

    Args:
        request: Scan request with token, owner, repo

    Returns:
        Task information
    """
    try:
        # Create task
        user_id = str(user.get("id", ""))
        task = task_service.create_task(
            "scan_repository",
            user_id,
            {
                "token": request.token,
                "owner": request.owner,
                "repo": request.repo,
            },
        )

        # Start task execution in background
        import asyncio

        async def execute():
            async def update_progress(progress: int, message: str):
                await task_service.update_task_progress(task.task_id, progress, message)

            try:
                result = await repository_service.scan_repository(
                    request.token,
                    request.owner,
                    request.repo,
                    update_progress,
                )
                await task_service.complete_task(task.task_id, result)
            except Exception as e:
                await task_service.fail_task(task.task_id, str(e))

        asyncio.create_task(execute())

        return {
            "task_id": task.task_id,
            "status": task.status,
            "message": "Task started",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_task_stats(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get task statistics

    Returns:
        Task statistics
    """
    return task_service.get_task_stats()
