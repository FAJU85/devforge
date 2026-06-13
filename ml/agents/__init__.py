"""
DevForge AI Agents - Autonomous web automation and testing
"""

from .browser_agent import BrowserAgent
from .test_generator_agent import TestGenerationAgent, TestCase
from .bug_detector_agent import BugDetectionAgent, Bug
from .web_task_agent import WebTaskAgent, TaskResult

__all__ = [
    'BrowserAgent',
    'TestGenerationAgent',
    'TestCase',
    'BugDetectionAgent',
    'Bug',
    'WebTaskAgent',
    'TaskResult',
]

__version__ = '2.0.0'
