#!/usr/bin/env python3
"""
Web Task Agent - Executes general web automation tasks
Uses Anthropic Claude for intelligent task understanding and execution
"""

import asyncio
import json
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os

try:
    from anthropic import Anthropic
    from playwright.async_api import async_playwright
except ImportError:
    print("Install dependencies: pip install anthropic playwright")
    exit(1)


@dataclass
class TaskResult:
    """Represents task execution result"""
    task_id: str
    status: str  # success, failed, partial
    description: str
    steps_executed: int
    output: Any
    errors: List[str]
    final_screenshot: Optional[str] = None


class WebTaskAgent:
    """AI-powered web task execution agent using Claude"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key)
        self.browser = None
        self.page = None
        self.conversation_history = []
        self.max_steps = int(os.getenv('AGENT_MAX_STEPS', 50))
        self.task_counter = 0

    async def start(self):
        """Start browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv('HEADLESS', 'true').lower() == 'true'
        )
        self.page = await self.browser.new_page()
        print("✓ Web task agent browser started")

    async def stop(self):
        """Stop browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        print("✓ Web task agent browser stopped")

    async def get_page_state(self) -> Dict[str, Any]:
        """Get current page state"""
        try:
            state = await self.page.evaluate("""() => {
                const elements = [];
                document.querySelectorAll('button, input, a, select, textarea, [onclick]').forEach((el, idx) => {
                    if (el.offsetParent !== null) {
                        elements.push({
                            id: idx,
                            type: el.tagName.toLowerCase(),
                            text: el.innerText || el.value || el.placeholder,
                            ariaLabel: el.getAttribute('aria-label'),
                            className: el.className,
                            id_attr: el.id,
                            role: el.getAttribute('role')
                        });
                    }
                });
                return {
                    title: document.title,
                    url: document.URL,
                    readyState: document.readyState,
                    elements: elements,
                    bodyText: document.body.innerText.slice(0, 500)
                };
            }""")
            return state
        except Exception as e:
            print(f"⚠ Failed to get page state: {e}")
            return {}

    async def execute_action(self, action: Dict) -> bool:
        """Execute a single action on the page"""
        action_type = action.get('type', '').lower()

        try:
            if action_type == 'navigate':
                await self.page.goto(action['target'], timeout=30000)
                print(f"  ✓ Navigated to {action['target']}")
                return True

            elif action_type == 'click':
                await self.page.click(action['target'], timeout=5000)
                print(f"  ✓ Clicked {action['target']}")
                return True

            elif action_type == 'fill':
                await self.page.fill(action['target'], action['value'], timeout=5000)
                print(f"  ✓ Filled {action['target']}")
                return True

            elif action_type == 'select':
                await self.page.select_option(action['target'], action['value'], timeout=5000)
                print(f"  ✓ Selected option")
                return True

            elif action_type == 'press':
                await self.page.press(action['target'], action['value'], timeout=5000)
                print(f"  ✓ Pressed key")
                return True

            elif action_type == 'wait':
                wait_time = int(action.get('value', 2))
                await asyncio.sleep(wait_time)
                print(f"  ✓ Waited {wait_time}s")
                return True

            elif action_type == 'scroll':
                await self.page.evaluate(f"window.scrollBy(0, {action.get('value', 300)})")
                print(f"  ✓ Scrolled page")
                return True

            elif action_type == 'extract':
                result = await self.page.evaluate(action['target'])
                print(f"  ✓ Extracted data")
                return result

            elif action_type == 'goto_url':
                await self.page.goto(action['value'], timeout=30000)
                print(f"  ✓ Navigated to {action['value']}")
                return True

            else:
                print(f"  ⚠ Unknown action type: {action_type}")
                return False

        except Exception as e:
            print(f"  ✗ Action failed: {e}")
            return False

    async def execute_task(
        self,
        task_description: str,
        start_url: Optional[str] = None,
        context: Optional[Dict] = None,
        max_iterations: Optional[int] = None
    ) -> TaskResult:
        """
        Execute a web task using AI reasoning

        Args:
            task_description: What to do
            start_url: URL to start at
            context: Additional context
            max_iterations: Max steps to take

        Returns:
            TaskResult with execution details
        """
        if not self.page:
            await self.start()

        self.task_counter += 1
        task_id = f"TASK-{self.task_counter:04d}"
        max_iterations = max_iterations or self.max_steps
        step_count = 0
        actions_taken = []
        errors = []
        task_output = None

        print(f"\n📋 Task {task_id}: {task_description}\n")

        # Navigate to start URL if provided
        if start_url:
            try:
                await self.page.goto(start_url, timeout=30000)
                print(f"✓ Navigated to {start_url}")
            except Exception as e:
                errors.append(f"Failed to navigate to {start_url}: {e}")
                return TaskResult(
                    task_id=task_id,
                    status="failed",
                    description=task_description,
                    steps_executed=0,
                    output=None,
                    errors=errors
                )

        # Main task loop
        while step_count < max_iterations:
            step_count += 1
            print(f"Step {step_count}/{max_iterations}:")

            # Get current page state
            page_state = await self.get_page_state()

            # Prepare context for Claude
            task_context = f"""You are an AI agent executing web tasks. Your task: {task_description}

Current page:
Title: {page_state.get('title', 'Unknown')}
URL: {page_state.get('url', 'Unknown')}

Available elements:
{json.dumps(page_state.get('elements', [])[:15], indent=2)}

Body text (first 500 chars):
{page_state.get('bodyText', 'No text')}

Previous actions:
{json.dumps(actions_taken[-3:], indent=2) if actions_taken else 'None'}

What is your next action? Respond in JSON format:
{{
    "action": "navigate|click|fill|select|press|wait|scroll|extract|done",
    "target": "CSS selector, URL, or JavaScript code",
    "value": "value to fill/select/press or wait time",
    "reasoning": "explain your action"
}}"""

            # Get Claude's decision
            self.conversation_history.append({
                "role": "user",
                "content": task_context
            })

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=self.conversation_history
            )

            response_text = response.content[0].text

            # Parse action
            try:
                action = json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    action = json.loads(json_match.group())
                else:
                    errors.append(f"Failed to parse action: {response_text}")
                    continue

            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            action_type = action.get('action', '').lower()
            reasoning = action.get('reasoning', '')
            print(f"  → {action_type.upper()}: {reasoning}")

            if action_type == 'done':
                print("✓ Task completed")
                task_output = action.get('result', '')
                break

            # Execute action
            result = await self.execute_action(action)
            actions_taken.append({
                'action': action_type,
                'target': action.get('target'),
                'success': result
            })

            # Brief pause between actions
            await asyncio.sleep(0.5)

        # Take final screenshot
        try:
            final_screenshot = base64.b64encode(
                await self.page.screenshot()
            ).decode('utf-8')
        except:
            final_screenshot = None

        # Determine final status
        status = "success" if step_count < max_iterations else "partial"

        return TaskResult(
            task_id=task_id,
            status=status,
            description=task_description,
            steps_executed=step_count,
            output=task_output,
            errors=errors,
            final_screenshot=final_screenshot
        )

    async def execute_tasks_batch(
        self,
        tasks: List[Dict],
        parallel: bool = False
    ) -> List[TaskResult]:
        """
        Execute multiple tasks

        Args:
            tasks: List of task definitions
            parallel: Execute in parallel (not recommended for single browser)

        Returns:
            List of TaskResults
        """
        results = []

        if parallel:
            # Create multiple browser instances
            # This is more complex and not shown in detail here
            print("⚠ Parallel task execution not fully implemented")

        for task in tasks:
            result = await self.execute_task(
                task.get('description', ''),
                task.get('start_url'),
                task.get('context')
            )
            results.append(result)

        return results


# Example usage
async def main():
    agent = WebTaskAgent()
    await agent.start()

    # Example 1: Simple task
    result1 = await agent.execute_task(
        task_description="Search for 'machine learning' on Google",
        start_url="https://www.google.com"
    )

    print(f"\nTask Result:")
    print(f"  Status: {result1.status}")
    print(f"  Steps: {result1.steps_executed}")
    print(f"  Errors: {result1.errors}")

    # Example 2: Complex task
    result2 = await agent.execute_task(
        task_description="Find the latest news on the homepage",
        start_url="https://news.ycombinator.com"
    )

    print(f"\nTask Result:")
    print(f"  Status: {result2.status}")
    print(f"  Steps: {result2.steps_executed}")

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
