#!/usr/bin/env python3
"""
Bug Detection Agent - Detects bugs through web interaction
Uses Anthropic Claude to analyze web behavior and find issues
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
class Bug:
    """Represents a detected bug"""
    id: str
    severity: str  # critical, high, medium, low
    category: str  # crash, performance, ui, logic, security
    description: str
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str
    screenshot: Optional[str] = None  # base64 encoded


class BugDetectionAgent:
    """AI-powered bug detection agent using Claude"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=self.api_key)
        self.browser = None
        self.page = None
        self.detected_bugs = []
        self.interaction_history = []

    async def start(self):
        """Start browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv('HEADLESS', 'true').lower() == 'true'
        )
        self.page = await self.browser.new_page()
        print("✓ Bug detector browser started")

    async def stop(self):
        """Stop browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        print("✓ Bug detector browser stopped")

    async def get_page_analysis(self) -> Dict[str, Any]:
        """Get comprehensive page analysis for bug detection"""
        try:
            analysis = await self.page.evaluate("""() => {
                const bugs = [];
                const warnings = [];

                // Check console errors
                window.__errors = window.__errors || [];

                // Check for broken elements
                const imgs = document.querySelectorAll('img');
                imgs.forEach(img => {
                    if (!img.complete || img.naturalHeight === 0) {
                        bugs.push({
                            type: 'broken_image',
                            src: img.src,
                            element: img.className
                        });
                    }
                });

                // Check for missing alt text (accessibility)
                imgs.forEach(img => {
                    if (!img.alt && img.src) {
                        warnings.push({
                            type: 'missing_alt_text',
                            src: img.src
                        });
                    }
                });

                // Check for broken links
                const links = document.querySelectorAll('a');
                links.forEach(link => {
                    if (!link.href || link.href === '#' || link.href === '') {
                        warnings.push({
                            type: 'broken_link',
                            text: link.innerText
                        });
                    }
                });

                // Check for form issues
                const forms = document.querySelectorAll('form');
                forms.forEach(form => {
                    const inputs = form.querySelectorAll('input, textarea, select');
                    inputs.forEach(input => {
                        if (!input.name && input.type !== 'hidden') {
                            warnings.push({
                                type: 'unnamed_form_field',
                                type_attr: input.type
                            });
                        }
                    });
                });

                return {
                    title: document.title,
                    url: document.URL,
                    bugs: bugs,
                    warnings: warnings,
                    elements_count: document.querySelectorAll('*').length,
                    has_errors: window.__errors && window.__errors.length > 0,
                    errors: window.__errors || []
                };
            }""")
            return analysis
        except Exception as e:
            print(f"✗ Page analysis failed: {e}")
            return {}

    async def detect_bugs(
        self,
        url: str,
        test_cases: List[str] = None,
        max_interactions: int = 10
    ) -> Dict:
        """
        Detect bugs by interacting with a web application

        Args:
            url: URL to test
            test_cases: List of test scenarios to try
            max_interactions: Maximum interactions to perform

        Returns:
            Dictionary with detected bugs
        """
        if not self.page:
            await self.start()

        self.detected_bugs = []
        self.interaction_history = []

        print(f"\n🔍 Detecting bugs at {url}\n")

        # Navigate to URL
        try:
            await self.page.goto(url, timeout=30000)
            print("✓ Page loaded")
        except Exception as e:
            return {
                "status": "failed",
                "error": f"Failed to load page: {e}"
            }

        # Analyze initial state
        page_analysis = await self.get_page_analysis()

        # Take screenshot
        screenshot = base64.b64encode(
            await self.page.screenshot()
        ).decode('utf-8')

        # Build context for Claude
        context = f"""You are a QA specialist analyzing a web application for bugs.

URL: {url}
Page Title: {page_analysis.get('title', 'Unknown')}

Initial Page Analysis:
{json.dumps(page_analysis, indent=2)}

Test Cases to Try:
{json.dumps(test_cases or ['Basic interaction test'], indent=2)}

Based on the page structure and test cases, what interactions would best help find bugs?
Suggest 5 specific user interactions to try.

Respond with ONLY valid JSON:
{{
    "suggested_interactions": ["interaction 1", "interaction 2", ...],
    "potential_issues": ["issue 1", "issue 2", ...],
    "areas_of_concern": ["area 1", "area 2", ...]
}}"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": context
            }]
        )

        response_text = response.content[0].text

        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {"suggested_interactions": [], "potential_issues": []}

        # Try suggested interactions
        for idx, interaction in enumerate(analysis.get('suggested_interactions', [])[:max_interactions]):
            interaction_num = idx + 1
            print(f"Interaction {interaction_num}: {interaction}")

            # Simulate interaction (in real scenario, would parse and execute)
            # For now, just wait and capture state
            await asyncio.sleep(1)

            # Take screenshot after interaction
            try:
                post_interaction_screenshot = base64.b64encode(
                    await self.page.screenshot()
                ).decode('utf-8')
                post_analysis = await self.get_page_analysis()

                self.interaction_history.append({
                    "interaction": interaction,
                    "page_state": post_analysis,
                    "screenshot": post_interaction_screenshot
                })
            except Exception as e:
                print(f"  ⚠ Failed to capture state: {e}")

        # Analyze findings with Claude
        findings_context = f"""Based on your analysis, here are the findings from testing {url}:

Initial State:
{json.dumps(page_analysis, indent=2)}

Test Interactions Performed:
{json.dumps([h['interaction'] for h in self.interaction_history], indent=2)}

Potential Issues Found:
{json.dumps(analysis.get('potential_issues', []), indent=2)}

Please identify and categorize any bugs found. For each bug, provide:
- Severity (critical/high/medium/low)
- Category (crash/performance/ui/logic/security)
- Clear description
- Steps to reproduce
- Expected vs actual behavior

Respond with ONLY valid JSON:
{{
    "bugs": [
        {{
            "id": "BUG-001",
            "severity": "high",
            "category": "ui",
            "description": "...",
            "steps": ["step 1", "step 2"],
            "expected": "...",
            "actual": "..."
        }}
    ],
    "summary": "...",
    "recommendations": ["rec 1", "rec 2"]
}}"""

        findings_response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": findings_context
            }]
        )

        findings_text = findings_response.content[0].text

        try:
            findings = json.loads(findings_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', findings_text, re.DOTALL)
            if json_match:
                findings = json.loads(json_match.group())
            else:
                findings = {"bugs": [], "summary": "Analysis complete", "recommendations": []}

        # Create Bug objects
        bugs = []
        for bug_data in findings.get('bugs', []):
            bug = Bug(
                id=bug_data.get('id', 'UNKNOWN'),
                severity=bug_data.get('severity', 'medium'),
                category=bug_data.get('category', 'logic'),
                description=bug_data.get('description', ''),
                steps_to_reproduce=bug_data.get('steps', []),
                expected_behavior=bug_data.get('expected', ''),
                actual_behavior=bug_data.get('actual', ''),
                screenshot=screenshot
            )
            bugs.append(bug)
            self.detected_bugs.append(bug)

        return {
            "status": "success",
            "url": url,
            "bugs_found": len(bugs),
            "bugs": [
                {
                    "id": bug.id,
                    "severity": bug.severity,
                    "category": bug.category,
                    "description": bug.description,
                    "steps": bug.steps_to_reproduce,
                    "expected": bug.expected_behavior,
                    "actual": bug.actual_behavior
                }
                for bug in bugs
            ],
            "summary": findings.get('summary', ''),
            "recommendations": findings.get('recommendations', []),
            "interactions_count": len(self.interaction_history)
        }

    def export_report(self, format: str = "json") -> str:
        """
        Export bug detection report

        Args:
            format: Report format (json, html, markdown)

        Returns:
            Formatted report string
        """
        if format == "json":
            return json.dumps({
                "bugs": [{
                    "id": bug.id,
                    "severity": bug.severity,
                    "category": bug.category,
                    "description": bug.description,
                    "steps": bug.steps_to_reproduce,
                    "expected": bug.expected_behavior,
                    "actual": bug.actual_behavior
                } for bug in self.detected_bugs],
                "total_bugs": len(self.detected_bugs),
                "severity_breakdown": {
                    "critical": len([b for b in self.detected_bugs if b.severity == "critical"]),
                    "high": len([b for b in self.detected_bugs if b.severity == "high"]),
                    "medium": len([b for b in self.detected_bugs if b.severity == "medium"]),
                    "low": len([b for b in self.detected_bugs if b.severity == "low"])
                }
            }, indent=2)

        elif format == "markdown":
            report = "# Bug Detection Report\n\n"
            for bug in self.detected_bugs:
                report += f"## {bug.id}: {bug.description}\n"
                report += f"**Severity**: {bug.severity} | **Category**: {bug.category}\n\n"
                report += f"**Steps to Reproduce**:\n"
                for step in bug.steps_to_reproduce:
                    report += f"- {step}\n"
                report += f"\n**Expected**: {bug.expected_behavior}\n"
                report += f"**Actual**: {bug.actual_behavior}\n\n"
            return report

        return json.dumps({"error": "Unknown format"})


# Example usage
async def main():
    agent = BugDetectionAgent()
    await agent.start()

    # Example: Detect bugs on a website
    result = await agent.detect_bugs(
        url="https://www.example.com",
        test_cases=[
            "Load the homepage",
            "Click on links",
            "Check for broken images",
            "Test form submission"
        ]
    )

    print(f"\n{result}")

    if result['status'] == 'success':
        print(f"\n✓ Found {result['bugs_found']} bugs:")
        for bug in result['bugs']:
            print(f"  - {bug['id']}: {bug['description']} ({bug['severity']})")

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
