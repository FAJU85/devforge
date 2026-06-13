"""Canary deployment configuration and monitoring setup."""

import os
from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class RolloutStage(Enum):
    """Canary rollout stages."""
    PHASE_1 = 0      # Feature flag off, DB disabled
    CANARY_10 = 10   # Internal staff + early adopters
    EARLY_ADOPTERS = 25
    HALF_ROLLOUT = 50
    MOST_USERS = 75
    FULL_ROLLOUT = 100


@dataclass
class CanaryStageConfig:
    """Configuration for a canary rollout stage."""
    stage: RolloutStage
    week: int
    rollout_percentage: int
    target_users: str
    metrics_targets: Dict[str, float]
    monitoring_intensity: str  # "basic", "moderate", "intensive"
    rollback_trigger: str

    def is_healthy(self, metrics: Dict[str, float]) -> bool:
        """Check if metrics are within acceptable ranges."""
        for metric_name, target_value in self.metrics_targets.items():
            actual = metrics.get(metric_name, 0)
            # For error rates, lower is better
            if "error_rate" in metric_name:
                if actual > target_value:
                    return False
            # For latency, lower is better
            elif "latency" in metric_name:
                if actual > target_value:
                    return False
            # For success, higher is better
            elif "success" in metric_name:
                if actual < target_value:
                    return False
        return True


# Canary rollout stages configuration
CANARY_STAGES: List[CanaryStageConfig] = [
    CanaryStageConfig(
        stage=RolloutStage.PHASE_1,
        week=1,
        rollout_percentage=0,
        target_users="None (feature flag off)",
        metrics_targets={
            "api_latency_p95_ms": 200,  # Should be low, minimal load
            "error_rate_percent": 0.5,
            "db_sync_success_percent": 100,  # Not used
        },
        monitoring_intensity="basic",
        rollback_trigger="Any critical error (unlikely)",
    ),
    CanaryStageConfig(
        stage=RolloutStage.CANARY_10,
        week=2,
        rollout_percentage=10,
        target_users="Internal staff (devs, designers) + early adopters",
        metrics_targets={
            "api_latency_p95_ms": 150,
            "error_rate_percent": 0.1,
            "db_connection_pool_utilization_percent": 60,
            "data_consistency_match_percent": 99.9,
            "message_count_db_vs_localStorage_mismatch_percent": 0.1,
        },
        monitoring_intensity="intensive",
        rollback_trigger="Error rate > 1%, latency > 500ms, data loss detected",
    ),
    CanaryStageConfig(
        stage=RolloutStage.EARLY_ADOPTERS,
        week=3,
        rollout_percentage=25,
        target_users="Early adopters, tech-savvy users",
        metrics_targets={
            "api_latency_p95_ms": 150,
            "error_rate_percent": 0.15,
            "db_connection_pool_utilization_percent": 70,
            "data_consistency_match_percent": 99.8,
        },
        monitoring_intensity="moderate",
        rollback_trigger="Error rate > 1.5%, data loss > 0.5%",
    ),
    CanaryStageConfig(
        stage=RolloutStage.HALF_ROLLOUT,
        week=4,
        rollout_percentage=50,
        target_users="Half of all users",
        metrics_targets={
            "api_latency_p95_ms": 200,
            "error_rate_percent": 0.2,
            "db_connection_pool_utilization_percent": 80,
            "data_consistency_match_percent": 99.5,
        },
        monitoring_intensity="moderate",
        rollback_trigger="Error rate > 2%, data loss > 1%",
    ),
    CanaryStageConfig(
        stage=RolloutStage.MOST_USERS,
        week=5,
        rollout_percentage=75,
        target_users="Most users (except very conservative users)",
        metrics_targets={
            "api_latency_p95_ms": 250,
            "error_rate_percent": 0.25,
            "db_connection_pool_utilization_percent": 85,
            "data_consistency_match_percent": 99.0,
        },
        monitoring_intensity="moderate",
        rollback_trigger="Error rate > 2.5%, data loss > 2%",
    ),
    CanaryStageConfig(
        stage=RolloutStage.FULL_ROLLOUT,
        week=6,
        rollout_percentage=100,
        target_users="All users",
        metrics_targets={
            "api_latency_p95_ms": 300,
            "error_rate_percent": 0.3,
            "db_connection_pool_utilization_percent": 90,
            "data_consistency_match_percent": 98.0,
        },
        monitoring_intensity="basic",
        rollback_trigger="Critical data loss, system unavailable > 5 min",
    ),
]


class CanaryController:
    """Manage canary rollout progression."""

    def __init__(self):
        self.current_stage = RolloutStage.PHASE_1
        self.stage_start_time = None
        self.metrics_history = []

    def get_current_config(self) -> CanaryStageConfig:
        """Get configuration for current stage."""
        for config in CANARY_STAGES:
            if config.stage == self.current_stage:
                return config
        return CANARY_STAGES[0]

    def advance_to_next_stage(self) -> bool:
        """Advance to next rollout stage."""
        current_idx = next(
            i for i, s in enumerate(CANARY_STAGES) if s.stage == self.current_stage
        )
        if current_idx < len(CANARY_STAGES) - 1:
            self.current_stage = CANARY_STAGES[current_idx + 1].stage
            return True
        return False

    def check_health(self, metrics: Dict[str, float]) -> bool:
        """Check if current stage is healthy."""
        config = self.get_current_config()
        return config.is_healthy(metrics)

    def should_rollback(self, metrics: Dict[str, float]) -> bool:
        """Determine if rollback is needed."""
        error_rate = metrics.get("error_rate_percent", 0)
        data_loss = metrics.get("data_loss_percent", 0)
        latency = metrics.get("api_latency_p95_ms", 0)

        # Rollback triggers
        if error_rate > 5:
            return True
        if data_loss > 5:
            return True
        if latency > 5000:  # 5 seconds
            return True

        return False


# Global canary controller
canary = CanaryController()


def get_canary_config() -> Dict:
    """Get current canary configuration."""
    config = canary.get_current_config()
    return {
        "stage": config.stage.name,
        "week": config.week,
        "rollout_percentage": config.rollout_percentage,
        "target_users": config.target_users,
        "monitoring_intensity": config.monitoring_intensity,
        "metrics_targets": config.metrics_targets,
    }
