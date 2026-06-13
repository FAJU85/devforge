#!/usr/bin/env python3
"""
Health Check Module - System health monitoring
Provides endpoint for status checks and dependency health
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import asyncio


class HealthStatus(str, Enum):
    """Health status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth:
    """Health status of a component"""

    def __init__(self, name: str, status: HealthStatus, message: str = ""):
        self.name = name
        self.status = status
        self.message = message
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp
        }


class SystemHealthCheck:
    """Monitors overall system health"""

    def __init__(self):
        """Initialize health checker"""
        self.components: Dict[str, ComponentHealth] = {}

    def set_component_health(
        self,
        name: str,
        status: HealthStatus,
        message: str = ""
    ):
        """Update component health status"""
        self.components[name] = ComponentHealth(name, status, message)

    def get_overall_status(self) -> HealthStatus:
        """Get overall system status"""
        if not self.components:
            return HealthStatus.HEALTHY

        statuses = [c.status for c in self.components.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        # Check API services
        await self._check_api_services()

        # Check external services
        await self._check_external_services()

        return self.get_health_report()

    async def _check_api_services(self):
        """Check internal API services health"""
        try:
            # Check if services can be imported
            from api.services.auth_service import auth_service
            from api.services.chat_service import chat_service
            from api.services.config_service import config_service

            self.set_component_health(
                "auth_service",
                HealthStatus.HEALTHY,
                "Authentication service operational"
            )
            self.set_component_health(
                "chat_service",
                HealthStatus.HEALTHY,
                "Chat service operational"
            )
            self.set_component_health(
                "config_service",
                HealthStatus.HEALTHY,
                "Configuration service operational"
            )

        except Exception as e:
            self.set_component_health(
                "api_services",
                HealthStatus.UNHEALTHY,
                f"Service error: {str(e)}"
            )

    async def _check_external_services(self):
        """Check external service health"""
        # Check Anthropic API
        try:
            from anthropic import Anthropic
            Anthropic()
            self.set_component_health(
                "anthropic_api",
                HealthStatus.HEALTHY,
                "Anthropic API available"
            )
        except Exception as e:
            self.set_component_health(
                "anthropic_api",
                HealthStatus.DEGRADED,
                f"Anthropic API check failed: {str(e)}"
            )

        # Check Groq API
        try:
            from groq import Groq
            Groq()
            self.set_component_health(
                "groq_api",
                HealthStatus.HEALTHY,
                "Groq API available"
            )
        except Exception as e:
            self.set_component_health(
                "groq_api",
                HealthStatus.DEGRADED,
                f"Groq API check failed: {str(e)}"
            )

        # Check Hugging Face API
        try:
            from huggingface_hub import InferenceClient
            InferenceClient()
            self.set_component_health(
                "huggingface_api",
                HealthStatus.HEALTHY,
                "Hugging Face API available"
            )
        except Exception as e:
            self.set_component_health(
                "huggingface_api",
                HealthStatus.DEGRADED,
                f"Hugging Face API check failed: {str(e)}"
            )

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        overall_status = self.get_overall_status()

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                name: health.to_dict()
                for name, health in self.components.items()
            },
            "summary": {
                "healthy": sum(1 for c in self.components.values() if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in self.components.values() if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in self.components.values() if c.status == HealthStatus.UNHEALTHY),
            }
        }


# Global health checker
health_check = SystemHealthCheck()
