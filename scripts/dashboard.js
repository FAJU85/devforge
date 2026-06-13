#!/usr/bin/env node

/**
 * QA Learning Dashboard Server
 * Serves the interactive dashboard for viewing learned patterns
 * Run: npm run qa:dashboard
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const os = require('os');

const DASHBOARD_PATH = path.join(__dirname, '../qa/learning/dashboard.html');
const PATTERNS_PATH = path.join(__dirname, '../qa/learning/learned_patterns.json');
const PORT = 3333;

// Create server
const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Serve dashboard HTML
  if (req.url === '/' || req.url === '/dashboard') {
    res.setHeader('Content-Type', 'text/html');
    try {
      const html = fs.readFileSync(DASHBOARD_PATH, 'utf8');
      res.writeHead(200);
      res.end(html);
    } catch (err) {
      res.writeHead(404);
      res.end(`<h1>Dashboard Not Found</h1><p>${err.message}</p>`);
    }
    return;
  }

  // Serve patterns JSON
  if (req.url === '/learned_patterns.json') {
    res.setHeader('Content-Type', 'application/json');
    try {
      const patterns = fs.readFileSync(PATTERNS_PATH, 'utf8');
      res.writeHead(200);
      res.end(patterns);
    } catch (err) {
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'Patterns file not found', message: err.message }));
    }
    return;
  }

  // Default: redirect to dashboard
  res.setHeader('Location', '/');
  res.writeHead(302);
  res.end();
});

// Start server
server.listen(PORT, '127.0.0.1', () => {
  const url = `http://127.0.0.1:${PORT}`;

  console.log('\n' + '='.repeat(70));
  console.log('\x1b[1m🎯 QA Learning Dashboard\x1b[0m');
  console.log('='.repeat(70));
  console.log(`\n✓ Dashboard running at: \x1b[36m${url}\x1b[0m`);
  console.log('✓ Press Ctrl+C to stop\n');

  // Try to open in browser (gracefully fail if not possible)
  const platform = os.platform();
  let openCommand;

  if (platform === 'win32') {
    openCommand = `start "${url}"`;
  } else if (platform === 'darwin') {
    openCommand = `open "${url}"`;
  } else {
    // Linux - try common browsers
    openCommand = `xdg-open "${url}" || sensible-browser "${url}" || echo "Open ${url} in your browser"`;
  }

  exec(openCommand, (err) => {
    if (err && !err.code) {
      console.log(`📱 Open your browser to: ${url}\n`);
    }
  });
});

// Error handling
server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`\n❌ Error: Port ${PORT} is already in use\n`);
    console.log('Try:');
    console.log(`  - Kill existing process: lsof -ti:${PORT} | xargs kill -9`);
    console.log(`  - Use different port: PORT=3334 npm run qa:dashboard\n`);
  } else {
    console.error(`\n❌ Server error: ${err.message}\n`);
  }
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n✓ Dashboard stopped\n');
  process.exit(0);
});
