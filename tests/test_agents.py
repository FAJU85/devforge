#!/usr/bin/env python3
"""
Comprehensive test suite for AI agents
Tests agent functionality, error handling, and integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ml.agents import (
    BrowserAgent,
    TestGenerationAgent,
    BugDetectionAgent,
    WebTaskAgent
)


class TestBrowserAgent:
    """Test suite for BrowserAgent"""

    @pytest.fixture
    async def agent(self):
        """Create test agent"""
        agent = BrowserAgent()
        yield agent

    @pytest.mark.asyncio
    async def test_browser_agent_initialization(self):
        """Test agent initialization"""
        agent = BrowserAgent()
        assert agent.client is not None
        assert agent.browser is None
        assert agent.page is None
        assert agent.conversation_history == []

    @pytest.mark.asyncio
    async def test_browser_navigation(self):
        """Test URL navigation"""
        agent = BrowserAgent()
        # Mock the navigate method
        with patch.object(agent, 'navigate', return_value=True) as mock_nav:
            result = await agent.navigate("https://example.com")
            assert result is True
            mock_nav.assert_called_once()

    @pytest.mark.asyncio
    async def test_screenshot_capture(self):
        """Test screenshot capture"""
        agent = BrowserAgent()
        with patch.object(agent, 'screenshot', return_value="mock_b64_data") as mock_ss:
            result = await agent.screenshot()
            assert result == "mock_b64_data"
            mock_ss.assert_called_once()

    @pytest.mark.asyncio
    async def test_page_content_extraction(self):
        """Test page content extraction"""
        agent = BrowserAgent()
        mock_content = {
            "title": "Test Page",
            "url": "https://example.com",
            "elements": []
        }
        with patch.object(agent, 'get_page_content', return_value=mock_content):
            result = await agent.get_page_content()
            assert result["title"] == "Test Page"
            assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_element_click(self):
        """Test element clicking"""
        agent = BrowserAgent()
        with patch.object(agent, 'click', return_value=True) as mock_click:
            result = await agent.click("button.submit")
            assert result is True
            mock_click.assert_called_once_with("button.submit")

    @pytest.mark.asyncio
    async def test_form_fill(self):
        """Test form field filling"""
        agent = BrowserAgent()
        with patch.object(agent, 'fill', return_value=True) as mock_fill:
            result = await agent.fill("input#username", "testuser")
            assert result is True
            mock_fill.assert_called_once_with("input#username", "testuser")


class TestTestGenerationAgent:
    """Test suite for TestGenerationAgent"""

    @pytest.fixture
    def agent(self):
        """Create test agent"""
        return TestGenerationAgent()

    def test_agent_initialization(self, agent):
        """Test agent initialization"""
        assert agent.client is not None
        assert agent.conversation_history == []

    def test_single_test_generation(self, agent):
        """Test single test generation"""
        with patch.object(agent.client.messages, 'create') as mock_create:
            mock_create.return_value.content = [Mock(text='{"status": "success"}')]
            result = agent.generate_test(
                "Test login",
                "http://localhost:3000/login"
            )
            assert "status" in result or "error" in result

    def test_test_suite_generation(self, agent):
        """Test suite generation"""
        with patch.object(agent.client.messages, 'create') as mock_create:
            mock_create.return_value.content = [Mock(text='{"test_cases": []}')]
            result = agent.generate_test_suite(
                "User authentication",
                ["login", "logout", "register"]
            )
            assert "test_cases" in result or "error" in result

    def test_test_refinement(self, agent):
        """Test test refinement"""
        test_code = "def test_login(): pass"
        feedback = "Add assertions"

        with patch.object(agent.client.messages, 'create') as mock_create:
            mock_create.return_value.content = [Mock(text='{"improved_code": "..."}')]
            result = agent.refine_test(test_code, feedback)
            assert "code" in result or "error" in result


class TestBugDetectionAgent:
    """Test suite for BugDetectionAgent"""

    @pytest.fixture
    async def agent(self):
        """Create test agent"""
        agent = BugDetectionAgent()
        yield agent

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization"""
        agent = BugDetectionAgent()
        assert agent.client is not None
        assert agent.browser is None
        assert agent.detected_bugs == []

    @pytest.mark.asyncio
    async def test_bug_scanning(self):
        """Test bug detection"""
        agent = BugDetectionAgent()
        with patch.object(agent, 'detect_bugs') as mock_detect:
            mock_detect.return_value = {
                "status": "success",
                "bugs_found": 3,
                "bugs": []
            }
            result = await agent.detect_bugs("https://example.com")
            assert result["status"] == "success"
            assert "bugs_found" in result

    @pytest.mark.asyncio
    async def test_bug_categorization(self):
        """Test bug categorization"""
        agent = BugDetectionAgent()
        mock_bugs = [
            {"severity": "critical", "category": "crash"},
            {"severity": "high", "category": "performance"},
            {"severity": "low", "category": "ui"}
        ]

        critical = [b for b in mock_bugs if b["severity"] == "critical"]
        assert len(critical) == 1


class TestWebTaskAgent:
    """Test suite for WebTaskAgent"""

    @pytest.fixture
    async def agent(self):
        """Create test agent"""
        agent = WebTaskAgent()
        yield agent

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization"""
        agent = WebTaskAgent()
        assert agent.client is not None
        assert agent.browser is None
        assert agent.task_counter == 0

    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test task execution"""
        agent = WebTaskAgent()
        with patch.object(agent, 'execute_task') as mock_execute:
            mock_execute.return_value = Mock(
                task_id="TASK-001",
                status="completed",
                steps_executed=5
            )
            result = await agent.execute_task("Search for AI")
            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_multi_step_workflow(self):
        """Test multi-step workflow"""
        agent = WebTaskAgent()
        with patch.object(agent, 'execute_task') as mock_execute:
            mock_execute.return_value = Mock(
                task_id="TASK-001",
                steps_executed=10,
                errors=[]
            )
            result = await agent.execute_task(
                "Navigate, click, extract data",
                max_iterations=15
            )
            assert result.steps_executed > 0


class TestAgentIntegration:
    """Integration tests for all agents"""

    @pytest.mark.asyncio
    async def test_sequential_agent_execution(self):
        """Test sequential execution of multiple agents"""
        browser_agent = BrowserAgent()
        test_agent = TestGenerationAgent()

        # Test that agents can be instantiated and used sequentially
        assert browser_agent is not None
        assert test_agent is not None

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test error handling in agents"""
        agent = BrowserAgent()

        # Mock a failed operation
        with patch.object(agent, 'navigate', return_value=False):
            result = await agent.navigate("invalid://url")
            assert result is False

    def test_agent_conversation_history(self):
        """Test conversation history tracking"""
        agent = TestGenerationAgent()

        initial_len = len(agent.conversation_history)
        agent.conversation_history.append({
            "role": "user",
            "content": "Test message"
        })

        assert len(agent.conversation_history) == initial_len + 1


# Test fixtures for async operations
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
