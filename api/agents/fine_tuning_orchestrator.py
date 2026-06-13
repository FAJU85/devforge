#!/usr/bin/env python3
"""
FineTuningOrchestrator Agent - Phase 8.6.1
Coordinates model fine-tuning with intelligent decision-making
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .tools import FineTuningTools

logger = logging.getLogger(__name__)


class FineTuningOrchestrator:
    """
    Orchestrates fine-tuning workflows including:
    - Model selection
    - Dataset preparation
    - Training execution
    - Validation
    - Deployment
    """

    def __init__(self):
        self.tools = FineTuningTools()
        self.logger = logger
        self.conversation_history: List[Dict[str, str]] = []
        self.workflow_id: Optional[str] = None

    async def select_best_model(self, task_type: str, constraints: Dict[str, Any]) -> str:
        """Select best model for task"""
        try:
            self.logger.info(f"Selecting model for task: {task_type}")

            models_response = await self.tools.list_available_models()
            models = models_response.models

            # Score models based on constraints
            best_score = -1
            best_model = None

            for model in models:
                if not model.get("supports_fine_tuning", False):
                    continue

                score = 100
                model_name = model["name"]

                # Cost considerations
                max_cost = constraints.get("max_cost_per_token", 0.03)
                if model.get("cost_per_1k_tokens", 0) > max_cost:
                    score -= 20

                # Token limit considerations
                required_tokens = constraints.get("min_token_capacity", 4096)
                if model.get("max_tokens", 0) < required_tokens:
                    score -= 30

                if score > best_score:
                    best_score = score
                    best_model = model_name

            if not best_model:
                raise ValueError("No suitable models found for task")

            self.logger.info(f"Selected model: {best_model}")
            self._add_to_history("assistant", f"Selected {best_model} for {task_type}")

            return best_model

        except Exception as e:
            self.logger.error(f"Error selecting model: {e}")
            self._add_to_history("assistant", f"Error selecting model: {str(e)}")
            raise

    async def prepare_dataset(self, task_type: str, config: Dict[str, Any]) -> str:
        """Prepare training dataset"""
        try:
            self.logger.info(f"Preparing dataset for task: {task_type}")

            response = await self.tools.prepare_training_dataset(task_type)

            self._add_to_history(
                "assistant",
                f"Prepared dataset {response.dataset_id} with {response.size} samples"
            )

            return response.dataset_id

        except Exception as e:
            self.logger.error(f"Error preparing dataset: {e}")
            self._add_to_history("assistant", f"Error preparing dataset: {str(e)}")
            raise

    async def start_training(
        self,
        model: str,
        dataset_id: str,
        training_params: Dict[str, Any]
    ) -> str:
        """Start fine-tuning job"""
        try:
            self.logger.info(f"Starting fine-tuning for {model}")

            learning_rate = training_params.get("learning_rate", 0.0001)
            epochs = training_params.get("epochs", 3)

            response = await self.tools.start_fine_tuning(
                model=model,
                dataset_id=dataset_id,
                learning_rate=learning_rate,
                epochs=epochs
            )

            self._add_to_history(
                "assistant",
                f"Started fine-tuning job {response.job_id} with LR={learning_rate}, epochs={epochs}"
            )

            return response.job_id

        except Exception as e:
            self.logger.error(f"Error starting training: {e}")
            self._add_to_history("assistant", f"Error starting training: {str(e)}")
            raise

    async def validate_model(self, model_id: str) -> bool:
        """Validate fine-tuned model"""
        try:
            self.logger.info(f"Validating model: {model_id}")

            response = await self.tools.validate_model(model_id)

            message = (
                f"Model validation completed - Accuracy: {response.accuracy:.2%}, "
                f"Loss: {response.loss:.4f}, Passed: {response.passed}"
            )
            self._add_to_history("assistant", message)

            return response.passed

        except Exception as e:
            self.logger.error(f"Error validating model: {e}")
            self._add_to_history("assistant", f"Error validating model: {str(e)}")
            raise

    async def deploy_model(self, model_id: str) -> Dict[str, Any]:
        """Deploy validated model"""
        try:
            self.logger.info(f"Deploying model: {model_id}")

            response = await self.tools.deploy_model(model_id)

            self._add_to_history(
                "assistant",
                f"Model {model_id} deployed successfully to {response['endpoint']}"
            )

            return response

        except Exception as e:
            self.logger.error(f"Error deploying model: {e}")
            self._add_to_history("assistant", f"Error deploying model: {str(e)}")
            raise

    async def execute_workflow(
        self,
        task_type: str,
        models: Optional[List[str]] = None,
        dataset_size: int = 10000,
        training_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute complete fine-tuning workflow"""
        try:
            self.workflow_id = f"ft_workflow_{datetime.utcnow().timestamp()}"
            self.logger.info(f"Starting fine-tuning workflow: {self.workflow_id}")

            self._add_to_history("user", f"Execute fine-tuning workflow for {task_type}")

            # Step 1: Select model
            constraints = {
                "max_cost_per_token": 0.03,
                "min_token_capacity": 4096
            }
            selected_model = await self.select_best_model(task_type, constraints)

            # Step 2: Prepare dataset
            dataset_id = await self.prepare_dataset(task_type, {"size": dataset_size})

            # Step 3: Start training
            if training_params is None:
                training_params = {
                    "learning_rate": 0.0001,
                    "epochs": 3,
                    "batch_size": 32
                }

            job_id = await self.start_training(selected_model, dataset_id, training_params)

            # Step 4: Validate
            model_valid = await self.validate_model(job_id)

            if not model_valid:
                raise ValueError("Model validation failed")

            # Step 5: Deploy
            deployment_info = await self.deploy_model(job_id)

            result = {
                "workflow_id": self.workflow_id,
                "status": "completed",
                "model": selected_model,
                "dataset_id": dataset_id,
                "job_id": job_id,
                "deployment": deployment_info,
                "conversation_history": self.conversation_history
            }

            self.logger.info(f"Workflow {self.workflow_id} completed successfully")

            return result

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow_id": self.workflow_id,
                "status": "failed",
                "error": str(e),
                "conversation_history": self.conversation_history
            }

    def _add_to_history(self, role: str, message: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get full conversation history"""
        return self.conversation_history

    def reset(self):
        """Reset agent state"""
        self.conversation_history = []
        self.workflow_id = None
