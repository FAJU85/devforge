# DevForge Development & Operations Guide

## Environment Setup

### Quick Start
```bash
# Health check
node scripts/health-check.js

# View metrics
node scripts/metrics.js

# Run tests
npm run test

# Start dev server
npm run dev
```

## E2E Testing

### Playwright Tests
```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test e2e/workflow.spec.ts

# Debug mode
npx playwright test --debug

# Generate HTML report
npx playwright test --reporter=html
```

## Code Quality (SDLC)

### Python
```bash
# Format code
black api/ tests/

# Lint
flake8 api/ tests/

# Type check
mypy api/

# Auto-import sort
isort api/ tests/
```

### TypeScript/React
```bash
# Format
prettier --write components/

# Lint
eslint components/ --ext .ts,.tsx

# Type check
tsc --noEmit
```

## Testing Coverage

### Run with Coverage
```bash
# Python
pytest --cov=api --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

## SRE & Monitoring

### Health Checks
```bash
# Full system health
node scripts/health-check.js

# Quick metrics
node scripts/metrics.js
```

### Logging & Debugging
```bash
# View app logs
tail -f /var/log/devforge.log

# Python debug mode
PYTHONVERBOSE=1 python main.py

# React dev tools
# Install React Developer Tools browser extension
```

## CI/CD Pipeline

### Local CI Simulation
```bash
# Run full CI suite
npm run lint
npm run type-check
npm run test
pytest tests/ --cov

# Build for production
npm run build
```

## Performance Monitoring

### Baseline Metrics
- API Response: <200ms
- Model Generation: <30s per model
- Streaming: Real-time (NDJSON)
- Session Load: <100ms

### Profiling
```bash
# Python profiling
python -m cProfile main.py

# Memory profiling
pip install memory_profiler
python -m memory_profiler main.py
```

## Database Migrations

```bash
# Run pending migrations
cd alembic
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## Troubleshooting

### Tests Failing
1. Check git status: `git status`
2. Run health check: `node scripts/health-check.js`
3. Clear cache: `rm -rf .next node_modules/.cache`
4. Reinstall: `npm ci`

### App Import Error
```bash
# Verify Python environment
python -c "import main"

# Check dependencies
pip list
npm list
```

### Network Issues
- Check sandbox network policy
- Use local-only services
- Verify localhost:3000 is accessible

## Deployment Checklist

- [ ] All tests passing (42/42)
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Code coverage >70%
- [ ] Health check passing
- [ ] Git status clean
- [ ] Environment variables set
- [ ] Database migrations current

