#!/usr/bin/env python3
"""
Phase 8.6: Agent Orchestration Service
Manages workflows between multiple agents
"""

from typing import Dict, List, Optional, Any
import logging
import uuid
from datetime import datetime
import json

from api.agents.agent_definitions import (
    WorkflowOrchestrator, AgentMessage, MessageType, AgentStatus
)
from api.agents.phase8_agents import (
    FineTuningOrchestrator, LoadTestAnalyzer,
    PerformanceAdvisor, CodeReviewerAgent
)

logger = logging.getLogger(__name__)


class AgentOrchestrationService:
    """Orchestrates multi-agent workflows"""

    def __init__(self):
        self.workflows: Dict[str, WorkflowOrchestrator] = {}
        self.agent_classes = {
            "fine_tuning_orchestrator": FineTuningOrchestrator,
            "load_test_analyzer": LoadTestAnalyzer,
            "performance_advisor": PerformanceAdvisor,
            "code_reviewer": CodeReviewerAgent
        }

    def create_workflow(self, workflow_type: str, request: Dict[str, Any]) -> WorkflowOrchestrator:
        """Create a new workflow"""
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        workflow = WorkflowOrchestrator(workflow_id, workflow_type)
        workflow.set_initial_request(request)

        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow {workflow_id} of type {workflow_type}")

        return workflow

    async def execute_fine_tuning_workflow(self, request: Dict[str, Any]) -> WorkflowOrchestrator:
        """Execute fine-tuning workflow"""
        workflow = self.create_workflow("fine_tuning", request)

        # Create agents
        fine_tuning_agent = FineTuningOrchestrator()
        code_reviewer = CodeReviewerAgent()

        workflow.add_agent(fine_tuning_agent)
        workflow.add_agent(code_reviewer)

        try:
            # Step 1: List available models
            logger.info(f"[{workflow.workflow_id}] Step 1: Listing available models")
            models_result = await fine_tuning_agent.act("list_available_models", {})

            initial_message = AgentMessage(
                agent_id=fine_tuning_agent.agent_id,
                agent_name=fine_tuning_agent.name,
                message_type=MessageType.ANALYSIS,
                content=f"Available models analyzed. Total: {models_result.get('total_count', 0)}",
                metadata={"tool": "list_available_models", "result": models_result}
            )
            workflow.record_message(initial_message)

            # Step 2: Prepare dataset
            logger.info(f"[{workflow.workflow_id}] Step 2: Preparing training dataset")
            task_type = request.get("task_type", "bug_detection")
            dataset_result = await fine_tuning_agent.act(
                "prepare_training_dataset",
                {"task_type": task_type}
            )

            dataset_message = AgentMessage(
                agent_id=fine_tuning_agent.agent_id,
                agent_name=fine_tuning_agent.name,
                message_type=MessageType.ANALYSIS,
                content=f"Training dataset prepared for {task_type}",
                metadata={"tool": "prepare_training_dataset", "result": dataset_result}
            )
            workflow.record_message(dataset_message)

            # Step 3: Start fine-tuning
            logger.info(f"[{workflow.workflow_id}] Step 3: Starting fine-tuning job")
            model_name = request.get("model", "gpt-3.5-turbo")
            ft_params = request.get("parameters", {})

            ft_result = await fine_tuning_agent.act(
                "start_fine_tuning",
                {
                    "model": model_name,
                    "dataset": task_type,
                    "params": ft_params
                }
            )

            ft_message = AgentMessage(
                agent_id=fine_tuning_agent.agent_id,
                agent_name=fine_tuning_agent.name,
                message_type=MessageType.RECOMMENDATION,
                content=f"Fine-tuning job started: {ft_result.get('job_id')}",
                metadata={"tool": "start_fine_tuning", "result": ft_result}
            )
            workflow.record_message(ft_message)

            # Step 4: Review training code (Code Reviewer Agent)
            logger.info(f"[{workflow.workflow_id}] Step 4: Code review of training implementation")
            training_code_snippet = f"""
# Training job configuration for {model_name}
job_config = {{
    'learning_rate': {ft_params.get('learning_rate', 2e-5)},
    'batch_size': {ft_params.get('batch_size', 32)},
    'num_epochs': {ft_params.get('num_epochs', 3)},
    'dataset_size': {dataset_result.get('dataset', {}).get('size', 0)}
}}
"""
            code_review = await code_reviewer.act(
                "review_code",
                {"code_snippet": training_code_snippet}
            )

            review_message = AgentMessage(
                agent_id=code_reviewer.agent_id,
                agent_name=code_reviewer.name,
                message_type=MessageType.ANALYSIS,
                content=f"Code review completed. Quality score: {code_review.get('quality_score', 0)}",
                metadata={"tool": "review_code", "result": code_review}
            )
            workflow.record_message(review_message)

            # Step 5: Validate model (simulated)
            logger.info(f"[{workflow.workflow_id}] Step 5: Validating fine-tuned model")
            model_id = ft_result.get("job_id")
            validation_result = await fine_tuning_agent.act(
                "validate_model",
                {"model_id": model_id}
            )

            validation_message = AgentMessage(
                agent_id=fine_tuning_agent.agent_id,
                agent_name=fine_tuning_agent.name,
                message_type=MessageType.ANALYSIS,
                content=f"Model validation complete. Ready for deployment: {validation_result.get('recommended_for_deployment', False)}",
                metadata={"tool": "validate_model", "result": validation_result}
            )
            workflow.record_message(validation_message)

            # Step 6: Deploy model
            logger.info(f"[{workflow.workflow_id}] Step 6: Deploying fine-tuned model")
            deployment_result = await fine_tuning_agent.act(
                "deploy_model",
                {"model_id": model_id}
            )

            deployment_message = AgentMessage(
                agent_id=fine_tuning_agent.agent_id,
                agent_name=fine_tuning_agent.name,
                message_type=MessageType.DECISION,
                content=f"Model deployment initiated. Status: {deployment_result.get('deployment_status')}",
                metadata={"tool": "deploy_model", "result": deployment_result}
            )
            workflow.record_message(deployment_message)

            # Final result
            final_result = {
                "workflow_type": "fine_tuning",
                "status": "completed",
                "model_id": model_id,
                "job_id": ft_result.get("job_id"),
                "deployment_status": deployment_result.get("deployment_status"),
                "endpoint": deployment_result.get("endpoint"),
                "validation": validation_result,
                "code_review": code_review
            }

            workflow.set_final_result(final_result)
            logger.info(f"[{workflow.workflow_id}] Workflow completed successfully")

        except Exception as e:
            logger.error(f"[{workflow.workflow_id}] Workflow error: {str(e)}")
            workflow.error_message = str(e)

        return workflow

    async def execute_optimization_workflow(self, request: Dict[str, Any]) -> WorkflowOrchestrator:
        """Execute performance optimization workflow"""
        workflow = self.create_workflow("optimization", request)

        # Create agents
        analyzer = LoadTestAnalyzer()
        advisor = PerformanceAdvisor()
        reviewer = CodeReviewerAgent()

        workflow.add_agent(analyzer)
        workflow.add_agent(advisor)
        workflow.add_agent(reviewer)

        try:
            # Step 1: Get load test results
            logger.info(f"[{workflow.workflow_id}] Step 1: Retrieving load test results")
            test_id = request.get("load_test_id", "lt_latest")
            test_results = await analyzer.act(
                "get_load_test_results",
                {"test_id": test_id}
            )

            analyzer_msg1 = AgentMessage(
                agent_id=analyzer.agent_id,
                agent_name=analyzer.name,
                message_type=MessageType.ANALYSIS,
                content=f"Load test results retrieved: {test_results.get('status')}",
                metadata={"tool": "get_load_test_results", "result": test_results}
            )
            workflow.record_message(analyzer_msg1)

            # Step 2: Analyze latency
            logger.info(f"[{workflow.workflow_id}] Step 2: Analyzing latency patterns")
            latency_analysis = await analyzer.act(
                "analyze_latency",
                {"metrics": test_results.get("metrics", {})}
            )

            analyzer_msg2 = AgentMessage(
                agent_id=analyzer.agent_id,
                agent_name=analyzer.name,
                message_type=MessageType.ANALYSIS,
                content="Latency analysis completed",
                metadata={"tool": "analyze_latency", "result": latency_analysis}
            )
            workflow.record_message(analyzer_msg2)

            # Step 3: Identify bottlenecks
            logger.info(f"[{workflow.workflow_id}] Step 3: Identifying bottlenecks")
            bottleneck_analysis = await analyzer.act(
                "identify_bottlenecks",
                {"metrics": test_results}
            )

            analyzer_msg3 = AgentMessage(
                agent_id=analyzer.agent_id,
                agent_name=analyzer.name,
                message_type=MessageType.ANALYSIS,
                content=f"Identified {bottleneck_analysis.get('total_bottlenecks', 0)} bottlenecks",
                metadata={"tool": "identify_bottlenecks", "result": bottleneck_analysis}
            )
            workflow.record_message(analyzer_msg3)

            # Step 4: Generate report
            logger.info(f"[{workflow.workflow_id}] Step 4: Generating analysis report")
            report = await analyzer.act(
                "generate_report",
                {"analysis": {
                    "latency": latency_analysis,
                    "bottlenecks": bottleneck_analysis
                }}
            )

            analyzer_msg4 = AgentMessage(
                agent_id=analyzer.agent_id,
                agent_name=analyzer.name,
                message_type=MessageType.RECOMMENDATION,
                content=f"Analysis report generated",
                metadata={"tool": "generate_report", "result": report}
            )
            workflow.record_message(analyzer_msg4)

            # Step 5: Get optimization recommendations
            logger.info(f"[{workflow.workflow_id}] Step 5: Generating optimization recommendations")

            # Cache strategy
            cache_recommendation = await advisor.act(
                "analyze_cache_strategy",
                {"queries": ["SELECT * FROM conversations", "SELECT * FROM messages"]}
            )

            advisor_msg1 = AgentMessage(
                agent_id=advisor.agent_id,
                agent_name=advisor.name,
                message_type=MessageType.RECOMMENDATION,
                content="Cache strategy recommendation provided",
                metadata={"tool": "analyze_cache_strategy", "result": cache_recommendation}
            )
            workflow.record_message(advisor_msg1)

            # Index suggestions
            index_recommendation = await advisor.act(
                "suggest_indexes",
                {"slow_queries": bottleneck_analysis.get("bottlenecks", [])}
            )

            advisor_msg2 = AgentMessage(
                agent_id=advisor.agent_id,
                agent_name=advisor.name,
                message_type=MessageType.RECOMMENDATION,
                content="Index recommendations provided",
                metadata={"tool": "suggest_indexes", "result": index_recommendation}
            )
            workflow.record_message(advisor_msg2)

            # Step 6: Code review of optimization code
            logger.info(f"[{workflow.workflow_id}] Step 6: Reviewing optimization implementation")
            optimization_code = """
# Cache strategy implementation
class OptimizationMiddleware:
    async def apply_caching(self, request, endpoint):
        cache_key = f"{endpoint}:{request.user_id}"
        if cached := await cache.get(cache_key):
            return cached

        result = await endpoint(request)
        await cache.set(cache_key, result, ttl=300)
        return result
"""

            code_review = await reviewer.act(
                "review_code",
                {"code_snippet": optimization_code}
            )

            reviewer_msg = AgentMessage(
                agent_id=reviewer.agent_id,
                agent_name=reviewer.name,
                message_type=MessageType.ANALYSIS,
                content="Code review complete",
                metadata={"tool": "review_code", "result": code_review}
            )
            workflow.record_message(reviewer_msg)

            # Final result
            final_result = {
                "workflow_type": "optimization",
                "status": "completed",
                "analysis": {
                    "latency": latency_analysis,
                    "bottlenecks": bottleneck_analysis
                },
                "recommendations": {
                    "caching": cache_recommendation,
                    "indexing": index_recommendation
                },
                "report": report,
                "code_review": code_review,
                "priority_actions": [
                    "Implement Redis caching for chat endpoints",
                    "Create composite indexes on frequently joined columns",
                    "Implement circuit breaker for external API calls"
                ]
            }

            workflow.set_final_result(final_result)
            logger.info(f"[{workflow.workflow_id}] Optimization workflow completed successfully")

        except Exception as e:
            logger.error(f"[{workflow.workflow_id}] Workflow error: {str(e)}")
            workflow.error_message = str(e)

        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowOrchestrator]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
        return workflow.get_status()

    def get_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow results"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}
        return workflow.get_results()

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "type": wf.workflow_type,
                "status": "completed" if wf.completed_at else "running",
                "created_at": wf.created_at.isoformat(),
                "agent_count": len(wf.conversation.agents),
                "message_count": len(wf.conversation.messages)
            }
            for wf in self.workflows.values()
        ]

    def clear_old_workflows(self, hours: int = 24) -> int:
        """Clear workflows older than specified hours"""
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        count = 0

        workflow_ids_to_remove = []
        for workflow_id, workflow in self.workflows.items():
            if workflow.created_at < cutoff_time:
                workflow_ids_to_remove.append(workflow_id)
                count += 1

        for workflow_id in workflow_ids_to_remove:
            del self.workflows[workflow_id]

        logger.info(f"Cleared {count} old workflows")
        return count


# Global instance
agent_orchestration_service = AgentOrchestrationService()

logger.info("Agent Orchestration Service initialized")
