#!/bin/bash

###############################################################################
# Comprehensive QA Suite Runner
# Orchestrates Selenium, Pytest, and Allure reporting
###############################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QA_DIR="$PROJECT_ROOT/qa"
ALLURE_RESULTS="$PROJECT_ROOT/allure-results"
ALLURE_REPORT="$PROJECT_ROOT/allure-report"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Comprehensive QA Suite${NC}"
echo -e "${BLUE}  Selenium + Pytest + Allure${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Parse arguments
TEST_TYPE="${1:-all}"
HEADLESS="${HEADLESS:-true}"

# Export headless mode
export HEADLESS=$HEADLESS

echo -e "${YELLOW}[QA Suite] Test Type: $TEST_TYPE${NC}"
echo -e "${YELLOW}[QA Suite] Headless Mode: $HEADLESS${NC}\n"

# 1. Clean previous results
echo -e "${BLUE}[1/5] Cleaning previous test results...${NC}"
rm -rf "$ALLURE_RESULTS" "$ALLURE_REPORT"
mkdir -p "$ALLURE_RESULTS"
echo -e "${GREEN}✓ Cleaned${NC}\n"

# 2. Run E2E tests (Playwright + Vitest)
echo -e "${BLUE}[2/5] Running E2E Tests (Playwright)...${NC}"
cd "$PROJECT_ROOT"
if npm run test:e2e 2>&1 | tee qa-e2e-results.log; then
    echo -e "${GREEN}✓ E2E Tests Passed${NC}\n"
else
    echo -e "${RED}✗ E2E Tests Failed (see qa-e2e-results.log)${NC}\n"
fi

# 3. Run Selenium UI tests
echo -e "${BLUE}[3/5] Running Selenium UI Tests...${NC}"
cd "$PROJECT_ROOT"

case $TEST_TYPE in
    all)
        echo -e "${YELLOW}   Running all Selenium tests...${NC}"
        python -m pytest qa/ -v --alluredir="$ALLURE_RESULTS" 2>&1 | tee qa/qa-selenium-results.log
        PYTEST_EXIT="${PIPESTATUS[0]}"
        ;;
    smoke)
        echo -e "${YELLOW}   Running smoke tests only...${NC}"
        python -m pytest qa/ -v -m smoke --alluredir="$ALLURE_RESULTS" 2>&1 | tee qa/qa-selenium-results.log
        PYTEST_EXIT="${PIPESTATUS[0]}"
        ;;
    selenium)
        echo -e "${YELLOW}   Running Selenium tests only...${NC}"
        python -m pytest qa/selenium/ -v --alluredir="$ALLURE_RESULTS" 2>&1 | tee qa/qa-selenium-results.log
        PYTEST_EXIT="${PIPESTATUS[0]}"
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo -e "${YELLOW}Usage: $0 [all|smoke|selenium]${NC}"
        exit 1
        ;;
esac

if [ "${PYTEST_EXIT}" -eq 0 ]; then
    echo -e "${GREEN}✓ Selenium Tests Passed${NC}\n"
else
    echo -e "${YELLOW}⚠ Selenium Tests Completed (see qa-selenium-results.log)${NC}\n"
fi

# 4. Generate Allure report
echo -e "${BLUE}[4/5] Generating Allure Report...${NC}"
if command -v allure &> /dev/null; then
    allure generate "$ALLURE_RESULTS" -o "$ALLURE_REPORT" --clean
    echo -e "${GREEN}✓ Allure Report Generated${NC}"
    echo -e "${YELLOW}   📊 Report location: $ALLURE_REPORT/index.html${NC}\n"
else
    echo -e "${RED}✗ Allure CLI not found. Install with: npm install -g allure${NC}\n"
fi

# 5. Summary
echo -e "${BLUE}[5/5] QA Suite Summary${NC}"
echo -e "${YELLOW}   📋 E2E Test Log: qa-e2e-results.log${NC}"
echo -e "${YELLOW}   📋 Selenium Log: qa-selenium-results.log${NC}"
echo -e "${YELLOW}   📊 Results Dir: $ALLURE_RESULTS${NC}"
echo -e "${YELLOW}   📊 Report Dir: $ALLURE_REPORT${NC}\n"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ QA Suite Complete${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Open report if available
if [ -f "$ALLURE_REPORT/index.html" ]; then
    echo -e "${YELLOW}Next: Open Allure report:${NC}"
    echo -e "${YELLOW}   ${GREEN}open $ALLURE_REPORT/index.html${NC}"
    echo -e "${YELLOW}   or${NC}"
    echo -e "${YELLOW}   ${GREEN}allure open $ALLURE_REPORT${NC}\n"
fi
