#!/usr/bin/env python3
"""
Task Service
Handles task execution and status tracking with WebSocket integration
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task data structure"""
    task_id: str
    task_type: str  # repository_scan, file_analysis, code_review, etc.
    status: str = TaskStatus.PENDING
    progress: int = 0
    message: str = ""
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    result: Dict[str, Any] = None
    error: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}


class TaskService:
    """Manages task execution and tracking"""

    def __init__(self):
        """Initialize task service"""
        self.tasks: Dict[str, Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.user_tasks: Dict[str, List[str]] = {}  # user_id -> [task_ids]
        self.broadcast_callback: Optional[Callable] = None

    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        Register a task handler

        Args:
            task_type: Task type to handle
            handler: Async handler function
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def set_broadcast_callback(self, callback: Callable) -> None:
        """
        Set callback for broadcasting task status updates

        Args:
            callback: Async callback function
        """
        self.broadcast_callback = callback

    def create_task(
        self,
        task_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Create a new task

        Args:
            task_type: Task type
            user_id: User ID
            metadata: Optional metadata

        Returns:
            Created task
        """
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            task_type=task_type,
            metadata=metadata or {},
        )

        self.tasks[task_id] = task

        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = []

        self.user_tasks[user_id].append(task_id)

        logger.info(f"Created task {task_id} of type {task_type} for user {user_id}")

        return task

    async def update_task_progress(
        self,
        task_id: str,
        progress: int,
        message: str,
        status: Optional[str] = None,
    ) -> Task:
        """
        Update task progress

        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
            message: Status message
            status: Optional new status

        Returns:
            Updated task
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]
        task.progress = max(0, min(100, progress))
        task.message = message

        if status:
            task.status = status
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.utcnow().isoformat()
            elif status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow().isoformat()

        # Broadcast update
        if self.broadcast_callback:
            try:
                await self.broadcast_callback(
                    task_id=task_id,
                    status=task.status,
                    progress=task.progress,
                    message=task.message,
                    metadata=task.metadata,
                )
            except Exception as e:
                logger.error(f"Error broadcasting task update: {e}")

        return task

    async def complete_task(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Mark task as completed

        Args:
            task_id: Task ID
            result: Optional result data

        Returns:
            Completed task
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]
        task.result = result or {}
        task.completed_at = datetime.utcnow().isoformat()

        return await self.update_task_progress(
            task_id,
            100,
            "Completed",
            TaskStatus.COMPLETED,
        )

    async def fail_task(
        self,
        task_id: str,
        error: str,
    ) -> Task:
        """
        Mark task as failed

        Args:
            task_id: Task ID
            error: Error message

        Returns:
            Failed task
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]
        task.error = error
        task.completed_at = datetime.utcnow().isoformat()

        return await self.update_task_progress(
            task_id,
            0,
            f"Failed: {error}",
            TaskStatus.FAILED,
        )

    async def execute_task(
        self,
        task_id: str,
        task_type: str,
        data: Dict[str, Any],
    ) -> Any:
        """
        Execute a task

        Args:
            task_id: Task ID
            task_type: Task type
            data: Task data

        Returns:
            Task result
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        if task_type not in self.task_handlers:
            raise ValueError(f"No handler for task type {task_type}")

        task = self.tasks[task_id]

        try:
            # Mark task as running
            await self.update_task_progress(
                task_id,
                0,
                "Starting...",
                TaskStatus.RUNNING,
            )

            # Execute handler
            handler = self.task_handlers[task_type]
            result = await handler(task_id, data, self.update_task_progress)

            # Mark as completed
            await self.complete_task(task_id, result)

            return result

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self.fail_task(task_id, str(e))
            raise

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID

        Args:
            task_id: Task ID

        Returns:
            Task or None
        """
        return self.tasks.get(task_id)

    def get_user_tasks(self, user_id: str) -> List[Task]:
        """
        Get all tasks for a user

        Args:
            user_id: User ID

        Returns:
            List of tasks
        """
        task_ids = self.user_tasks.get(user_id, [])
        return [self.tasks.get(task_id) for task_id in task_ids if task_id in self.tasks]

    def get_task_stats(self) -> Dict[str, Any]:
        """
        Get task statistics

        Returns:
            Stats dict
        """
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": total_tasks - completed - failed - running,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global task service instance
task_service = TaskService()
