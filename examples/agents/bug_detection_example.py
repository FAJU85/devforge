#!/usr/bin/env python3
"""
Bug Detection Agent Example - Detect bugs through interaction
Demonstrates how to use the BugDetectionAgent for QA
"""

import asyncio
from ml.agents import BugDetectionAgent
import json


async def example_basic_detection():
    """Example: Basic bug detection on a website"""
    agent = BugDetectionAgent()
    await agent.start()

    print("Scanning for bugs on example.com...")
    result = await agent.detect_bugs(
        url="https://www.example.com",
        test_cases=[
            "Load homepage",
            "Check for broken links",
            "Verify form fields",
            "Check image loading"
        ]
    )

    if result['status'] == 'success':
        print(f"\n✓ Scan complete")
        print(f"  Bugs found: {result['bugs_found']}")
        print(f"  Interactions: {result['interactions_count']}")

        if result['bugs']:
            print(f"\nBugs detected:")
            for bug in result['bugs']:
                print(f"  [{bug['severity'].upper()}] {bug['id']}: {bug['description']}")

        print(f"\nRecommendations:")
        for rec in result.get('recommendations', []):
            print(f"  • {rec}")
    else:
        print(f"✗ Scan failed: {result.get('error')}")

    await agent.stop()
    return result


async def example_focused_testing():
    """Example: Focused testing on specific functionality"""
    agent = BugDetectionAgent()
    await agent.start()

    print("Testing login functionality for bugs...")
    result = await agent.detect_bugs(
        url="http://localhost:3000/login",
        test_cases=[
            "Test with empty username",
            "Test with empty password",
            "Test with invalid email format",
            "Test with very long input",
            "Test SQL injection attempt",
            "Test successful login with valid credentials"
        ],
        max_interactions=8
    )

    if result['status'] == 'success':
        print(f"\n✓ Login testing complete")
        print(f"  Bugs found: {result['bugs_found']}")

        # Categorize bugs
        severity_counts = {}
        for bug in result['bugs']:
            severity = bug['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        print(f"\nBug breakdown by severity:")
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                print(f"  {severity.capitalize()}: {count}")

        print(f"\nSummary: {result.get('summary', '')}")
    else:
        print(f"✗ Testing failed: {result.get('error')}")

    await agent.stop()
    return result


async def example_report_generation():
    """Example: Generate bug report"""
    agent = BugDetectionAgent()
    await agent.start()

    print("Scanning website and generating report...")
    result = await agent.detect_bugs(
        url="https://example.com/app",
        test_cases=[
            "Basic navigation",
            "Form submission",
            "Error handling",
            "Performance"
        ],
        max_interactions=10
    )

    if result['status'] == 'success':
        # Export as JSON report
        json_report = agent.export_report(format="json")
        print("\nJSON Report generated:")
        print(json_report[:500] + "...\n")

        # Export as Markdown report
        md_report = agent.export_report(format="markdown")
        print("Markdown Report generated:")
        print(md_report[:500] + "...\n")

        # Save reports
        with open('/tmp/bug_report.json', 'w') as f:
            f.write(json_report)

        with open('/tmp/bug_report.md', 'w') as f:
            f.write(md_report)

        print("✓ Reports saved to /tmp/")
    else:
        print(f"✗ Scanning failed: {result.get('error')}")

    await agent.stop()
    return result


async def example_continuous_monitoring():
    """Example: Monitor website for regressions"""
    agent = BugDetectionAgent()
    await agent.start()

    print("Monitoring for regressions...")

    test_urls = [
        "https://example.com",
        "https://example.com/products",
        "https://example.com/cart"
    ]

    all_bugs = []

    for url in test_urls:
        print(f"\nScanning {url}...")
        result = await agent.detect_bugs(
            url=url,
            test_cases=["Load page", "Check functionality"],
            max_interactions=5
        )

        if result['status'] == 'success':
            all_bugs.extend(result['bugs'])
            print(f"  ✓ Found {result['bugs_found']} issue(s)")
        else:
            print(f"  ✗ Scan failed")

    print(f"\n{'='*50}")
    print(f"Total issues found across all pages: {len(all_bugs)}")

    # Group by severity
    critical = [b for b in all_bugs if b['severity'] == 'critical']
    high = [b for b in all_bugs if b['severity'] == 'high']

    if critical:
        print(f"\n⚠ CRITICAL ISSUES ({len(critical)}):")
        for bug in critical:
            print(f"  - {bug['description']}")

    if high:
        print(f"\n⚠ HIGH PRIORITY ({len(high)}):")
        for bug in high:
            print(f"  - {bug['description']}")

    await agent.stop()


async def main():
    print("=== Bug Detection Agent Examples ===\n")

    print("Example 1: Basic Bug Detection")
    print("=" * 50)
    # This requires network access to example.com
    # await example_basic_detection()
    print("(Requires network access to external sites)")

    print("\n\nExample 2: Focused Testing")
    print("=" * 50)
    print("(Requires local test server running)")
    # await example_focused_testing()

    print("\n\nExample 3: Report Generation")
    print("=" * 50)
    print("(Requires network access)")
    # await example_report_generation()

    print("\n\nExample 4: Continuous Monitoring")
    print("=" * 50)
    print("(Requires network access to multiple sites)")
    # await example_continuous_monitoring()

    print("\n\n✓ Examples completed")
    print("\nNote: Run actual examples in an environment with:")
    print("  - Network access to test servers")
    print("  - API keys configured in .env files")
    print("  - Playwright browsers installed (npx playwright install)")


if __name__ == "__main__":
    asyncio.run(main())
