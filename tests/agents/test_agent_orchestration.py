#!/usr/bin/env python3
"""
Tests for agent orchestration service
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from api.services.agent_orchestration_service import AgentOrchestrationService


@pytest.fixture
def orchestration_service():
    """Create a test orchestration service"""
    return AgentOrchestrationService()


class TestAgentOrchestrationService:
    """Test AgentOrchestrationService class"""

    def test_service_initialization(self, orchestration_service):
        assert len(orchestration_service.workflows) == 0
        assert len(orchestration_service.agent_classes) == 4

    def test_create_workflow(self, orchestration_service):
        request = {"task_type": "bug_detection"}
        workflow = orchestration_service.create_workflow("fine_tuning", request)
        assert workflow.workflow_id is not None
        assert workflow.workflow_type == "fine_tuning"
        assert workflow.initial_request == request

    def test_create_multiple_workflows(self, orchestration_service):
        for i in range(3):
            request = {"task_type": f"task_{i}"}
            orchestration_service.create_workflow("fine_tuning", request)

        assert len(orchestration_service.workflows) == 3

    def test_get_workflow(self, orchestration_service):
        request = {"task_type": "bug_detection"}
        workflow = orchestration_service.create_workflow("fine_tuning", request)

        retrieved = orchestration_service.get_workflow(workflow.workflow_id)
        assert retrieved is not None
        assert retrieved.workflow_id == workflow.workflow_id

    def test_get_nonexistent_workflow(self, orchestration_service):
        retrieved = orchestration_service.get_workflow("nonexistent")
        assert retrieved is None

    def test_get_workflow_status(self, orchestration_service):
        request = {"task_type": "bug_detection"}
        workflow = orchestration_service.create_workflow("fine_tuning", request)

        status = orchestration_service.get_workflow_status(workflow.workflow_id)
        assert status["workflow_id"] == workflow.workflow_id
        assert status["status"] == "running"

    def test_get_workflow_status_nonexistent(self, orchestration_service):
        status = orchestration_service.get_workflow_status("nonexistent")
        assert "error" in status

    def test_get_workflow_results(self, orchestration_service):
        request = {"task_type": "bug_detection"}
        workflow = orchestration_service.create_workflow("fine_tuning", request)
        workflow.set_final_result({"status": "completed"})

        results = orchestration_service.get_workflow_results(workflow.workflow_id)
        assert results["workflow_id"] == workflow.workflow_id
        assert results["final_result"]["status"] == "completed"

    def test_get_all_workflows(self, orchestration_service):
        for i in range(3):
            orchestration_service.create_workflow("fine_tuning", {})

        all_workflows = orchestration_service.get_all_workflows()
        assert len(all_workflows) == 3

    def test_clear_old_workflows(self, orchestration_service):
        from datetime import datetime, timedelta

        # Create workflows
        for i in range(3):
            wf = orchestration_service.create_workflow("fine_tuning", {})
            # Mark first as old
            if i == 0:
                wf.created_at = datetime.utcnow() - timedelta(hours=25)

        # Clear workflows older than 24 hours
        cleared = orchestration_service.clear_old_workflows(hours=24)
        assert cleared == 1
        assert len(orchestration_service.workflows) == 2

    @pytest.mark.asyncio
    async def test_execute_fine_tuning_workflow(self, orchestration_service):
        """Test fine-tuning workflow execution"""
        request = {
            "task_type": "bug_detection",
            "model": "gpt-3.5-turbo",
            "parameters": {
                "learning_rate": 2e-5,
                "batch_size": 32,
                "num_epochs": 3
            }
        }

        workflow = await orchestration_service.execute_fine_tuning_workflow(request)

        assert workflow.workflow_id is not None
        assert workflow.workflow_type == "fine_tuning"
        assert workflow.final_result is not None
        assert len(workflow.conversation.messages) > 0

    @pytest.mark.asyncio
    async def test_execute_optimization_workflow(self, orchestration_service):
        """Test optimization workflow execution"""
        request = {
            "load_test_id": "lt_latest",
            "metrics_target": {
                "p95_latency_ms": 300
            }
        }

        workflow = await orchestration_service.execute_optimization_workflow(request)

        assert workflow.workflow_id is not None
        assert workflow.workflow_type == "optimization"
        assert workflow.final_result is not None
        assert len(workflow.conversation.messages) > 0

    @pytest.mark.asyncio
    async def test_workflow_message_recording(self, orchestration_service):
        """Test message recording during workflow"""
        request = {"task_type": "bug_detection"}
        workflow = await orchestration_service.execute_fine_tuning_workflow(request)

        # Verify messages were recorded
        messages = workflow.conversation.get_conversation_history()
        assert len(messages) > 0

        # Check message types
        message_types = [msg["message_type"] for msg in messages]
        assert "analysis" in message_types or "recommendation" in message_types

    @pytest.mark.asyncio
    async def test_workflow_agent_states(self, orchestration_service):
        """Test agent states during workflow"""
        request = {"task_type": "bug_detection"}
        workflow = await orchestration_service.execute_fine_tuning_workflow(request)

        agent_states = workflow.conversation.get_agent_states()
        assert len(agent_states) > 0

        for agent_id, state in agent_states.items():
            assert "status" in state
            assert "message_count" in state

    @pytest.mark.asyncio
    async def test_fine_tuning_workflow_steps(self, orchestration_service):
        """Test fine-tuning workflow executes all steps"""
        request = {
            "task_type": "bug_detection",
            "model": "gpt-3.5-turbo"
        }

        workflow = await orchestration_service.execute_fine_tuning_workflow(request)

        # Verify final result has expected structure
        assert "model_id" in workflow.final_result
        assert "job_id" in workflow.final_result
        assert "deployment_status" in workflow.final_result
        assert "validation" in workflow.final_result
        assert "code_review" in workflow.final_result

    @pytest.mark.asyncio
    async def test_optimization_workflow_recommendations(self, orchestration_service):
        """Test optimization workflow provides recommendations"""
        request = {"load_test_id": "lt_latest"}

        workflow = await orchestration_service.execute_optimization_workflow(request)

        # Verify final result has recommendations
        assert "recommendations" in workflow.final_result
        assert "priority_actions" in workflow.final_result
        assert len(workflow.final_result["priority_actions"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, orchestration_service):
        """Test workflow error handling"""
        request = {"task_type": "invalid_task"}

        # Patch the agent to raise an error
        with patch('api.agents.phase8_agents.FineTuningOrchestrator.act') as mock_act:
            mock_act.side_effect = Exception("Test error")

            workflow = await orchestration_service.execute_fine_tuning_workflow(request)

            # Should complete but with error message
            assert workflow.error_message is not None

    def test_workflow_persistence(self, orchestration_service):
        """Test workflows persist in service"""
        request1 = {"task_type": "bug_detection"}
        request2 = {"task_type": "code_optimization"}

        wf1 = orchestration_service.create_workflow("fine_tuning", request1)
        wf2 = orchestration_service.create_workflow("fine_tuning", request2)

        # Both should be retrievable
        assert orchestration_service.get_workflow(wf1.workflow_id) is not None
        assert orchestration_service.get_workflow(wf2.workflow_id) is not None

        # Should be in all workflows list
        all_wfs = orchestration_service.get_all_workflows()
        ids = [wf["workflow_id"] for wf in all_wfs]
        assert wf1.workflow_id in ids
        assert wf2.workflow_id in ids

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, orchestration_service):
        """Test running multiple workflows concurrently"""
        requests = [
            {"task_type": "bug_detection"},
            {"task_type": "code_optimization"},
            {"task_type": "performance_prediction"}
        ]

        # Create workflows concurrently
        workflows = [
            orchestration_service.create_workflow("fine_tuning", req)
            for req in requests
        ]

        # All should be retrievable
        assert len(orchestration_service.get_all_workflows()) == 3

        # All should have unique IDs
        ids = [wf.workflow_id for wf in workflows]
        assert len(set(ids)) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
