#!/usr/bin/env python3
"""
Phase 8.6: AutoGen Agent Definitions
Defines the base agent classes and orchestration patterns for multi-agent system
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent role classification"""
    ORCHESTRATOR = "orchestrator"
    ANALYZER = "analyzer"
    ADVISOR = "advisor"
    REVIEWER = "reviewer"


class MessageType(str, Enum):
    """Message type in agent conversation"""
    QUERY = "query"
    RESPONSE = "response"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    DECISION = "decision"
    ERROR = "error"


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ToolDefinition:
    """Definition of a tool available to an agent"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Optional[Callable] = None
    requires_approval: bool = False
    timeout_seconds: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "requires_approval": self.requires_approval,
            "timeout_seconds": self.timeout_seconds
        }


@dataclass
class AgentMessage:
    """A message in agent conversation"""
    agent_id: str
    agent_name: str
    message_type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class AgentState:
    """Current state of an agent"""
    agent_id: str
    agent_name: str
    role: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    task_progress: float = 0.0
    last_action: Optional[str] = None
    last_action_time: Optional[datetime] = None
    messages: List[AgentMessage] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role.value,
            "status": self.status.value,
            "current_task": self.current_task,
            "task_progress": self.task_progress,
            "last_action": self.last_action,
            "last_action_time": self.last_action_time.isoformat() if self.last_action_time else None,
            "message_count": len(self.messages)
        }


class BaseAgent:
    """Base class for all agents"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        description: str,
        tools: List[ToolDefinition],
        system_prompt: str
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.description = description
        self.tools = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt
        self.state = AgentState(
            agent_id=agent_id,
            agent_name=name,
            role=role
        )
        self.conversation_history: List[AgentMessage] = []

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available tools as serializable list"""
        return [tool.to_dict() for tool in self.tools.values()]

    def add_message(self, message: AgentMessage) -> None:
        """Add message to conversation history"""
        self.conversation_history.append(message)
        self.state.messages.append(message)

    def update_status(self, status: AgentStatus, task: Optional[str] = None) -> None:
        """Update agent status"""
        self.state.status = status
        self.state.current_task = task
        self.state.last_action_time = datetime.utcnow()

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return self.state.to_dict()

    def get_conversation(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return [msg.to_dict() for msg in self.conversation_history]

    async def think(self, input_text: str) -> str:
        """Process input and generate response (to be overridden)"""
        raise NotImplementedError("Subclass must implement think()")

    async def act(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute an action using available tools (to be overridden)"""
        raise NotImplementedError("Subclass must implement act()")


class ConversationManager:
    """Manages conversations between agents"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.agents: Dict[str, BaseAgent] = {}
        self.messages: List[AgentMessage] = []
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None

    def add_agent(self, agent: BaseAgent) -> None:
        """Add agent to conversation"""
        self.agents[agent.agent_id] = agent

    def record_message(self, message: AgentMessage) -> None:
        """Record message in conversation"""
        self.messages.append(message)
        if message.agent_id in self.agents:
            self.agents[message.agent_id].add_message(message)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return [msg.to_dict() for msg in self.messages]

    def get_agent_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state of all agents"""
        return {
            agent_id: agent.get_state()
            for agent_id, agent in self.agents.items()
        }

    def mark_complete(self) -> None:
        """Mark conversation as complete"""
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "agents": list(self.agents.keys()),
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (self.completed_at - self.created_at).total_seconds() if self.completed_at else None
        }


class WorkflowOrchestrator:
    """Orchestrates multi-agent workflows"""

    def __init__(self, workflow_id: str, workflow_type: str):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.conversation = ConversationManager(workflow_id)
        self.initial_request: Optional[Dict[str, Any]] = None
        self.final_result: Optional[Dict[str, Any]] = None
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None

    def set_initial_request(self, request: Dict[str, Any]) -> None:
        """Set initial request for workflow"""
        self.initial_request = request

    def set_final_result(self, result: Dict[str, Any]) -> None:
        """Set final result after workflow completion"""
        self.final_result = result
        self.completed_at = datetime.utcnow()

    def add_agent(self, agent: BaseAgent) -> None:
        """Add agent to workflow"""
        self.conversation.add_agent(agent)

    def record_message(self, message: AgentMessage) -> None:
        """Record message in workflow"""
        self.conversation.record_message(message)

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status"""
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.created_at).total_seconds()
        elif self.created_at:
            duration = (datetime.utcnow() - self.created_at).total_seconds()

        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": "completed" if self.completed_at else "running",
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "agent_count": len(self.conversation.agents),
            "message_count": len(self.conversation.messages),
            "error_message": self.error_message
        }

    def get_results(self) -> Dict[str, Any]:
        """Get workflow results"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "initial_request": self.initial_request,
            "final_result": self.final_result,
            "agent_states": self.conversation.get_agent_states(),
            "conversation_history": self.conversation.get_conversation_history(),
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


logger.info("Agent definitions module loaded")
