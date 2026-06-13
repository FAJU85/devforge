#!/usr/bin/env python3
"""
Browser Automation Agent - AI-powered browser control
Uses Playwright + Anthropic Claude for autonomous web interaction
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import base64
import os

try:
    from anthropic import Anthropic
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("Install dependencies: pip install anthropic playwright")
    exit(1)


@dataclass
class BrowserAction:
    """Represents a browser action"""
    type: str  # navigate, click, fill, screenshot, wait, extract
    target: Optional[str] = None
    value: Optional[str] = None
    description: str = ""


class BrowserAgent:
    """AI-powered browser agent using Claude"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key)
        self.browser = None
        self.page = None
        self.conversation_history = []
        self.max_steps = int(os.getenv('AGENT_MAX_STEPS', 50))

    async def start(self):
        """Start browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv('HEADLESS', 'true').lower() == 'true'
        )
        self.page = await self.browser.new_page()
        print("✓ Browser started")

    async def stop(self):
        """Stop browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        print("✓ Browser stopped")

    async def navigate(self, url: str) -> bool:
        """Navigate to URL"""
        try:
            await self.page.goto(url, timeout=30000)
            print(f"✓ Navigated to {url}")
            return True
        except Exception as e:
            print(f"✗ Navigation failed: {e}")
            return False

    async def screenshot(self) -> str:
        """Take screenshot and encode as base64"""
        try:
            screenshot_bytes = await self.page.screenshot()
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            print(f"✗ Screenshot failed: {e}")
            return ""

    async def get_page_content(self) -> Dict[str, Any]:
        """Get page structure and content"""
        try:
            content = await self.page.evaluate("""() => {
                const elements = [];
                document.querySelectorAll('button, input, a, select, textarea').forEach((el, idx) => {
                    if (el.offsetParent !== null) {
                        elements.push({
                            id: idx,
                            type: el.tagName.toLowerCase(),
                            text: el.innerText || el.value || el.placeholder,
                            ariaLabel: el.getAttribute('aria-label'),
                            className: el.className,
                            visible: el.offsetParent !== null
                        });
                    }
                });
                return {
                    title: document.title,
                    url: document.URL,
                    elements: elements
                };
            }""")
            return content
        except Exception as e:
            print(f"✗ Failed to get page content: {e}")
            return {}

    async def click(self, selector: str) -> bool:
        """Click element"""
        try:
            await self.page.click(selector, timeout=5000)
            print(f"✓ Clicked {selector}")
            return True
        except Exception as e:
            print(f"✗ Click failed: {e}")
            return False

    async def fill(self, selector: str, text: str) -> bool:
        """Fill input field"""
        try:
            await self.page.fill(selector, text, timeout=5000)
            print(f"✓ Filled {selector}")
            return True
        except Exception as e:
            print(f"✗ Fill failed: {e}")
            return False

    async def execute_task(self, task_description: str, max_iterations: int = None) -> Dict:
        """Execute a task with AI reasoning"""
        if not self.page:
            await self.start()

        max_iterations = max_iterations or self.max_steps
        step_count = 0
        actions_taken = []

        print(f"\n📋 Task: {task_description}\n")

        while step_count < max_iterations:
            step_count += 1
            print(f"Step {step_count}/{max_iterations}:")

            # Get current page state
            page_content = await self.get_page_content()
            screenshot = await self.screenshot()

            # Prepare context for Claude
            context = f"""
You are an AI agent controlling a web browser. Your task: {task_description}

Current page:
Title: {page_content.get('title', 'Unknown')}
URL: {page_content.get('url', 'Unknown')}

Available elements:
{json.dumps(page_content.get('elements', [])[:10], indent=2)}

Previous actions:
{json.dumps(actions_taken[-5:], indent=2) if actions_taken else 'None'}

What is your next action? Respond in JSON format:
{{
    "action": "navigate|click|fill|scroll|wait|extract|done",
    "target": "CSS selector or URL",
    "value": "text to fill or null",
    "reasoning": "explain why"
}}
"""

            # Get Claude's decision
            self.conversation_history.append({
                "role": "user",
                "content": context
            })

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=self.conversation_history
            )

            action_text = response.content[0].text

            # Parse action
            try:
                action = json.loads(action_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', action_text, re.DOTALL)
                if json_match:
                    action = json.loads(json_match.group())
                else:
                    print(f"⚠ Failed to parse action: {action_text}")
                    continue

            self.conversation_history.append({
                "role": "assistant",
                "content": action_text
            })

            # Execute action
            action_type = action.get('action', '').lower()
            reasoning = action.get('reasoning', '')

            print(f"  → {action_type.upper()}: {reasoning}")

            if action_type == "done":
                print("✓ Task completed")
                return {
                    "status": "completed",
                    "steps": step_count,
                    "actions": actions_taken
                }

            elif action_type == "navigate":
                await self.navigate(action.get('target', ''))
                actions_taken.append(action)

            elif action_type == "click":
                selector = action.get('target', '')
                await self.click(selector)
                actions_taken.append(action)

            elif action_type == "fill":
                selector = action.get('target', '')
                value = action.get('value', '')
                await self.fill(selector, value)
                actions_taken.append(action)

            elif action_type == "wait":
                wait_time = int(action.get('value', 1))
                await asyncio.sleep(wait_time)
                actions_taken.append(action)

            elif action_type == "scroll":
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                actions_taken.append(action)

            elif action_type == "extract":
                content = await self.page.evaluate(action.get('target', ''))
                print(f"  Extracted: {content}")
                actions_taken.append({**action, "result": content})

            await asyncio.sleep(0.5)  # Brief pause between actions

        return {
            "status": "max_steps_reached",
            "steps": step_count,
            "actions": actions_taken
        }


# Example usage
async def main():
    agent = BrowserAgent()
    await agent.start()

    # Example: Navigate to a site
    await agent.navigate("https://www.example.com")

    # Example: Execute a task
    result = await agent.execute_task(
        "Find and click the first link on the page, then take a screenshot"
    )

    print(f"\nTask result: {result}")

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
