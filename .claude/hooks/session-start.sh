#!/bin/bash

# Only run in remote Claude Code on the web environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

echo "[session-start] Installing npm dependencies…"
npm install --prefer-offline 2>&1 || npm install 2>&1

echo "[session-start] Installing Playwright Chromium browser…"
if npx playwright install chromium 2>&1; then
  echo "[session-start] Playwright Chromium installed successfully."
else
  echo "[session-start] WARNING: Playwright browser download failed."
  echo "[session-start] Add 'cdn.playwright.dev' to your environment's network allowlist at code.claude.com."
fi

echo "[session-start] Installing Python dependencies (best-effort)…"
pip install -r requirements.txt --quiet 2>&1 || true
pip install sentry-sdk[fastapi]==2.27.0 pytest==8.3.5 pytest-asyncio==0.25.3 \
    httpx==0.28.1 rollbar==1.3.0 posthog==7.17.0 pytest-cov==6.0.0 --quiet 2>&1 || true

echo "[session-start] Done."
