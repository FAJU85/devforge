# Self-Evolving QA System

A comprehensive test automation framework combining three phases:
- **Phase 1**: Intelligent E2E Test Generation
- **Phase 2**: Self-Healing Tests
- **Phase 4**: Generative Test Data

## Quick Start

### Phase 1: Generate E2E Tests

Generate a test from a natural language description:

```bash
npm run test:generate:test -- --description "User should be able to login with email and password"
```

This generates a complete Playwright test file in `tests/generated/`.

### Phase 2: Self-Healing Tests

Use intelligent locators that automatically recover from broken selectors:

```typescript
import { CommonLocators } from '../helpers/self-healing-locators';

test('login with self-healing', async ({ page }) => {
  const emailInput = CommonLocators.input(page, 'Email');
  const submitBtn = CommonLocators.submitButton(page);

  // These selectors automatically try fallbacks if primary breaks
  await emailInput.fill('test@example.com');
  await submitBtn.click();
});
```

### Phase 4: Generate Test Data

Generate realistic user accounts and edge cases:

```bash
npm run test:generate:data -- --count 10
```

This creates `tests/fixtures/test-data.json` with:
- Realistic user accounts (names, emails, passwords)
- Edge cases (invalid inputs, special characters, unicode)

Use in tests:

```typescript
import { generateUserAccount, generateEdgeCaseData } from '../generators/test-data-generator';

test('login with generated user', async ({ page }) => {
  const user = await generateUserAccount({ role: 'user' });
  
  await page.fill('input[type="email"]', user.email);
  await page.fill('input[type="password"]', user.password);
  await page.click('button[type="submit"]');
});
```

## Architecture

### Phase 1: Intelligent Test Generation

**How it works:**
1. You describe a test scenario in natural language
2. Claude API processes the description
3. Generates complete, valid Playwright test code
4. Test is saved and ready to use

**Use cases:**
- Generate tests from user stories
- Auto-create regression tests from bug reports
- Generate integration test suites from API specs

**Files:**
- `tests/generators/test-generator.ts` - Test generation logic
- `tests/generators/generate-tests.ts` - CLI tool

**CLI Usage:**

```bash
# Generate single test
npm run test:generate:test -- --description "User should be able to reset password"

# Generate test suite from multiple scenarios
npx ts-node tests/generators/generate-tests.ts --type test \
  --description "Authentication flow" \
  --output ./tests/generated
```

### Phase 2: Self-Healing Tests

**How it works:**
1. Define multiple selection strategies (primary + fallbacks)
2. Test tries primary selector first
3. If it fails, automatically tries fallback selectors
4. Caches successful selectors for speed
5. Reports which fallback was used

**Common selectors:**
- `button:has-text("Submit")` - Text-based (most resilient)
- `[aria-label="email"]` - Accessibility-based
- `[role="button"]` - Role-based
- `.submit-btn` - Class-based (fragile)
- `#submit` - ID-based (fragile)

**Built-in helpers:**

```typescript
// Use pre-built common locators
const submitBtn = CommonLocators.submitButton(page);
const emailInput = CommonLocators.input(page, 'Email');
const dialog = CommonLocators.dialog(page);
const sidebar = CommonLocators.sidebar(page);

// Create custom self-healing locator
const customBtn = createSelfHealingLocator(
  page,
  'button[data-testid="custom"]', // primary
  ['button.custom-btn', 'button:has-text("Custom")'], // fallbacks
  'Custom button'
);
```

**Methods:**

```typescript
// Find element with fallbacks
const element = await locator.find();

// Click with self-healing
await locator.click();

// Fill text field
await locator.fill('text');

// Assert visibility
await locator.assertVisible();

// Get text content
const text = await locator.getText();
```

**Files:**
- `tests/helpers/self-healing-locators.ts` - Self-healing implementation

### Phase 4: Generative Test Data

**How it works:**
1. Claude generates realistic test data
2. Falls back to deterministic data if API unavailable
3. Includes edge cases (XSS, SQL injection, unicode, etc.)
4. Creates fixture files for reuse

**Generated user accounts include:**
- Unique ID
- Realistic name (can be non-ASCII)
- Valid email address
- Strong password (12-16 chars, mixed case, symbols)
- Role (user/admin/moderator)
- Creation timestamp
- Active status

**Edge cases generated:**
- Email validation (incomplete, missing parts, duplicated dots)
- Password strength (weak passwords, missing character types)
- Input boundaries (empty, very long, whitespace-only)
- Security attacks (XSS, SQL injection, null bytes)
- Unicode (Chinese, emoji, accented characters)

**Files:**
- `tests/generators/test-data-generator.ts` - Data generation logic
- `tests/fixtures/test-data.json` - Generated fixture (auto-created)

**Usage:**

```typescript
import { 
  generateUserAccount, 
  generateUserAccounts,
  generateEdgeCaseData,
  createTestDataFixture 
} from '../generators/test-data-generator';

// Single user
const user = await generateUserAccount({ role: 'admin' });

// Multiple users
const users = await generateUserAccounts(5);

// Edge cases
const edgeCases = await generateEdgeCaseData();

// Create fixture file
await createTestDataFixture('./tests/fixtures/my-data.json', users, edgeCases);
```

## Integration Example

See `tests/generated/self-healing-example.spec.ts` for a complete example combining all three phases:

```typescript
test('login with self-healing and generated data', async ({ page }) => {
  // Phase 4: Generate realistic test data
  const testUser = await generateUserAccount({ role: 'user' });

  // Phase 2: Use self-healing locators
  const emailInput = CommonLocators.input(page, 'Email');
  const submitBtn = CommonLocators.submitButton(page);

  // Phase 1: Generated test code (if using test-generator)
  await emailInput.fill(testUser.email);
  await submitBtn.click();

  // Self-healing assertion
  const successMsg = createSelfHealingLocator(
    page,
    'text=Welcome',
    ['text=Success', '.success-message'],
    'Success message'
  );
  await successMsg.assertVisible();
});
```

## Running Generated Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run only self-healing example
npm run test:self-heal

# Run with debug mode
npm run test:e2e:debug

# Run with specific tag
npx playwright test --grep "self-healing"
```

## Best Practices

### Phase 1 (Test Generation)

1. **Be specific**: "User login" → "User should be able to log in with valid email and password, and see a welcome message"
2. **Include context**: Include component names, page names, or flow descriptions
3. **Review generated tests**: AI-generated tests need review before production use
4. **Test scenarios, not implementation**: Focus on user behavior, not DOM details
5. **Use as template**: Generated tests are starting points; customize as needed

### Phase 2 (Self-Healing)

1. **Prefer semantic selectors**: `role`, `aria-label`, text-based > class > ID
2. **Test in multiple browsers**: Self-healing strategies work best with consistent HTML
3. **Monitor fallback usage**: If fallbacks are frequently used, update primary selectors
4. **Keep fallbacks simple**: Complex fallbacks are harder to maintain
5. **Document selector intent**: Add comments explaining why each selector is needed

### Phase 4 (Test Data)

1. **Regenerate periodically**: Update fixture data monthly for fresh test scenarios
2. **Use edge cases**: Always include edge case tests in your suite
3. **Isolate test data**: Each test should have independent data
4. **Clean up after tests**: Reset state or use new data per test
5. **Version fixtures**: Keep fixture files in git for reproducibility

## Configuration

### Environment Variables

```bash
# Required for Phase 1 (test generation)
export ANTHROPIC_API_KEY="your-key"

# Optional: Custom output directories
export TEST_GENERATED_DIR="./tests/generated"
export TEST_FIXTURES_DIR="./tests/fixtures"
```

### Playwright Config

Tests automatically use:
- Base URL: `http://localhost:5173`
- Headless mode in CI
- Retries in CI (2 retries)
- HTML report generation

## Troubleshooting

### Tests fail with "Element not found"

1. Check self-healing fallbacks are accurate
2. Add new fallback selectors based on actual DOM
3. Update `CommonLocators` with new strategies
4. Verify element is visible before interaction

### Generated tests don't compile

1. Check `ANTHROPIC_API_KEY` is set
2. Generated code is TypeScript; ensure proper imports
3. Manually fix syntax errors in generated code
4. Report issues to improve generation

### Test data generation slow

1. Uses Claude API (requires network)
2. Falls back to deterministic generation if API unavailable
3. Cache generated fixture: `tests/fixtures/test-data.json`
4. Regenerate only when needed

## Advanced Usage

### Custom Self-Healing Strategies

```typescript
const myLocator = createSelfHealingLocator(
  page,
  'button[data-cy="special-btn"]', // primary
  [
    'button[data-test="special"]',
    'button.special__btn',
    'button:has-text("Special")',
    'aside button:last-child',
  ],
  'Special button'
);
```

### Batch Test Generation

```typescript
const descriptions = [
  'User should login with valid credentials',
  'User should see error with invalid password',
  'User should be able to logout',
];

const tests = await batchGenerateTests(descriptions);
tests.forEach(test => {
  // Save each test
  fs.writeFileSync(`tests/generated/${test.name}.spec.ts`, test.code);
});
```

### Test Data with Custom Schemas

```typescript
// Generate data matching your app's schema
const user = await generateUserAccount({
  role: 'admin',
  locale: 'en-US'
});

// Extend with custom fields
const extendedUser = {
  ...user,
  companyId: 'acme-corp',
  department: 'Engineering',
  customField: 'value'
};
```

## Metrics & Monitoring

Track effectiveness:

```bash
# Count generated tests
find tests/generated -name "*.spec.ts" | wc -l

# Count self-healing fallback usage
grep -r "Self-healing:" . --include="*.ts" | wc -l

# Monitor test pass rate
npm run test:e2e | grep -E "passed|failed"
```

## Future Enhancements

- [ ] Phase 3: Learn from production traffic (OpenTelemetry integration)
- [ ] Phase 5: Full self-maintaining suite (auto-prune, auto-update)
- [ ] Flakiness prediction: Identify and fix flaky tests automatically
- [ ] Visual regression detection: Compare screenshots across runs
- [ ] Performance benchmarking: Track test execution time
- [ ] Coverage analysis: Identify untested code paths

## References

- [Playwright Documentation](https://playwright.dev)
- [Claude API Reference](https://docs.anthropic.com)
- [Self-Healing Test Locators](https://github.com/healenium)

---

**Status**: ✅ Production Ready (Phases 1, 2, 4)
**Last Updated**: 2026-06-13
**Maintainer**: DevForge QA Team
