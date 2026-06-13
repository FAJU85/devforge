import React from 'react';
import { Code2, ExternalLink, Copy } from 'lucide-react';

export default function APIPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
          API Documentation
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          Access DevForge agents and services via REST APIs
        </p>
      </div>

      {/* API Services */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <APIService
          title="Agent Orchestration"
          port="8001"
          description="High-level task execution"
          status="online"
        />
        <APIService
          title="Browser Control"
          port="8002"
          description="Low-level browser automation"
          status="online"
        />
        <APIService
          title="Task Orchestrator"
          port="8003"
          description="Task coordination and monitoring"
          status="online"
        />
      </div>

      {/* Documentation Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Start */}
        <DocumentationSection title="Quick Start">
          <CodeBlock
            language="bash"
            code={`# Start all APIs
bash scripts/start-agents-api.sh

# Health check
curl http://localhost:8001/health

# Create task
curl -X POST http://localhost:8001/api/agents/browser/task \\
  -H "Content-Type: application/json" \\
  -d '{
    "description": "Navigate to example.com",
    "url": "https://example.com"
  }'`}
          />
        </DocumentationSection>

        {/* Python Client */}
        <DocumentationSection title="Python Client">
          <CodeBlock
            language="python"
            code={`from ml.orchestrator_client import get_client

# Create client
client = get_client()

# Generate test
result = client.generate_test_sync(
    "Test login functionality",
    "http://localhost:3000/login"
)

# Check status
stats = client.get_stats()`}
          />
        </DocumentationSection>
      </div>

      {/* Endpoints Reference */}
      <div className="dev-card">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Key Endpoints
        </h2>
        <div className="space-y-3">
          <EndpointItem
            method="POST"
            path="/api/agents/browser/task"
            description="Execute browser automation"
          />
          <EndpointItem
            method="POST"
            path="/api/agents/test-generator/generate"
            description="Generate tests from description"
          />
          <EndpointItem
            method="POST"
            path="/api/agents/bug-detector/scan"
            description="Scan website for bugs"
          />
          <EndpointItem
            method="GET"
            path="/api/tasks/{task_id}"
            description="Get task status and result"
          />
          <EndpointItem
            method="GET"
            path="/api/stats"
            description="Get platform statistics"
          />
        </div>
      </div>

      {/* Links */}
      <div className="dev-card">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Resources
        </h2>
        <div className="space-y-3">
          <Link href="http://localhost:8001/docs" label="Agent API Docs (Swagger)" />
          <Link href="http://localhost:8002/docs" label="Browser API Docs (Swagger)" />
          <Link href="http://localhost:8003/docs" label="Orchestrator Docs (Swagger)" />
          <Link href="/docs/API_ORCHESTRATION_GUIDE.md" label="Full API Guide" />
        </div>
      </div>
    </div>
  );
}

function APIService({ title, port, description, status }) {
  const isOnline = status === 'online';
  return (
    <div className="dev-card">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white">
            {title}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            {description}
          </p>
        </div>
        <div
          className={`w-3 h-3 rounded-full ${
            isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}
        />
      </div>
      <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-700">
        <code className="text-sm text-[#76cd1d] font-mono">
          localhost:{port}
        </code>
        <a
          href={`http://localhost:${port}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#76cd1d] hover:text-[#63b50f] transition flex items-center gap-1"
        >
          <span className="text-xs">Docs</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}

function DocumentationSection({ title, children }) {
  return (
    <div className="dev-card">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
        <Code2 className="w-5 h-5" />
        {title}
      </h2>
      {children}
    </div>
  );
}

function CodeBlock({ language, code }) {
  return (
    <div className="relative">
      <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-xs font-mono">
        <code>{code}</code>
      </pre>
      <button className="absolute top-3 right-3 p-2 bg-slate-800 hover:bg-slate-700 rounded transition">
        <Copy className="w-4 h-4 text-slate-400" />
      </button>
    </div>
  );
}

function EndpointItem({ method, path, description }) {
  const methodColor = {
    POST: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    GET: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    PUT: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
    DELETE: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
  };

  return (
    <div className="flex items-start gap-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
      <span
        className={`px-2 py-1 rounded text-xs font-bold whitespace-nowrap ${
          methodColor[method]
        }`}
      >
        {method}
      </span>
      <div className="flex-1">
        <code className="text-sm text-slate-900 dark:text-white font-mono block">
          {path}
        </code>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
          {description}
        </p>
      </div>
    </div>
  );
}

function Link({ href, label }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition text-slate-900 dark:text-white font-medium"
    >
      <span>{label}</span>
      <ExternalLink className="w-4 h-4 ml-auto text-slate-600 dark:text-slate-400" />
    </a>
  );
}
