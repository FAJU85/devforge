# Development Environment & SDLC Guide

This document describes the comprehensive development environment setup for DevForge, including E2E testing, code quality tools, and SRE/observability.

## Quick Start

Install dependencies and initialize git hooks:

```bash
make install
make health
```

Run tests and check code quality:

```bash
make test
make lint
make format
```

## E2E Testing Tools

### Playwright (Primary)
Browser automation testing across Chrome, Firefox, Safari.

```bash
npm run test:e2e              # Run E2E tests in headless mode
npm run test:e2e:headed       # Run with visible browser
npm run test:e2e:debug        # Debug in inspector mode
```

Configuration: `playwright.config.ts`  
Test files: `e2e/**/*.spec.ts`

### Vitest (Unit & Integration)
Fast, Vite-native test runner for component and unit testing.

```bash
npm run test:unit             # Run unit tests once
npm run test:component        # Run component tests
npm run test:ui               # Interactive UI test runner
npm run test:unit:coverage    # Coverage report
```

Configuration: `vite.config.ts` with Vitest settings  
Test files: `tests/**/*.test.ts`

## SDLC Tools (Code Quality)

### Python Code Quality

#### Formatting & Linting

```bash
make format                   # Format Python code (Black + isort)
make lint                     # Lint Python (Ruff)
make typecheck                # Type checking (mypy)
```

Tools:
- **Black**: Deterministic code formatter
- **isort**: Import sorting (PEP 8)
- **Ruff**: Fast Python linter (replaces Flake8)
- **mypy**: Static type checker

Configuration: `pyproject.toml`

#### Pre-commit Hooks

```bash
pre-commit install            # Install git hooks
pre-commit run --all-files    # Run hooks on all files
```

Hooks configured in `.pre-commit-config.yaml`:
- Black formatting
- isort import sorting
- Ruff linting & formatting
- mypy type checking
- YAML/JSON validation
- Private key detection

### JavaScript/TypeScript Code Quality

#### Formatting

```bash
npm run format                # Format with Prettier
```

Configuration: `.prettierrc.json`  
Prettier formats TypeScript, JSX, CSS, JSON.

#### Linting

```bash
npm run lint                  # ESLint (via package.json scripts)
```

Configuration: `.eslintrc.json`

#### Type Checking

```bash
npm run typecheck             # TypeScript compiler check
```

Configuration: `tsconfig.json`

## Testing & Coverage

### Full Test Suite

```bash
make test                     # Run all test suites
npm run test:all              # Node + E2E tests
```

### Coverage Reports

```bash
npm run test:unit:coverage    # Unit test coverage
```

Coverage thresholds in `vitest.config.ts`.

## Health Checks & Metrics

### Health Endpoints

Once the app is running, health checks are available at:

```bash
curl http://localhost:8000/health           # Full health status
curl http://localhost:8000/health/live      # Liveness probe
curl http://localhost:8000/health/ready     # Readiness probe
curl http://localhost:8000/metrics          # Prometheus metrics
```

### Health Check Script

```bash
node scripts/health-check.js  # Verify app readiness
```

Checks:
- Python app imports
- Test suite status
- Required source files
- Dependencies installed

### Metrics Script

```bash
node scripts/metrics.js       # Report code & project metrics
```

Reports:
- Lines of code (backend, frontend)
- Test count
- Git commit history
- Performance baselines

## SRE & Observability

### Structured Logging

Logs are output as JSON for easy parsing:

```json
{
  "timestamp": "2026-06-16T10:30:45.123456",
  "level": "INFO",
  "logger": "devforge",
  "message": "Application started",
  "module": "main",
  "function": "startup",
  "line": 245
}
```

### Prometheus Metrics

The `/metrics` endpoint exposes metrics in Prometheus format:

```
devforge_uptime_seconds 3600.5
devforge_requests_total 1250
devforge_errors_total 3
devforge_request_duration_ms 45.2
devforge_memory_usage_mb 128.4
```

### HTTP Request Logging

All HTTP requests/responses are logged with:
- Method, path, status code
- Client IP
- Duration (milliseconds)
- Error details on failure

Example log:
```json
{
  "type": "http_response",
  "method": "POST",
  "path": "/api/generate/code-parallel",
  "status": 200,
  "duration_ms": 2345.67
}
```

## Development Workflow

### 1. Before First Commit

```bash
# Install dependencies and git hooks
make install

# Run full quality gate
make lint
make format
make typecheck
make test
make health
```

### 2. During Development

```bash
# Start dev servers (Node + Python in parallel)
make dev

# Watch tests in foreground
npm run test:unit:watch

# Check types while editing (optional)
npm run typecheck
```

### 3. Before Pushing Code

```bash
# Format code
make format

# Run linter
make lint

# Run tests
make test

# Verify health
make health
```

### 4. Git Workflow

```bash
# Pre-commit hooks automatically run on `git commit`
# They will:
# - Format code with Black
# - Sort imports with isort
# - Lint with Ruff
# - Check types with mypy
# - Validate YAML/JSON

git add src/myfile.py
git commit -m "Add new feature"  # Hooks run here

# If hooks fail, fix and re-commit
```

## Continuous Integration

### CI/CD Pipeline Simulation

```bash
make ci                       # Run full CI pipeline locally
```

Equivalent to:
```bash
npm install
python -m pip install -r requirements.txt
make lint
make typecheck
make test
make health
```

## Deployment Checklist

Before deploying to production:

- [ ] All tests passing locally: `make test`
- [ ] No lint errors: `make lint`
- [ ] Type checks passing: `make typecheck`
- [ ] Health checks passing: `make health`
- [ ] Environment variables set (`.env`)
- [ ] Database migrations applied
- [ ] Feature flags configured
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

## Troubleshooting

### Pre-commit hooks failing

If pre-commit hooks block a commit:

```bash
# View which hooks failed
pre-commit run --all-files

# Run a specific hook manually
pre-commit run black --all-files

# Skip hooks (only for emergency; not recommended)
git commit --no-verify
```

### Tests failing after dependency changes

```bash
# Clear Node cache and reinstall
rm -rf node_modules
npm install

# Clear Python cache and reinstall
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Health checks failing

```bash
# Check what's failing
make health

# Verify dependencies
make lint
npm list

# Check environment variables
env | grep -E "GITHUB|HF_|SENTRY|ROLLBAR"
```

## Common Commands

| Task | Command |
|------|---------|
| Install dependencies | `make install` |
| Format code | `make format` |
| Lint code | `make lint` |
| Run unit tests | `make test` |
| Run E2E tests | `npm run test:e2e` |
| Type checking | `make typecheck` |
| Full CI pipeline | `make ci` |
| Health check | `make health` |
| Metrics report | `make metrics` |
| Start dev server | `make dev` |
| Clean build artifacts | `make clean` |

## References

- **Playwright**: https://playwright.dev/
- **Vitest**: https://vitest.dev/
- **Black**: https://black.readthedocs.io/
- **Ruff**: https://docs.astral.sh/ruff/
- **mypy**: https://mypy.readthedocs.io/
- **Prettier**: https://prettier.io/
- **ESLint**: https://eslint.org/
- **pre-commit**: https://pre-commit.com/
- **Prometheus**: https://prometheus.io/docs/instrumenting/exposition_formats/
