#!/usr/bin/env python3
"""
Agent Orchestrator Client
Unified interface for interacting with agent APIs
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
import asyncio

import requests


class OrchestratorClient:
    """Client for Agent Orchestration API"""

    def __init__(
        self,
        orchestrator_url: str = "http://localhost:8003",
        agent_url: str = "http://localhost:8001",
        browser_url: str = "http://localhost:8002"
    ):
        """Initialize orchestrator client"""
        self.orchestrator_url = orchestrator_url
        self.agent_url = agent_url
        self.browser_url = browser_url
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check if orchestrator is healthy"""
        try:
            response = self.session.get(f"{self.orchestrator_url}/health")
            return response.status_code == 200
        except:
            return False

    # Task Management

    def create_task(
        self,
        task_type: str,
        description: str,
        params: Dict,
        priority: str = "medium",
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new task and return task_id"""
        payload = {
            "task_type": task_type,
            "description": description,
            "priority": priority,
            "params": params,
            "metadata": metadata or {}
        }

        response = self.session.post(
            f"{self.orchestrator_url}/api/orchestrator/task",
            json=payload
        )

        if response.status_code != 200:
            raise Exception(f"Failed to create task: {response.text}")

        return response.json()["task_id"]

    def get_task(self, task_id: str) -> Dict:
        """Get task status and result"""
        response = self.session.get(
            f"{self.orchestrator_url}/api/orchestrator/task/{task_id}"
        )

        if response.status_code != 200:
            raise Exception(f"Task not found: {task_id}")

        return response.json()

    def wait_for_task(self, task_id: str, timeout: int = 300, poll_interval: int = 2) -> Dict:
        """Wait for task to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            task = self.get_task(task_id)

            if task["status"] in ["completed", "failed"]:
                return task

            time.sleep(poll_interval)

        raise TimeoutError(f"Task {task_id} timed out after {timeout}s")

    def list_tasks(
        self,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """List tasks with optional filtering"""
        params = {}
        if task_type:
            params["task_type"] = task_type
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority

        response = self.session.get(
            f"{self.orchestrator_url}/api/orchestrator/tasks",
            params=params
        )

        if response.status_code != 200:
            raise Exception(f"Failed to list tasks: {response.text}")

        return response.json()["tasks"]

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        response = self.session.delete(
            f"{self.orchestrator_url}/api/orchestrator/task/{task_id}"
        )

        return response.status_code == 200

    # Browser Automation Tasks

    def browser_navigate(self, url: str) -> str:
        """Create browser navigation task"""
        task_id = self.create_task(
            task_type="browser_automation",
            description=f"Navigate to {url}",
            params={"description": f"Navigate to {url}", "url": url}
        )
        return task_id

    def browser_click(self, selector: str) -> str:
        """Create browser click task"""
        task_id = self.create_task(
            task_type="browser_automation",
            description=f"Click element: {selector}",
            params={"description": f"Click {selector}", "selector": selector}
        )
        return task_id

    def browser_fill_form(self, form_data: Dict[str, str]) -> str:
        """Create form filling task"""
        task_id = self.create_task(
            task_type="browser_automation",
            description="Fill form",
            params={"description": "Fill form", "form_data": form_data}
        )
        return task_id

    # Test Generation Tasks

    def generate_test(
        self,
        description: str,
        url: Optional[str] = None,
        framework: str = "pytest"
    ) -> str:
        """Create test generation task"""
        task_id = self.create_task(
            task_type="test_generation",
            description=description,
            params={
                "description": description,
                "url": url,
                "framework": framework
            }
        )
        return task_id

    def generate_test_suite(
        self,
        feature_description: str,
        test_scenarios: List[str],
        framework: str = "pytest"
    ) -> str:
        """Create test suite generation task"""
        task_id = self.create_task(
            task_type="test_generation",
            description=f"Generate test suite: {feature_description}",
            params={
                "description": feature_description,
                "scenarios": test_scenarios,
                "framework": framework,
                "suite": True
            }
        )
        return task_id

    # Bug Detection Tasks

    def scan_for_bugs(
        self,
        url: str,
        test_cases: Optional[List[str]] = None,
        max_interactions: int = 10
    ) -> str:
        """Create bug detection task"""
        task_id = self.create_task(
            task_type="bug_detection",
            description=f"Scan for bugs: {url}",
            params={
                "url": url,
                "test_cases": test_cases,
                "max_interactions": max_interactions
            },
            priority="high"
        )
        return task_id

    # Web Task Execution

    def execute_web_task(
        self,
        description: str,
        start_url: Optional[str] = None,
        context: Optional[Dict] = None,
        max_steps: int = 50
    ) -> str:
        """Create web task execution"""
        task_id = self.create_task(
            task_type="web_task",
            description=description,
            params={
                "description": description,
                "start_url": start_url,
                "context": context,
                "max_steps": max_steps
            }
        )
        return task_id

    # Batch Operations

    def batch_tasks(
        self,
        tasks: List[Dict],
        parallel: bool = False
    ) -> Dict:
        """Execute multiple tasks"""
        payload = {
            "tasks": tasks,
            "parallel": parallel
        }

        response = self.session.post(
            f"{self.orchestrator_url}/api/orchestrator/batch",
            json=payload
        )

        if response.status_code != 200:
            raise Exception(f"Failed to create batch: {response.text}")

        return response.json()

    # Statistics

    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        response = self.session.get(
            f"{self.orchestrator_url}/api/orchestrator/stats"
        )

        if response.status_code != 200:
            raise Exception(f"Failed to get stats: {response.text}")

        return response.json()

    # Synchronous Execution

    def execute_sync(
        self,
        task_type: str,
        description: str,
        params: Dict,
        timeout: int = 300
    ) -> Dict:
        """Execute a task synchronously (wait for completion)"""
        task_id = self.create_task(task_type, description, params)
        return self.wait_for_task(task_id, timeout)

    def generate_test_sync(
        self,
        description: str,
        url: Optional[str] = None,
        framework: str = "pytest",
        timeout: int = 60
    ) -> Dict:
        """Generate test synchronously"""
        task_id = self.generate_test(description, url, framework)
        return self.wait_for_task(task_id, timeout)

    def scan_bugs_sync(
        self,
        url: str,
        test_cases: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Dict:
        """Scan for bugs synchronously"""
        task_id = self.scan_for_bugs(url, test_cases)
        return self.wait_for_task(task_id, timeout)

    def execute_task_sync(
        self,
        description: str,
        start_url: Optional[str] = None,
        timeout: int = 300
    ) -> Dict:
        """Execute web task synchronously"""
        task_id = self.execute_web_task(description, start_url)
        return self.wait_for_task(task_id, timeout)

    # Browser API (Low-level)

    def browser_screenshot(self) -> bytes:
        """Take a screenshot via Browser API"""
        response = self.session.get(f"{self.browser_url}/api/browser/screenshot")

        if response.status_code != 200:
            raise Exception("Failed to capture screenshot")

        data = response.json()
        # Decode base64 screenshot
        import base64
        return base64.b64decode(data["screenshot"])

    def browser_get_content(self) -> Dict:
        """Get page content via Browser API"""
        response = self.session.get(f"{self.browser_url}/api/browser/content")

        if response.status_code != 200:
            raise Exception("Failed to get page content")

        return response.json()["content"]

    def browser_navigate_direct(self, url: str) -> bool:
        """Navigate directly via Browser API (no task)"""
        response = self.session.post(
            f"{self.browser_url}/api/browser/navigate",
            json={"url": url}
        )

        return response.status_code == 200

    def browser_click_direct(self, selector: str) -> bool:
        """Click directly via Browser API (no task)"""
        response = self.session.post(
            f"{self.browser_url}/api/browser/click",
            json={"selector": selector}
        )

        return response.status_code == 200

    def browser_fill_direct(self, selector: str, text: str) -> bool:
        """Fill form field directly via Browser API (no task)"""
        response = self.session.post(
            f"{self.browser_url}/api/browser/fill",
            json={"selector": selector, "text": text}
        )

        return response.status_code == 200


# Convenience functions

def get_client() -> OrchestratorClient:
    """Get an orchestrator client with environment config"""
    orchestrator_url = os.getenv(
        "ORCHESTRATOR_URL",
        "http://localhost:8003"
    )
    agent_url = os.getenv("AGENT_API_URL", "http://localhost:8001")
    browser_url = os.getenv("BROWSER_API_URL", "http://localhost:8002")

    return OrchestratorClient(orchestrator_url, agent_url, browser_url)


if __name__ == "__main__":
    # Example usage
    client = get_client()

    print(f"Orchestrator healthy: {client.health_check()}")
    print(f"Stats: {client.get_stats()}")
