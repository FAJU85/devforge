/**
 * Generative Test Data Generator
 * Creates realistic synthetic user accounts and edge case data
 */

import Anthropic from '@anthropic-ai/sdk';

export interface UserAccount {
  id: string;
  name: string;
  email: string;
  password: string;
  role: 'user' | 'admin' | 'moderator';
  isActive: boolean;
  createdAt: string;
  metadata?: Record<string, any>;
}

export interface EdgeCaseData {
  type: string;
  value: any;
  description: string;
  expectedBehavior: string;
}

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || '',
});

/**
 * Generate realistic user account with AI
 */
export async function generateUserAccount(
  options?: { role?: string; locale?: string }
): Promise<UserAccount> {
  try {
    const prompt = buildUserPrompt(options);
    const message = await client.messages.create({
      model: 'claude-opus-4-8',
      max_tokens: 512,
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    });

    const responseText =
      message.content[0].type === 'text' ? message.content[0].text : '';

    return parseUserAccount(responseText);
  } catch (error) {
    console.warn('AI user generation failed, using fallback:', error);
    return generateUserAccountFallback(options);
  }
}

/**
 * Generate multiple realistic user accounts
 */
export async function generateUserAccounts(
  count: number = 5,
  options?: { role?: string; locale?: string }
): Promise<UserAccount[]> {
  const users: UserAccount[] = [];

  for (let i = 0; i < count; i++) {
    try {
      const user = await generateUserAccount(options);
      users.push(user);
    } catch (error) {
      console.warn(`Failed to generate user ${i + 1}, using fallback`);
      users.push(generateUserAccountFallback(options));
    }
  }

  return users;
}

/**
 * Generate edge case test data
 */
export async function generateEdgeCaseData(): Promise<EdgeCaseData[]> {
  const edgeCases: EdgeCaseData[] = [];

  const categories = [
    'email validation',
    'password strength',
    'input boundaries',
    'special characters',
    'unicode handling',
  ];

  for (const category of categories) {
    try {
      const prompt = buildEdgeCasePrompt(category);
      const message = await client.messages.create({
        model: 'claude-opus-4-8',
        max_tokens: 512,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
      });

      const responseText =
        message.content[0].type === 'text' ? message.content[0].text : '';

      const cases = parseEdgeCases(responseText, category);
      edgeCases.push(...cases);
    } catch (error) {
      console.warn(`Failed to generate edge cases for ${category}:`, error);
    }
  }

  // Add deterministic edge cases
  edgeCases.push(
    ...getStaticEdgeCases()
  );

  return edgeCases;
}

/**
 * Build prompt for user generation
 */
function buildUserPrompt(
  options?: { role?: string; locale?: string }
): string {
  return `Generate a realistic test user account in JSON format.

Requirements:
1. Name: realistic and diverse (can include non-ASCII characters)
2. Email: valid format, realistic domain
3. Password: 12-16 characters, strong (mix of upper, lower, numbers, symbols)
4. Role: ${options?.role || 'user'} (or random if not specified)
5. isActive: boolean
6. createdAt: ISO 8601 timestamp (within last year)
7. id: unique UUID-like string

Return ONLY valid JSON, no markdown or explanation:
{
  "id": "...",
  "name": "...",
  "email": "...",
  "password": "...",
  "role": "...",
  "isActive": true,
  "createdAt": "..."
}`;
}

/**
 * Build prompt for edge case data
 */
function buildEdgeCasePrompt(category: string): string {
  return `Generate 3 edge case test values for "${category}" in JSON array format.

For each case include:
- type: string (data type)
- value: the test value
- description: what makes it an edge case
- expectedBehavior: what should happen when tested

Examples of good edge cases:
- Empty strings, very long strings, only whitespace
- Invalid emails like "test@", "@example.com"
- Passwords without special chars, all symbols, SQL injection attempts
- Numbers at boundaries: -1, 0, max integer
- Unicode: emojis, RTL text, combining characters
- Special characters: <>, ", ', backslash, null bytes

Return ONLY valid JSON array, no markdown:
[
  {
    "type": "string",
    "value": "...",
    "description": "...",
    "expectedBehavior": "..."
  },
  ...
]`;
}

/**
 * Parse user account from JSON response
 */
function parseUserAccount(jsonString: string): UserAccount {
  try {
    const user = JSON.parse(jsonString);
    return {
      id: user.id || generateId(),
      name: user.name || 'Test User',
      email: user.email || 'test@example.com',
      password: user.password || 'SecurePass123!',
      role: user.role || 'user',
      isActive: user.isActive !== false,
      createdAt: user.createdAt || new Date().toISOString(),
      metadata: user.metadata || {},
    };
  } catch {
    console.error('Failed to parse user JSON');
    return generateUserAccountFallback();
  }
}

/**
 * Parse edge cases from JSON response
 */
function parseEdgeCases(jsonString: string, category: string): EdgeCaseData[] {
  try {
    const cases = JSON.parse(jsonString);
    if (!Array.isArray(cases)) {
      return [];
    }
    return cases.map((c) => ({
      type: c.type || 'unknown',
      value: c.value,
      description: c.description || `Edge case for ${category}`,
      expectedBehavior: c.expectedBehavior || 'Should handle gracefully',
    }));
  } catch {
    console.error('Failed to parse edge cases JSON');
    return [];
  }
}

/**
 * Fallback user generation (deterministic)
 */
function generateUserAccountFallback(options?: {
  role?: string;
  locale?: string;
}): UserAccount {
  const timestamp = Date.now();
  const names = [
    'Alice Johnson',
    'Bob Smith',
    'Charlie Brown',
    'Diana Prince',
    'Eve Wilson',
  ];
  const name = names[Math.floor(Math.random() * names.length)];

  return {
    id: generateId(),
    name,
    email: `${name.toLowerCase().replace(' ', '.')}+${timestamp}@example.com`,
    password: `SecurePass${timestamp}!`,
    role: (options?.role || 'user') as 'user' | 'admin' | 'moderator',
    isActive: true,
    createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
  };
}

/**
 * Get static edge cases (always reliable)
 */
function getStaticEdgeCases(): EdgeCaseData[] {
  return [
    // Email validation
    {
      type: 'email',
      value: 'test@',
      description: 'Incomplete email address',
      expectedBehavior: 'Should reject as invalid',
    },
    {
      type: 'email',
      value: '@example.com',
      description: 'Missing local part',
      expectedBehavior: 'Should reject as invalid',
    },
    {
      type: 'email',
      value: 'test..dot@example.com',
      description: 'Consecutive dots',
      expectedBehavior: 'Should reject or sanitize',
    },

    // Password strength
    {
      type: 'password',
      value: '123456',
      description: 'Numbers only, too short',
      expectedBehavior: 'Should reject as weak',
    },
    {
      type: 'password',
      value: 'abcdef',
      description: 'Lowercase only',
      expectedBehavior: 'Should reject as weak',
    },
    {
      type: 'password',
      value: 'ABCDEF',
      description: 'Uppercase only',
      expectedBehavior: 'Should reject as weak',
    },

    // Input boundaries
    {
      type: 'string',
      value: '',
      description: 'Empty string',
      expectedBehavior: 'Should reject or show validation error',
    },
    {
      type: 'string',
      value: ' '.repeat(1000),
      description: 'Very long whitespace',
      expectedBehavior: 'Should be trimmed or rejected',
    },
    {
      type: 'number',
      value: -1,
      description: 'Negative number where positive expected',
      expectedBehavior: 'Should reject or handle gracefully',
    },

    // Special characters
    {
      type: 'string',
      value: '<script>alert("xss")</script>',
      description: 'XSS injection attempt',
      expectedBehavior: 'Should be escaped or rejected',
    },
    {
      type: 'string',
      value: "'; DROP TABLE users; --",
      description: 'SQL injection attempt',
      expectedBehavior: 'Should be escaped or rejected',
    },
    {
      type: 'string',
      value: 'test\0null',
      description: 'Null byte injection',
      expectedBehavior: 'Should be sanitized',
    },

    // Unicode & internationalization
    {
      type: 'string',
      value: '你好世界',
      description: 'Chinese characters',
      expectedBehavior: 'Should be accepted and displayed correctly',
    },
    {
      type: 'string',
      value: '🚀🎉💯',
      description: 'Emoji characters',
      expectedBehavior: 'Should be accepted or rejected consistently',
    },
    {
      type: 'string',
      value: 'café',
      description: 'Accented characters',
      expectedBehavior: 'Should be handled correctly in storage and display',
    },
  ];
}

/**
 * Generate unique ID
 */
function generateId(): string {
  return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create test data fixture file
 */
export async function createTestDataFixture(
  filePath: string,
  users: UserAccount[] = [],
  edgeCases: EdgeCaseData[] = []
): Promise<void> {
  const fixture = {
    users: users.length > 0 ? users : await generateUserAccounts(5),
    edgeCases: edgeCases.length > 0 ? edgeCases : await generateEdgeCaseData(),
    generated: new Date().toISOString(),
  };

  const fs = await import('fs').then((m) => m.promises);
  const path = await import('path');

  const dir = path.dirname(filePath);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(fixture, null, 2));

  console.log(`✅ Test data fixture created: ${filePath}`);
}

export default {
  generateUserAccount,
  generateUserAccounts,
  generateEdgeCaseData,
  createTestDataFixture,
};
