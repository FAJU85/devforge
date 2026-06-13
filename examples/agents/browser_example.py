#!/usr/bin/env python3
"""
Browser Agent Example - Autonomous web navigation
Demonstrates how to use the BrowserAgent for web automation
"""

import asyncio
from ml.agents import BrowserAgent


async def example_navigate_and_interact():
    """Example: Navigate and interact with a website"""
    agent = BrowserAgent()
    await agent.start()

    # Navigate to a website
    await agent.navigate("https://www.example.com")

    # Take a screenshot
    screenshot = await agent.screenshot()
    print(f"✓ Screenshot captured ({len(screenshot)} bytes)")

    # Get page content
    content = await agent.get_page_content()
    print(f"✓ Found {len(content.get('elements', []))} interactive elements")

    await agent.stop()


async def example_form_filling():
    """Example: Fill and submit a form"""
    agent = BrowserAgent()
    await agent.start()

    # Navigate to a form
    await agent.navigate("https://www.example.com/form")

    # Fill form fields
    await agent.fill("input#username", "testuser")
    await agent.fill("input#password", "testpass123")

    # Click submit button
    await agent.click("button[type='submit']")

    # Wait a bit for response
    await asyncio.sleep(2)

    # Take screenshot of result
    screenshot = await agent.screenshot()
    print("✓ Form submitted and response captured")

    await agent.stop()


async def example_task_execution():
    """Example: Execute a complex task with AI reasoning"""
    agent = BrowserAgent()
    await agent.start()

    # Execute a complex task with multiple steps
    result = await agent.execute_task(
        task_description="Search for 'artificial intelligence' on Google and click the first link",
        max_iterations=10
    )

    print(f"\nTask Execution Result:")
    print(f"  Status: {result['status']}")
    print(f"  Steps: {result['steps']}")
    print(f"  Actions taken:")
    for action in result['actions']:
        print(f"    - {action.get('action', 'unknown')}: {action.get('reasoning', '')}")

    await agent.stop()


async def example_multi_step_workflow():
    """Example: Multi-step workflow"""
    agent = BrowserAgent()
    await agent.start()

    # Step 1: Navigate to login page
    print("Step 1: Navigating to login page...")
    await agent.navigate("https://example.com/login")
    await asyncio.sleep(1)

    # Step 2: Fill login form
    print("Step 2: Filling login form...")
    page_content = await agent.get_page_content()
    username_input = next(
        (e for e in page_content.get('elements', [])
         if e.get('type') == 'input' and 'user' in e.get('ariaLabel', '').lower()),
        None
    )

    if username_input:
        await agent.fill(f"input[type='text']", "testuser@example.com")
        await agent.fill(f"input[type='password']", "testpass123")

    # Step 3: Submit
    print("Step 3: Submitting login...")
    await agent.click("button[type='submit']")
    await asyncio.sleep(2)

    # Step 4: Take final screenshot
    print("Step 4: Capturing final state...")
    screenshot = await agent.screenshot()
    print(f"✓ Logged in successfully, screenshot captured")

    await agent.stop()


async def main():
    print("=== Browser Agent Examples ===\n")

    print("Example 1: Navigate and Interact")
    print("-" * 40)
    await example_navigate_and_interact()

    print("\n\nExample 2: Form Filling")
    print("-" * 40)
    # Commented out because it needs a real form
    # await example_form_filling()
    print("(Skipped - requires real form)")

    print("\n\nExample 3: Task Execution")
    print("-" * 40)
    # This requires network access
    # await example_task_execution()
    print("(Skipped - requires network)")

    print("\n\nExample 4: Multi-step Workflow")
    print("-" * 40)
    # await example_multi_step_workflow()
    print("(Skipped - requires real website)")

    print("\n\n✓ Examples completed")


if __name__ == "__main__":
    asyncio.run(main())
