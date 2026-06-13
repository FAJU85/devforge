/**
 * Intelligent E2E Test Generator
 * Generates Playwright E2E test scenarios from descriptions, user stories, or component specs
 */

import Anthropic from '@anthropic-ai/sdk';

interface TestGenerationRequest {
  description: string;
  component?: string;
  scenario?: string;
  context?: string;
}

interface GeneratedTest {
  name: string;
  code: string;
  tags: string[];
}

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || '',
});

/**
 * Generate E2E test from natural language description
 */
export async function generateE2ETest(
  request: TestGenerationRequest
): Promise<GeneratedTest> {
  const prompt = buildPrompt(request);

  try {
    const message = await client.messages.create({
      model: 'claude-opus-4-8',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    });

    const responseText =
      message.content[0].type === 'text' ? message.content[0].text : '';

    return parseGeneratedTest(responseText, request);
  } catch (error) {
    console.error('Test generation failed:', error);
    throw error;
  }
}

/**
 * Generate multiple test scenarios from a feature description
 */
export async function generateTestSuite(
  featureDescription: string,
  scenarios: string[]
): Promise<GeneratedTest[]> {
  const tests: GeneratedTest[] = [];

  for (const scenario of scenarios) {
    const test = await generateE2ETest({
      description: featureDescription,
      scenario,
    });
    tests.push(test);
  }

  return tests;
}

/**
 * Build the prompt for test generation
 */
function buildPrompt(request: TestGenerationRequest): string {
  return `Generate a Playwright E2E test based on the following:

Description: ${request.description}
${request.component ? `Component: ${request.component}` : ''}
${request.scenario ? `Scenario: ${request.scenario}` : ''}
${request.context ? `Context: ${request.context}` : ''}

Requirements for the generated test:
1. Use Playwright test syntax (@playwright/test)
2. Include proper setup with test.beforeEach for navigation
3. Use semantic selectors (role-based, label-based, text-based) when possible
4. Include helpful comments explaining the test logic
5. Add clear assertions with descriptive messages
6. Handle both success and failure cases
7. Include proper error handling and visibility checks
8. Make tests independent and idempotent

Return ONLY valid TypeScript/JavaScript test code that can be directly used with Playwright.
No markdown, no code blocks, just the code.

Example format:
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test('should do something', async ({ page }) => {
    const element = page.locator('button:has-text("Click me")');
    await expect(element).toBeVisible();
    await element.click();
    await expect(page.locator('text=Success')).toBeVisible();
  });
});`;
}

/**
 * Parse generated test code and extract metadata
 */
function parseGeneratedTest(
  code: string,
  request: TestGenerationRequest
): GeneratedTest {
  // Extract test name from description or scenario
  const testName =
    request.scenario || request.description.split('\n')[0].slice(0, 50);

  // Extract tags from description keywords
  const tags: string[] = [];
  if (request.description.toLowerCase().includes('form'))
    tags.push('form');
  if (request.description.toLowerCase().includes('button'))
    tags.push('button');
  if (request.description.toLowerCase().includes('error'))
    tags.push('error-handling');
  if (request.description.toLowerCase().includes('validation'))
    tags.push('validation');
  if (request.description.toLowerCase().includes('accessibility'))
    tags.push('a11y');

  return {
    name: testName,
    code,
    tags,
  };
}

/**
 * Batch generate tests from multiple descriptions
 */
export async function batchGenerateTests(
  descriptions: string[]
): Promise<GeneratedTest[]> {
  const tests: GeneratedTest[] = [];

  for (const description of descriptions) {
    try {
      const test = await generateE2ETest({ description });
      tests.push(test);
    } catch (error) {
      console.warn(
        `Failed to generate test for "${description}":`,
        error
      );
    }
  }

  return tests;
}

export default {
  generateE2ETest,
  generateTestSuite,
  batchGenerateTests,
};
