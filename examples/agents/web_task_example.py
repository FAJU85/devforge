#!/usr/bin/env python3
"""
Web Task Agent Example - Execute general web automation tasks
Demonstrates how to use the WebTaskAgent for task execution
"""

import asyncio
from ml.agents import WebTaskAgent


async def example_simple_navigation():
    """Example: Simple web navigation task"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Navigate to GitHub and find top repositories\n")

    result = await agent.execute_task(
        task_description="Go to github.com and find the trending repositories section",
        start_url="https://github.com",
        max_iterations=5
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")
    if result.errors:
        print(f"  Errors: {result.errors}")

    await agent.stop()
    return result


async def example_form_filling_task():
    """Example: Fill and submit a form"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Fill out a registration form\n")

    result = await agent.execute_task(
        task_description="Fill out the registration form with: username='testuser', email='test@example.com', password='SecurePass123', and submit it",
        start_url="http://localhost:3000/register",
        max_iterations=8
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")
    if result.output:
        print(f"  Output: {result.output}")

    await agent.stop()
    return result


async def example_information_extraction():
    """Example: Extract information from a page"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Extract product information from an e-commerce page\n")

    result = await agent.execute_task(
        task_description="Navigate to the products page, find the most expensive item, and extract its name, price, and description",
        start_url="http://localhost:3000/products",
        max_iterations=10
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")
    if result.output:
        print(f"  Extracted Data: {result.output}")

    await agent.stop()
    return result


async def example_multi_page_workflow():
    """Example: Multi-page workflow"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Complete a multi-step checkout process\n")

    result = await agent.execute_task(
        task_description="Complete the checkout process: 1) Browse products, 2) Add item to cart, 3) Go to checkout, 4) Fill shipping info, 5) Complete payment",
        start_url="http://localhost:3000",
        max_iterations=15
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")
    if result.errors:
        print(f"  Issues encountered:")
        for error in result.errors:
            print(f"    - {error}")

    await agent.stop()
    return result


async def example_search_task():
    """Example: Search and analyze results"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Search for specific information\n")

    result = await agent.execute_task(
        task_description="Search for 'machine learning frameworks', click on the first result, and extract the key features listed on the page",
        start_url="https://www.google.com",
        max_iterations=10
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")
    print(f"  Final page: {result.output if result.output else 'Not captured'}")

    await agent.stop()
    return result


async def example_dynamic_content_handling():
    """Example: Handle dynamic/JavaScript-rendered content"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Interact with dynamic content\n")

    result = await agent.execute_task(
        task_description="Click the 'Load More' button to load additional items, wait for them to appear, then extract the count of loaded items",
        start_url="http://localhost:3000/dynamic",
        max_iterations=8
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")

    await agent.stop()
    return result


async def example_error_handling():
    """Example: Task with error handling"""
    agent = WebTaskAgent()
    await agent.start()

    print("Task: Handle error scenarios gracefully\n")

    result = await agent.execute_task(
        task_description="Try to access a page, if you get an error, navigate back and try another path",
        start_url="http://localhost:3000/invalid",
        max_iterations=6
    )

    print(f"\nTask Result:")
    print(f"  Status: {result.status}")
    print(f"  Steps executed: {result.steps_executed}")

    if result.errors:
        print(f"  Handled errors:")
        for error in result.errors:
            print(f"    - {error}")
    else:
        print(f"  No errors encountered (task completed successfully)")

    await agent.stop()
    return result


async def example_batch_tasks():
    """Example: Execute multiple tasks in sequence"""
    agent = WebTaskAgent()
    await agent.start()

    tasks = [
        {
            "description": "Navigate to homepage",
            "start_url": "http://localhost:3000"
        },
        {
            "description": "Click on the about page link",
            "start_url": "http://localhost:3000/about"
        },
        {
            "description": "Look for contact information",
            "start_url": "http://localhost:3000/contact"
        }
    ]

    print("Executing batch of tasks:\n")

    results = []
    for i, task in enumerate(tasks, 1):
        print(f"Task {i}: {task['description']}")
        result = await agent.execute_task(
            task_description=task['description'],
            start_url=task.get('start_url'),
            max_iterations=5
        )
        results.append(result)
        print(f"  ✓ Completed in {result.steps_executed} steps\n")

    await agent.stop()

    print(f"\nBatch Summary:")
    print(f"  Total tasks: {len(results)}")
    print(f"  Successful: {sum(1 for r in results if r.status == 'success')}")
    print(f"  Partial: {sum(1 for r in results if r.status == 'partial')}")
    print(f"  Failed: {sum(1 for r in results if r.status == 'failed')}")

    return results


async def main():
    print("=== Web Task Agent Examples ===\n")

    print("Example 1: Simple Navigation")
    print("=" * 50)
    print("(Requires network access)\n")
    # await example_simple_navigation()

    print("\nExample 2: Form Filling")
    print("=" * 50)
    print("(Requires local test server)\n")
    # await example_form_filling_task()

    print("\nExample 3: Information Extraction")
    print("=" * 50)
    print("(Requires local test server)\n")
    # await example_information_extraction()

    print("\nExample 4: Multi-page Workflow")
    print("=" * 50)
    print("(Requires local test server)\n")
    # await example_multi_page_workflow()

    print("\nExample 5: Search Task")
    print("=" * 50)
    print("(Requires network access to Google)\n")
    # await example_search_task()

    print("\nExample 6: Dynamic Content Handling")
    print("=" * 50)
    print("(Requires local test server with dynamic content)\n")
    # await example_dynamic_content_handling()

    print("\nExample 7: Error Handling")
    print("=" * 50)
    print("(Requires local test server)\n")
    # await example_error_handling()

    print("\nExample 8: Batch Tasks")
    print("=" * 50)
    print("(Requires local test server)\n")
    # await example_batch_tasks()

    print("\n✓ Examples completed")
    print("\nNote: Run actual examples in an environment with:")
    print("  - Network access (for web examples)")
    print("  - Local test server running on localhost:3000")
    print("  - API keys configured in .env files")
    print("  - Playwright browsers installed (npx playwright install)")


if __name__ == "__main__":
    asyncio.run(main())
