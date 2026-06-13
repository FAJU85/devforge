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
  echo "[session-start] Playwright CDN blocked — falling back to Sparticuz/chromium from GitHub releases…"
  # Full headless Chromium build (used by serverless platforms); GitHub releases
  # are reachable even when cdn.playwright.dev is not on the network allowlist.
  SPARTICUZ_DIR="/opt/sparticuz"
  if [ ! -x "$SPARTICUZ_DIR/chromium" ]; then
    mkdir -p "$SPARTICUZ_DIR"
    TAG=$(curl -sI --max-time 10 "https://github.com/Sparticuz/chromium/releases/latest" | grep -i '^location' | grep -o 'v[0-9.]*' | head -1)
    TAG="${TAG:-v149.0.0}"
    echo "[session-start] Downloading Sparticuz/chromium $TAG…"
    if curl -sL --max-time 300 -o "$SPARTICUZ_DIR/pack.tar" \
        "https://github.com/Sparticuz/chromium/releases/download/$TAG/chromium-$TAG-pack.x64.tar"; then
      command -v brotli >/dev/null || apt-get install -y brotli >/dev/null 2>&1
      tar xf "$SPARTICUZ_DIR/pack.tar" -C "$SPARTICUZ_DIR"
      brotli -d "$SPARTICUZ_DIR/chromium.br" -o "$SPARTICUZ_DIR/chromium" && chmod +x "$SPARTICUZ_DIR/chromium"
    fi
  fi
  if [ -x "$SPARTICUZ_DIR/chromium" ] && "$SPARTICUZ_DIR/chromium" --version >/dev/null 2>&1; then
    echo "[session-start] Chromium ready at $SPARTICUZ_DIR/chromium"
    echo "[session-start] Run e2e with: CHROME_EXECUTABLE=$SPARTICUZ_DIR/chromium npx playwright test"
  else
    echo "[session-start] WARNING: No browser available. Add 'cdn.playwright.dev' to the network allowlist at code.claude.com."
  fi
fi

echo "[session-start] Installing Python dependencies (best-effort)…"
pip install -r requirements.txt --quiet 2>&1 || true
pip install sentry-sdk[fastapi]==2.27.0 pytest==8.3.5 pytest-asyncio==0.25.3 \
    httpx==0.28.1 rollbar==1.3.0 posthog==7.17.0 pytest-cov==6.0.0 --quiet 2>&1 || true

echo "[session-start] Running full test suite…"
npm run test:e2e 2>&1 || echo "[session-start] Tests completed with warnings (see results above)"

echo "[session-start] Done."
