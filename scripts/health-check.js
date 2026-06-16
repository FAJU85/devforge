#!/usr/bin/env node
/**
 * Health Check Script
 * Verifies application readiness and critical system status
 */

const http = require('http');
const fs = require('fs');

async function checkHealth() {
  console.log('🏥 DevForge Health Check\n');

  const checks = {
    'App Import': async () => {
      try {
        require('../main.py'); // Would need adjustment for Python
        return { pass: true, msg: 'App imports successfully' };
      } catch (e) {
        return { pass: false, msg: `Import failed: ${e.message}` };
      }
    },
    
    'Test Suite': async () => {
      try {
        const result = require('child_process').execSync(
          'python -m pytest tests/test_multi_model_endpoint.py -q',
          { encoding: 'utf8' }
        );
        return { pass: result.includes('passed'), msg: 'Tests passing' };
      } catch (e) {
        return { pass: false, msg: 'Tests failing' };
      }
    },

    'Source Files': async () => {
      const files = [
        'api/routes/generate.py',
        'components/generate/CodeGeneratorPage.tsx',
        'main.py'
      ];
      const missing = files.filter(f => !fs.existsSync(f));
      return {
        pass: missing.length === 0,
        msg: missing.length ? `Missing: ${missing.join(', ')}` : 'All source files present'
      };
    },

    'Dependencies': async () => {
      const nodeModules = fs.existsSync('node_modules');
      const pythonEnv = fs.existsSync('.venv') || process.env.VIRTUAL_ENV;
      return {
        pass: nodeModules,
        msg: nodeModules ? 'Dependencies installed' : 'Missing node_modules'
      };
    }
  };

  let passed = 0;
  for (const [name, check] of Object.entries(checks)) {
    try {
      const result = await check();
      const icon = result.pass ? '✓' : '✗';
      console.log(`${icon} ${name}: ${result.msg}`);
      if (result.pass) passed++;
    } catch (e) {
      console.log(`✗ ${name}: ${e.message}`);
    }
  }

  console.log(`\n${passed}/${Object.keys(checks).length} checks passed\n`);
  process.exit(passed === Object.keys(checks).length ? 0 : 1);
}

checkHealth().catch(console.error);
