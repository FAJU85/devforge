#!/usr/bin/env python3
"""
Tests for agent definitions and core classes
"""

import pytest
from datetime import datetime
from api.agents.agent_definitions import (
    BaseAgent, AgentRole, AgentStatus, MessageType,
    AgentMessage, AgentState, ToolDefinition,
    ConversationManager, WorkflowOrchestrator
)


class TestToolDefinition:
    """Test ToolDefinition class"""

    def test_tool_definition_creation(self):
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            requires_approval=False,
            timeout_seconds=30
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.requires_approval is False

    def test_tool_definition_to_dict(self):
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            output_schema={"type": "object"}
        )
        tool_dict = tool.to_dict()
        assert "name" in tool_dict
        assert "description" in tool_dict
        assert tool_dict["timeout_seconds"] == 30


class TestAgentMessage:
    """Test AgentMessage class"""

    def test_message_creation(self):
        msg = AgentMessage(
            agent_id="agent1",
            agent_name="TestAgent",
            message_type=MessageType.ANALYSIS,
            content="Test analysis"
        )
        assert msg.agent_id == "agent1"
        assert msg.agent_name == "TestAgent"
        assert msg.message_type == MessageType.ANALYSIS

    def test_message_to_dict(self):
        msg = AgentMessage(
            agent_id="agent1",
            agent_name="TestAgent",
            message_type=MessageType.ANALYSIS,
            content="Test analysis",
            metadata={"key": "value"}
        )
        msg_dict = msg.to_dict()
        assert msg_dict["agent_id"] == "agent1"
        assert msg_dict["message_type"] == "analysis"
        assert msg_dict["metadata"]["key"] == "value"


class TestAgentState:
    """Test AgentState class"""

    def test_agent_state_creation(self):
        state = AgentState(
            agent_id="agent1",
            agent_name="TestAgent",
            role=AgentRole.ANALYZER
        )
        assert state.agent_id == "agent1"
        assert state.role == AgentRole.ANALYZER
        assert state.status == AgentStatus.IDLE

    def test_agent_state_to_dict(self):
        state = AgentState(
            agent_id="agent1",
            agent_name="TestAgent",
            role=AgentRole.ANALYZER,
            status=AgentStatus.ACTING,
            current_task="analyzing data"
        )
        state_dict = state.to_dict()
        assert state_dict["status"] == "acting"
        assert state_dict["current_task"] == "analyzing data"


class TestBaseAgent:
    """Test BaseAgent class"""

    def test_base_agent_creation(self):
        tools = [
            ToolDefinition(
                name="tool1",
                description="Test tool",
                input_schema={},
                output_schema={}
            )
        ]
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=tools,
            system_prompt="Test prompt"
        )
        assert agent.agent_id == "agent1"
        assert agent.name == "TestAgent"
        assert len(agent.tools) == 1

    def test_add_message(self):
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=[],
            system_prompt="Test prompt"
        )
        msg = AgentMessage(
            agent_id="agent1",
            agent_name="TestAgent",
            message_type=MessageType.RESPONSE,
            content="Test message"
        )
        agent.add_message(msg)
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0].content == "Test message"

    def test_update_status(self):
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=[],
            system_prompt="Test prompt"
        )
        agent.update_status(AgentStatus.THINKING, "analyzing")
        assert agent.state.status == AgentStatus.THINKING
        assert agent.state.current_task == "analyzing"

    def test_get_tools(self):
        tools = [
            ToolDefinition(
                name="tool1",
                description="Tool 1",
                input_schema={},
                output_schema={}
            ),
            ToolDefinition(
                name="tool2",
                description="Tool 2",
                input_schema={},
                output_schema={}
            )
        ]
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=tools,
            system_prompt="Test prompt"
        )
        agent_tools = agent.get_tools()
        assert len(agent_tools) == 2
        assert agent_tools[0]["name"] == "tool1"
        assert agent_tools[1]["name"] == "tool2"


class TestConversationManager:
    """Test ConversationManager class"""

    def test_conversation_creation(self):
        conv = ConversationManager("workflow1")
        assert conv.workflow_id == "workflow1"
        assert len(conv.agents) == 0
        assert len(conv.messages) == 0

    def test_add_agent(self):
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=[],
            system_prompt="Test prompt"
        )
        conv = ConversationManager("workflow1")
        conv.add_agent(agent)
        assert len(conv.agents) == 1
        assert "agent1" in conv.agents

    def test_record_message(self):
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=[],
            system_prompt="Test prompt"
        )
        conv = ConversationManager("workflow1")
        conv.add_agent(agent)

        msg = AgentMessage(
            agent_id="agent1",
            agent_name="TestAgent",
            message_type=MessageType.ANALYSIS,
            content="Test message"
        )
        conv.record_message(msg)
        assert len(conv.messages) == 1
        assert len(agent.conversation_history) == 1

    def test_get_conversation_history(self):
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=[],
            system_prompt="Test prompt"
        )
        conv = ConversationManager("workflow1")
        conv.add_agent(agent)

        msg1 = AgentMessage(
            agent_id="agent1",
            agent_name="TestAgent",
            message_type=MessageType.ANALYSIS,
            content="Message 1"
        )
        msg2 = AgentMessage(
            agent_id="agent1",
            agent_name="TestAgent",
            message_type=MessageType.RESPONSE,
            content="Message 2"
        )
        conv.record_message(msg1)
        conv.record_message(msg2)

        history = conv.get_conversation_history()
        assert len(history) == 2
        assert history[0]["content"] == "Message 1"
        assert history[1]["content"] == "Message 2"


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator class"""

    def test_workflow_creation(self):
        workflow = WorkflowOrchestrator("wf1", "fine_tuning")
        assert workflow.workflow_id == "wf1"
        assert workflow.workflow_type == "fine_tuning"
        assert workflow.created_at is not None

    def test_set_initial_request(self):
        workflow = WorkflowOrchestrator("wf1", "fine_tuning")
        request = {"task_type": "bug_detection", "model": "gpt-3.5"}
        workflow.set_initial_request(request)
        assert workflow.initial_request == request

    def test_set_final_result(self):
        workflow = WorkflowOrchestrator("wf1", "fine_tuning")
        result = {"status": "completed", "job_id": "ft_123"}
        workflow.set_final_result(result)
        assert workflow.final_result == result
        assert workflow.completed_at is not None

    def test_add_agent(self):
        agent = BaseAgent(
            agent_id="agent1",
            name="TestAgent",
            role=AgentRole.ANALYZER,
            description="A test agent",
            tools=[],
            system_prompt="Test prompt"
        )
        workflow = WorkflowOrchestrator("wf1", "fine_tuning")
        workflow.add_agent(agent)
        assert len(workflow.conversation.agents) == 1

    def test_get_status(self):
        workflow = WorkflowOrchestrator("wf1", "fine_tuning")
        workflow.set_initial_request({"task": "test"})
        status = workflow.get_status()
        assert status["workflow_id"] == "wf1"
        assert status["workflow_type"] == "fine_tuning"
        assert status["status"] == "running"

    def test_get_results(self):
        workflow = WorkflowOrchestrator("wf1", "fine_tuning")
        workflow.set_initial_request({"task": "test"})
        workflow.set_final_result({"completed": True})
        results = workflow.get_results()
        assert results["workflow_id"] == "wf1"
        assert results["initial_request"]["task"] == "test"
        assert results["final_result"]["completed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
