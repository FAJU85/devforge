#!/usr/bin/env python3
"""
Test Generator Agent - Generates test code from natural language
Uses Anthropic Claude to understand requirements and create test cases
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


@dataclass
class TestCase:
    """Represents a generated test case"""
    name: str
    description: str
    code: str
    framework: str  # pytest, unittest, playwright, selenium
    assertions: List[str]


class TestGenerationAgent:
    """AI-powered test generation agent using Claude"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key) if Anthropic else None
        self.conversation_history = []

    def generate_test(
        self,
        description: str,
        target_url: str = None,
        framework: str = "pytest",
        context: Dict = None
    ) -> Dict:
        """
        Generate test code from natural language description

        Args:
            description: What the test should do
            target_url: URL to test against
            framework: Test framework to use (pytest, unittest, playwright, selenium)
            context: Additional context (page title, elements, etc.)

        Returns:
            Dictionary with generated test code and metadata
        """

        # Build context for Claude
        context_str = ""
        if target_url:
            context_str += f"Target URL: {target_url}\n"
        if context:
            context_str += f"Page Context:\n{json.dumps(context, indent=2)}\n"

        prompt = f"""You are an expert QA engineer generating test code.

Framework: {framework}
Description: {description}

{context_str}

Generate a complete, runnable test case that:
1. Is syntactically correct
2. Follows {framework} conventions
3. Includes clear assertions
4. Has descriptive test names
5. Includes docstrings

Respond with ONLY valid JSON in this format:
{{
    "test_name": "test_name_here",
    "code": "complete test code",
    "assertions": ["assertion 1", "assertion 2"],
    "imports": ["import statement 1", "import statement 2"],
    "setup": "setup code if needed",
    "teardown": "cleanup code if needed"
}}"""

        # Get Claude's response
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=self.conversation_history
        )

        response_text = response.content[0].text

        # Parse response
        try:
            test_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                test_data = json.loads(json_match.group())
            else:
                return {
                    "status": "failed",
                    "error": "Failed to parse response",
                    "raw_response": response_text
                }

        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        # Format complete test code
        imports = test_data.get('imports', [])
        setup = test_data.get('setup', '')
        test_code = test_data.get('code', '')
        teardown = test_data.get('teardown', '')

        complete_code = "\n".join(imports) + "\n\n"
        if setup:
            complete_code += f"def setup():\n    {setup}\n\n"
        complete_code += test_code
        if teardown:
            complete_code += f"\n\ndef teardown():\n    {teardown}"

        return {
            "status": "success",
            "test_name": test_data.get('test_name', 'generated_test'),
            "code": complete_code,
            "assertions": test_data.get('assertions', []),
            "framework": framework
        }

    def generate_test_suite(
        self,
        feature_description: str,
        test_scenarios: List[str],
        framework: str = "pytest"
    ) -> Dict:
        """
        Generate a complete test suite for a feature

        Args:
            feature_description: Description of the feature being tested
            test_scenarios: List of test scenarios to cover
            framework: Test framework to use

        Returns:
            Dictionary with generated test suite
        """

        prompt = f"""You are an expert QA engineer creating a test suite.

Feature: {feature_description}

Test Scenarios to Cover:
{json.dumps(test_scenarios, indent=2)}

Framework: {framework}

Generate a complete test suite that:
1. Covers all scenarios
2. Uses proper {framework} patterns
3. Includes fixtures or setup/teardown
4. Has good assertions
5. Is well-documented

Respond with ONLY valid JSON:
{{
    "test_cases": [
        {{
            "name": "test name",
            "code": "test code"
        }}
    ],
    "fixtures": "fixture code if needed",
    "conftest": "conftest.py content if pytest"
}}"""

        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            messages=self.conversation_history
        )

        response_text = response.content[0].text

        try:
            suite_data = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                suite_data = json.loads(json_match.group())
            else:
                return {
                    "status": "failed",
                    "error": "Failed to parse response"
                }

        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        return {
            "status": "success",
            "test_cases": suite_data.get('test_cases', []),
            "fixtures": suite_data.get('fixtures', ''),
            "conftest": suite_data.get('conftest', ''),
            "framework": framework
        }

    def refine_test(self, test_code: str, feedback: str) -> Dict:
        """
        Refine existing test based on feedback

        Args:
            test_code: Current test code
            feedback: Feedback on the test

        Returns:
            Dictionary with refined test code
        """

        prompt = f"""Review and improve this test code based on feedback:

Current Test:
{test_code}

Feedback:
{feedback}

Provide an improved version that addresses the feedback.
Respond with ONLY valid JSON:
{{
    "improved_code": "improved test code",
    "changes": ["change 1", "change 2"],
    "reasoning": "why these changes were made"
}}"""

        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=self.conversation_history
        )

        response_text = response.content[0].text

        try:
            refined_data = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                refined_data = json.loads(json_match.group())
            else:
                return {"status": "failed", "error": "Failed to parse response"}

        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })

        return {
            "status": "success",
            "code": refined_data.get('improved_code', ''),
            "changes": refined_data.get('changes', []),
            "reasoning": refined_data.get('reasoning', '')
        }


# Example usage
def main():
    agent = TestGenerationAgent()

    # Example 1: Simple test generation
    print("Generating test for login functionality...")
    result = agent.generate_test(
        description="Test user login with valid credentials",
        target_url="http://localhost:3000/login",
        framework="playwright"
    )

    if result['status'] == 'success':
        print(f"\nGenerated test: {result['test_name']}")
        print(f"Code:\n{result['code']}\n")
        print(f"Assertions: {result['assertions']}\n")

    # Example 2: Test suite generation
    print("\nGenerating test suite for user management...")
    suite_result = agent.generate_test_suite(
        feature_description="User authentication and profile management",
        test_scenarios=[
            "User can register with valid email",
            "User can login with correct password",
            "User cannot login with wrong password",
            "User can update profile information",
            "User can logout"
        ],
        framework="pytest"
    )

    if suite_result['status'] == 'success':
        print(f"Generated {len(suite_result['test_cases'])} test cases")
        for test in suite_result['test_cases']:
            print(f"  - {test['name']}")


if __name__ == "__main__":
    main()
