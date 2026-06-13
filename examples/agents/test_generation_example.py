#!/usr/bin/env python3
"""
Test Generation Agent Example - Generate tests from natural language
Demonstrates how to use the TestGenerationAgent for test creation
"""

from ml.agents import TestGenerationAgent
import json


def example_simple_test():
    """Example: Generate a simple test from description"""
    agent = TestGenerationAgent()

    print("Generating test for user authentication...")
    result = agent.generate_test(
        description="Test that a user can successfully login with valid credentials",
        target_url="http://localhost:3000/login",
        framework="pytest"
    )

    if result['status'] == 'success':
        print(f"\n✓ Generated test: {result['test_name']}")
        print(f"\nGenerated Code:\n{result['code']}\n")
        print(f"Assertions: {result['assertions']}")
    else:
        print(f"✗ Failed: {result.get('error')}")

    return result


def example_playwright_test():
    """Example: Generate a Playwright test"""
    agent = TestGenerationAgent()

    print("Generating Playwright test for form submission...")
    result = agent.generate_test(
        description="Test that the contact form can be filled and submitted successfully",
        target_url="http://localhost:3000/contact",
        framework="playwright",
        context={
            "form_fields": ["name", "email", "message"],
            "submit_button": "Send Message"
        }
    )

    if result['status'] == 'success':
        print(f"\n✓ Generated test: {result['test_name']}")
        print(f"\nGenerated Code:\n{result['code']}\n")
    else:
        print(f"✗ Failed: {result.get('error')}")

    return result


def example_test_suite():
    """Example: Generate a complete test suite"""
    agent = TestGenerationAgent()

    print("Generating test suite for user management feature...")
    result = agent.generate_test_suite(
        feature_description="User registration, login, and profile management",
        test_scenarios=[
            "User can register with a new email address",
            "User cannot register with duplicate email",
            "User can login with correct credentials",
            "User cannot login with wrong password",
            "Logged-in user can view their profile",
            "User can update profile information",
            "User can logout successfully"
        ],
        framework="pytest"
    )

    if result['status'] == 'success':
        print(f"\n✓ Generated {len(result['test_cases'])} test cases:")
        for test in result['test_cases']:
            print(f"  - {test['name']}")

        if result.get('conftest'):
            print(f"\nGenerated conftest.py:")
            print(result['conftest'][:200] + "...\n")
    else:
        print(f"✗ Failed: {result.get('error')}")

    return result


def example_api_test():
    """Example: Generate API tests"""
    agent = TestGenerationAgent()

    print("Generating API test for user endpoints...")
    result = agent.generate_test(
        description="Test GET /api/users endpoint returns list of users with correct schema",
        framework="pytest",
        context={
            "api_endpoint": "GET /api/users",
            "expected_fields": ["id", "name", "email", "created_at"],
            "expected_status": 200
        }
    )

    if result['status'] == 'success':
        print(f"\n✓ Generated test: {result['test_name']}")
        print(f"\nGenerated Code:\n{result['code']}\n")
    else:
        print(f"✗ Failed: {result.get('error')}")

    return result


def example_test_refinement():
    """Example: Refine existing test based on feedback"""
    agent = TestGenerationAgent()

    # Start with a basic test
    initial_result = agent.generate_test(
        description="Test login functionality",
        framework="pytest"
    )

    if initial_result['status'] != 'success':
        print("✗ Failed to generate initial test")
        return

    initial_code = initial_result['code']
    print("Initial test generated. Refining based on feedback...\n")

    # Refine the test
    feedback = "The test needs better error handling and should test both success and failure cases"

    refine_result = agent.refine_test(
        test_code=initial_code,
        feedback=feedback
    )

    if refine_result['status'] == 'success':
        print(f"✓ Test refined")
        print(f"\nChanges made:")
        for change in refine_result.get('changes', []):
            print(f"  - {change}")

        print(f"\nReasoning: {refine_result.get('reasoning')}")
        print(f"\nRefined Code:\n{refine_result.get('code')}\n")
    else:
        print(f"✗ Refinement failed: {refine_result.get('error')}")

    return refine_result


def example_multilevel_tests():
    """Example: Generate tests at different levels"""
    agent = TestGenerationAgent()

    tests = {
        "unit": "Test that the add() function correctly sums two numbers",
        "integration": "Test that the API correctly processes form submission and updates database",
        "e2e": "Test complete user journey: signup, login, create post, view post"
    }

    print("Generating tests at different levels:\n")

    results = {}
    for level, description in tests.items():
        print(f"Generating {level.upper()} test...")
        result = agent.generate_test(
            description=description,
            framework="pytest"
        )

        if result['status'] == 'success':
            print(f"  ✓ Generated {result['test_name']}")
            results[level] = result
        else:
            print(f"  ✗ Failed: {result.get('error')}")

    return results


def main():
    print("=== Test Generation Agent Examples ===\n")

    print("Example 1: Simple Test Generation")
    print("=" * 50)
    example_simple_test()

    print("\n\nExample 2: Playwright Test")
    print("=" * 50)
    example_playwright_test()

    print("\n\nExample 3: Test Suite Generation")
    print("=" * 50)
    example_test_suite()

    print("\n\nExample 4: API Test Generation")
    print("=" * 50)
    example_api_test()

    print("\n\nExample 5: Test Refinement")
    print("=" * 50)
    example_test_refinement()

    print("\n\nExample 6: Multi-level Tests")
    print("=" * 50)
    example_multilevel_tests()

    print("\n\n✓ All examples completed")


if __name__ == "__main__":
    main()
