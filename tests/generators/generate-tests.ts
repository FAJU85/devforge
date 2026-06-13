#!/usr/bin/env node

/**
 * CLI: Generate E2E tests and test data
 * Usage:
 *   npx ts-node tests/generators/generate-tests.ts --type test --description "..."
 *   npx ts-node tests/generators/generate-tests.ts --type data --count 10
 */

import { generateE2ETest, generateTestSuite } from './test-generator';
import { generateUserAccounts, generateEdgeCaseData, createTestDataFixture } from './test-data-generator';
import * as fs from 'fs';
import * as path from 'path';

interface CommandOptions {
  type: 'test' | 'data' | 'both';
  description?: string;
  count?: number;
  output?: string;
}

async function main() {
  const args = process.argv.slice(2);
  const options = parseArgs(args);

  console.log('🚀 Test Generator CLI');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  try {
    if (options.type === 'test' || options.type === 'both') {
      await generateTests(options);
    }

    if (options.type === 'data' || options.type === 'both') {
      await generateData(options);
    }

    console.log('✅ Generation complete!');
  } catch (error) {
    console.error('❌ Generation failed:', error);
    process.exit(1);
  }
}

async function generateTests(options: CommandOptions): Promise<void> {
  console.log('\n📝 Generating E2E Tests...');

  if (!options.description) {
    console.warn('⚠️  No description provided. Skipping test generation.');
    return;
  }

  try {
    const test = await generateE2ETest({
      description: options.description,
    });

    const outputDir = options.output || './tests/generated';
    const fileName = `generated-${Date.now()}.spec.ts`;
    const filePath = path.join(outputDir, fileName);

    // Create directory if it doesn't exist
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Wrap in test file structure
    const testContent = wrapInTestFile(test.code, test.name, test.tags);

    fs.writeFileSync(filePath, testContent);

    console.log(`✅ Test generated: ${filePath}`);
    console.log(`   Tags: ${test.tags.join(', ')}`);
    console.log(`   Lines: ${test.code.split('\n').length}`);
  } catch (error) {
    console.error('❌ Test generation failed:', error);
    throw error;
  }
}

async function generateData(options: CommandOptions): Promise<void> {
  console.log('\n📊 Generating Test Data...');

  try {
    const count = options.count || 5;

    const users = await generateUserAccounts(count);
    const edgeCases = await generateEdgeCaseData();

    const outputDir = options.output || './tests/fixtures';
    const filePath = path.join(outputDir, 'test-data.json');

    await createTestDataFixture(filePath, users, edgeCases);

    console.log(`✅ Test data generated: ${filePath}`);
    console.log(`   Users: ${users.length}`);
    console.log(`   Edge cases: ${edgeCases.length}`);
  } catch (error) {
    console.error('❌ Data generation failed:', error);
    throw error;
  }
}

function parseArgs(args: string[]): CommandOptions {
  const options: CommandOptions = {
    type: 'both',
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case '--type':
        options.type = args[++i] as 'test' | 'data' | 'both';
        break;
      case '--description':
        options.description = args[++i];
        break;
      case '--count':
        options.count = parseInt(args[++i], 10);
        break;
      case '--output':
        options.output = args[++i];
        break;
      case '--help':
        printHelp();
        process.exit(0);
    }
  }

  return options;
}

function wrapInTestFile(code: string, name: string, tags: string[]): string {
  const timestamp = new Date().toISOString();

  return `/**
 * Generated E2E Test
 * Name: ${name}
 * Tags: ${tags.join(', ')}
 * Generated: ${timestamp}
 *
 * This test was automatically generated. Review and adjust as needed.
 */

import { test, expect } from '@playwright/test';
import { CommonLocators, createSelfHealingLocator } from '../helpers/self-healing-locators';
import { generateUserAccount, generateEdgeCaseData } from '../generators/test-data-generator';

${code}
`;
}

function printHelp(): void {
  console.log(`
Usage: npx ts-node tests/generators/generate-tests.ts [options]

Options:
  --type <type>           test | data | both (default: both)
  --description <desc>    Description for test generation
  --count <n>             Number of users to generate (default: 5)
  --output <path>         Output directory (default: ./tests/generated or ./tests/fixtures)
  --help                  Show this help message

Examples:
  # Generate a single test
  npx ts-node tests/generators/generate-tests.ts --type test --description "User login flow"

  # Generate test data
  npx ts-node tests/generators/generate-tests.ts --type data --count 20

  # Generate everything
  npx ts-node tests/generators/generate-tests.ts --type both
`);
}

main().catch(console.error);
