#!/usr/bin/env python3
"""
WebSocket Server
Handles real-time updates and task status streaming
"""

import json
import asyncio
from typing import Dict, Set, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    HEARTBEAT = "heartbeat"
    STATUS = "status"
    UPDATE = "update"
    NOTIFICATION = "notification"
    ERROR = "error"
    TASK_PROGRESS = "task_progress"
    SYNC = "sync"
    MESSAGE = "message"


@dataclass
class TaskStatusUpdate:
    """Task status update structure"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: str
    timestamp: str = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: str
    data: Any
    timestamp: str = None
    id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self))


class WebSocketConnectionManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Dict[str, Set[Any]] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> message_types
        self.task_subscriptions: Dict[str, Set[str]] = {}  # task_id -> user_ids
        self.message_handlers: Dict[str, Callable] = {}

    async def connect(self, user_id: str, websocket: Any) -> None:
        """
        Register a new WebSocket connection

        Args:
            user_id: User ID
            websocket: WebSocket connection object
        """
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    async def disconnect(self, user_id: str, websocket: Any) -> None:
        """
        Unregister a WebSocket connection

        Args:
            user_id: User ID
            websocket: WebSocket connection object
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_subscriptions:
                    del self.user_subscriptions[user_id]
                logger.info(f"User {user_id} disconnected")

    def subscribe_user(self, user_id: str, message_types: list) -> None:
        """
        Subscribe user to specific message types

        Args:
            user_id: User ID
            message_types: List of message types to subscribe to
        """
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()

        self.user_subscriptions[user_id].update(message_types)
        logger.info(f"User {user_id} subscribed to: {message_types}")

    def subscribe_task(self, task_id: str, user_ids: list) -> None:
        """
        Subscribe users to task updates

        Args:
            task_id: Task ID
            user_ids: List of user IDs to subscribe
        """
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = set()

        self.task_subscriptions[task_id].update(user_ids)
        logger.info(f"Task {task_id} subscribed by users: {user_ids}")

    async def broadcast_to_user(
        self,
        user_id: str,
        message_type: str,
        data: Any,
    ) -> None:
        """
        Broadcast message to all connections of a user

        Args:
            user_id: User ID
            message_type: Message type
            data: Message data
        """
        if user_id not in self.active_connections:
            return

        message = WebSocketMessage(type=message_type, data=data)
        message_json = message.to_json()

        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected.add(websocket)

        # Cleanup disconnected connections
        for websocket in disconnected:
            await self.disconnect(user_id, websocket)

    async def broadcast_task_update(
        self,
        task_id: str,
        status: str,
        progress: int,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Broadcast task status update to all subscribed users

        Args:
            task_id: Task ID
            status: Task status
            progress: Progress percentage (0-100)
            message: Status message
            metadata: Optional metadata
        """
        if task_id not in self.task_subscriptions:
            return

        update = TaskStatusUpdate(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            metadata=metadata or {},
        )

        message = WebSocketMessage(
            type=MessageType.TASK_PROGRESS,
            data=asdict(update),
        )
        message_json = message.to_json()

        for user_id in self.task_subscriptions[task_id]:
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_text(message_json)
                    except Exception as e:
                        logger.error(f"Error sending task update to user {user_id}: {e}")

    async def broadcast_to_all(
        self,
        message_type: str,
        data: Any,
    ) -> None:
        """
        Broadcast message to all connected users

        Args:
            message_type: Message type
            data: Message data
        """
        message = WebSocketMessage(type=message_type, data=data)
        message_json = message.to_json()

        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, message_type, data)

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a message handler

        Args:
            message_type: Message type to handle
            handler: Async handler function
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")

    async def handle_message(
        self,
        user_id: str,
        message_data: Dict[str, Any],
    ) -> None:
        """
        Handle incoming message

        Args:
            user_id: User ID
            message_data: Message data dict
        """
        message_type = message_data.get("type")
        data = message_data.get("data", {})

        # Handle heartbeat
        if message_type == MessageType.HEARTBEAT:
            await self.broadcast_to_user(
                user_id,
                MessageType.STATUS,
                {"status": "pong"},
            )
            return

        # Handle subscription
        if message_type == "subscribe":
            message_types = data.get("types", [])
            self.subscribe_user(user_id, message_types)
            return

        # Handle task subscription
        if message_type == "subscribe_task":
            task_id = data.get("task_id")
            if task_id:
                self.subscribe_task(task_id, [user_id])
            return

        # Call registered handler if available
        if message_type in self.message_handlers:
            handler = self.message_handlers[message_type]
            try:
                await handler(user_id, data)
            except Exception as e:
                logger.error(f"Error in message handler for {message_type}: {e}")
                await self.broadcast_to_user(
                    user_id,
                    MessageType.ERROR,
                    {"error": f"Handler error: {str(e)}"},
                )

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics

        Returns:
            Stats dict
        """
        total_users = len(self.active_connections)
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        total_subscriptions = sum(len(types) for types in self.user_subscriptions.values())

        return {
            "total_users": total_users,
            "total_connections": total_connections,
            "total_subscriptions": total_subscriptions,
            "active_tasks": len(self.task_subscriptions),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global connection manager instance
connection_manager = WebSocketConnectionManager()
