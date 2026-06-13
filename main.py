from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Callable, List, Optional
import ast as _ast
import json, os, requests, base64, re, asyncio, threading, secrets, time
from urllib.parse import quote as _urlquote
from concurrent.futures import ThreadPoolExecutor, as_completed as _futs_done

# Load .env file when running locally (no-op if file doesn't exist)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from anthropic import Anthropic
from huggingface_hub import InferenceClient

# Phase 5 - Dashboard Routes
try:
    from api.routes.auth import router as auth_router
    from api.routes.chat import router as chat_router
    from api.routes.config import router as config_router
    from api.routes.repositories import router as repositories_router
    from api.routes.tasks import router as tasks_router
    _DASHBOARD_ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Dashboard routes unavailable: {e}")
    _DASHBOARD_ROUTES_AVAILABLE = False

# WebSocket support
try:
    from fastapi import WebSocket, WebSocketDisconnect
    from api.websocket import connection_manager, initialize_task_broadcast
    _WEBSOCKET_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] WebSocket support unavailable: {e}")
    _WEBSOCKET_AVAILABLE = False
    connection_manager = None
    initialize_task_broadcast = None

# Optional: Sentry error monitoring (backend + request tracing)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration
    _SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
    if _SENTRY_DSN:
        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment=os.environ.get("ENVIRONMENT", "production"),
        )
except ImportError:
    pass

# Optional: Rollbar error monitoring (backend exceptions + frontend JS errors)
try:
    import rollbar
    _ROLLBAR_TOKEN = os.environ.get("ROLLBAR_ACCESS_TOKEN", "")
    _ROLLBAR_ENV = os.environ.get("ROLLBAR_ENVIRONMENT", "production")
    if _ROLLBAR_TOKEN:
        rollbar.init(
            _ROLLBAR_TOKEN,
            _ROLLBAR_ENV,
            handler="thread",
            allow_logging_basic_config=False,
        )
    else:
        _ROLLBAR_TOKEN = ""
except ImportError:
    _ROLLBAR_TOKEN = ""

# Optional: PostHog product analytics (server-side event capture)
try:
    import posthog as _posthog_sdk
    _POSTHOG_KEY = os.environ.get("POSTHOG_API_KEY", "")
    _POSTHOG_PROJECT_ID = os.environ.get("POSTHOG_PROJECT_ID", "")
    if _POSTHOG_KEY:
        _posthog_sdk.project_api_key = _POSTHOG_KEY
        _posthog_sdk.host = "https://us.i.posthog.com"
        _posthog_sdk.disabled = False
    else:
        _posthog_sdk = None
except ImportError:
    _posthog_sdk = None
    _POSTHOG_KEY = ""
    _POSTHOG_PROJECT_ID = ""

# Optional: control-plane (LangGraph + Pinecone + Go data-plane integration)
try:
    from control_plane.graph import build_graph as _build_langgraph
    from control_plane.memory.pinecone_client import (
        query_context as _pinecone_query,
        upsert_text as _pinecone_upsert,
    )
    _CONTROL_PLANE_AVAILABLE = True
except Exception:
    _CONTROL_PLANE_AVAILABLE = False
    def _build_langgraph(): return None  # noqa: E301
    def _pinecone_query(q: str, top_k: int = 3) -> str: return ""  # noqa: E301
    def _pinecone_upsert(text: str, metadata=None) -> bool: return False  # noqa: E301

# Optional: Database v2 API (PostgreSQL-backed endpoints)
try:
    from api_v2 import router as v2_router
    _DB_API_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Database API v2 unavailable: {e}")
    _DB_API_AVAILABLE = False

app = FastAPI(title="DevForge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include v2 API router (database-backed endpoints)
if _DB_API_AVAILABLE:
    app.include_router(v2_router)

# Include Phase 5 Dashboard routes
if _DASHBOARD_ROUTES_AVAILABLE:
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(config_router)
    app.include_router(repositories_router)
    app.include_router(tasks_router)

# Initialize WebSocket-Task integration
if _WEBSOCKET_AVAILABLE and initialize_task_broadcast:
    initialize_task_broadcast()

# WebSocket endpoint for real-time updates
if _WEBSOCKET_AVAILABLE:
    @app.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """
        WebSocket endpoint for real-time communication

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()
        await connection_manager.connect(user_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                await connection_manager.handle_message(user_id, message_data)
        except WebSocketDisconnect:
            await connection_manager.disconnect(user_id, websocket)
        except Exception as e:
            print(f"WebSocket error for user {user_id}: {e}")
            await connection_manager.disconnect(user_id, websocket)

    @app.get("/api/websocket/stats")
    async def get_websocket_stats():
        """Get WebSocket connection statistics"""
        return connection_manager.get_connection_stats()


@app.middleware("http")
async def _rollbar_middleware(request, call_next):
    """Report unhandled exceptions to Rollbar with request context."""
    try:
        return await call_next(request)
    except Exception as exc:
        if _ROLLBAR_TOKEN:
            try:
                import rollbar
                rollbar.report_exc_info(
                    extra_data={
                        "path": str(request.url.path),
                        "method": request.method,
                    }
                )
            except Exception:
                pass
        raise


@app.middleware("http")
async def _security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    # X-Frame-Options omitted — app runs inside HF Spaces iframe
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-XSS-Protection", "0")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return response


@app.middleware("http")
async def _feature_flag_middleware(request, call_next):
    """Add feature flag status to response headers."""
    from feature_flags import is_db_sync_enabled

    response = await call_next(request)

    # Extract user ID from request (GitHub login or IP)
    user_id = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or "anonymous"

    # Check if DB sync is enabled for this user/request
    db_enabled = is_db_sync_enabled(user_id)
    response.headers["X-DB-Enabled"] = "true" if db_enabled else "false"

    return response


def _emit_posthog_metrics(user_id: str, flag_buckets: dict, path: str, status_code: int, latency_ms: float) -> None:
    """Best-effort PostHog capture for each active flag bucket on API paths."""
    if not (flag_buckets and _posthog_sdk and path.startswith("/api/")):
        return
    for flag_name, bucket in flag_buckets.items():
        try:
            _posthog_sdk.capture(
                distinct_id=user_id or "anonymous",
                event="request_completed",
                properties={
                    "flag": flag_name,
                    "bucket": bucket,
                    "latency_ms": round(latency_ms, 2),
                    "status_code": status_code,
                    "path": path,
                    "$process_person_profile": False,
                },
            )
        except Exception:
            pass


@app.middleware("http")
async def _flag_routing_middleware(request, call_next):
    """Assign flag cohort buckets per request and capture latency metrics to PostHog."""
    import time as _time
    start = _time.monotonic()
    user_id = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "")
    )
    try:
        active_flags = [
            f for f in _flags_mod.get_all()  # noqa: F821
            if f.get("enabled") and f.get("status") in ("canary", "live")
        ]
        flag_buckets: dict[str, str] = {}
        for flag in active_flags:
            is_canary = _flags_mod.is_flag_enabled(flag["name"], user_id)  # noqa: F821
            flag_buckets[flag["name"]] = "canary" if is_canary else "control"
    except Exception:
        flag_buckets = {}
    request.state.flag_buckets = flag_buckets
    request.state.user_id = user_id
    response = await call_next(request)
    latency_ms = (_time.monotonic() - start) * 1000.0
    _emit_posthog_metrics(user_id, flag_buckets, request.url.path, response.status_code, latency_ms)
    if flag_buckets:
        response.headers["X-Flag-Buckets"] = ",".join(f"{k}:{v}" for k, v in flag_buckets.items())
    return response


GITHUB_CLIENT_ID     = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
HF_TOKEN             = os.environ.get("HF_TOKEN", "")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "vooom")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "asd1234")


class AdminLoginBody(BaseModel):
    username: str
    password: str


# Brute-force protection: sliding window of failed attempts per client IP
_ADMIN_ATTEMPTS: dict = {}
_ADMIN_MAX_ATTEMPTS = 5
_ADMIN_WINDOW_SECS = 300


@app.post("/api/admin/login")
async def admin_login(body: AdminLoginBody, request: Request):
    """Simple admin auth — credentials configurable via ADMIN_USERNAME / ADMIN_PASSWORD env vars.

    Rate-limited to 5 failed attempts per 5 minutes per client IP; credential
    comparison is constant-time to avoid timing side channels.
    """
    import hmac as _hmac
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    attempts = [t for t in _ADMIN_ATTEMPTS.get(ip, []) if now - t < _ADMIN_WINDOW_SECS]
    if len(attempts) >= _ADMIN_MAX_ATTEMPTS:
        _ADMIN_ATTEMPTS[ip] = attempts
        return JSONResponse(
            {"ok": False, "error": "Too many attempts — try again in a few minutes"},
            status_code=429,
        )
    user_ok = _hmac.compare_digest(body.username.encode(), ADMIN_USERNAME.encode())
    pass_ok = _hmac.compare_digest(body.password.encode(), ADMIN_PASSWORD.encode())
    if user_ok and pass_ok:
        _ADMIN_ATTEMPTS.pop(ip, None)
        return {"ok": True}
    attempts.append(now)
    _ADMIN_ATTEMPTS[ip] = attempts
    return {"ok": False}

AGENT_PROMPTS = {
    "code":      "You are an expert coding agent. Write high-quality, production-ready code. Always show the full file path before every code block. Explain every change clearly.",
    "review":    "You are an expert code reviewer. Find bugs, security vulnerabilities, performance issues, and bad patterns. Give specific, actionable feedback with improved code snippets.",
    "architect": "You are a software architect. Design scalable, maintainable systems. Provide folder structures, interfaces, and tech decisions with clear reasoning.",
    "debug":     "You are a debugging specialist. Find root causes of errors. Provide complete, tested fixes with clear explanations.",
    "docs":      "You are a technical writer. Write clear, comprehensive documentation with usage examples, parameter descriptions, return values, and edge cases.",
    "refactor":  "You are a refactoring expert. Restructure code to improve readability, maintainability, and performance without changing behavior. Identify code smells, apply SOLID principles, extract methods, reduce complexity, and eliminate duplication. Always show the full file path before code blocks and explain each refactoring decision.",
    "testgen":   "You are a test generation expert. Write comprehensive test suites that cover all code paths. Include unit tests, integration tests, edge cases, and error conditions. Use the appropriate testing framework for the language. Show full file paths before every test file. Aim for high coverage and clear test names that document behavior.",
}

SECURITY_FOOTER = (
    "\n\n## Security Requirements (Non-Negotiable):\n"
    "• Never use eval(), exec(), os.system(), or any dynamic code execution\n"
    "• Never hardcode passwords, API keys, tokens, or secrets — use environment variables\n"
    "• Always validate and sanitize all user inputs before processing or storing\n"
    "• Use parameterized queries for all database operations — no string concatenation in SQL\n"
    "• Use HTTPS for all external connections\n"
    "• Catch specific exceptions — never swallow errors silently with bare except clauses"
)

SKILL_PROMPTS = {
    "go":       "SKILL - Go/Golang: Write idiomatic Go. Use explicit error returns (never panic for business logic), interfaces for abstraction, goroutines+channels for concurrency. Follow Go naming conventions. Prefer stdlib.",
    "zod":      "SKILL - Zod + TypeScript: Use Zod for ALL schema validation and type inference. Define z.object() schemas first, derive types with z.infer<typeof schema>. Validate all external/user data through Zod. Use strict TypeScript config.",
    "tests":    "SKILL - Testing: Always include comprehensive unit tests. Cover happy paths, edge cases, and error conditions. Use appropriate framework (Jest/Vitest for TS, testing package for Go, pytest for Python).",
    "errors":   "SKILL - Error Handling: Implement thorough error handling. Never silently swallow errors. Use typed/structured errors with context. Return errors up the call stack.",
    "security": "SKILL - Security: Validate and sanitize all inputs, use parameterized queries, implement proper auth checks, never log secrets, follow OWASP Top 10.",
    "docs":     "SKILL - Documentation: Add complete inline docs. JSDoc for TS/JS, GoDoc for Go, docstrings for Python. Document params, return values, errors, and include usage examples.",
    "perf":     "SKILL - Performance: Choose efficient data structures, minimize allocations, implement caching where beneficial, consider time/space complexity.",
    "solid":    "SKILL - SOLID + Clean Code: Apply SOLID principles. Keep functions small and focused. Prefer composition over inheritance. Use dependency injection.",
    "react":    "SKILL - React: Write modern functional React components with hooks. Use TypeScript strictly. Prefer named exports. Use React.memo / useMemo / useCallback only when profiling shows a need. Prefer controlled components. Separate concerns: keep UI, state, and side-effects in distinct layers.",
    "nextjs":   "SKILL - Next.js App Router: Use React Server Components by default. Add 'use client' only when you need interactivity or browser APIs. Use route handlers (app/api/) for API endpoints. Leverage Suspense and streaming. Use next/image, next/link, and next/font. Follow Vercel deployment best practices.",
    "docker":   "SKILL - Docker: Write minimal, layered Dockerfiles. Use multi-stage builds to keep images small. Pin base image versions. Run as non-root user. Use .dockerignore. Prefer COPY over ADD. Set explicit WORKDIR. Use health checks.",
    "sql":      "SKILL - SQL / Database: Write efficient, readable SQL. Use indexes on JOIN and WHERE columns. Avoid N+1 queries — use JOINs or batch loads. Use transactions for multi-step writes. Prefer parameterized queries. Add EXPLAIN ANALYZE comments for complex queries.",
}

MA_PLAN_SYSTEM   = "You are a software architect. Analyze the task and create a clear, concise step-by-step implementation plan. List files to create/modify, key functions, and potential pitfalls. Do NOT write actual code yet."
MA_CODE_SYSTEM   = "You are an expert coding agent. Implement the task following the provided plan. Write complete, production-ready code with full file paths before every code block."
MA_TEST_SYSTEM   = "You are a test engineer. Write comprehensive automated tests for the implementation provided. Include unit tests, edge cases, and error conditions. Show full file paths before every test file. Use the appropriate testing framework for the language (pytest, Jest/Vitest, Go testing, etc.)."
MA_REVIEW_SYSTEM = "You are a senior code reviewer. Review the implementation and tests for bugs, security issues, performance problems, missing error handling, and code quality. Be specific and constructive."

def _build_skills_section(skills: list) -> str:
    """Return the formatted skills block for the system prompt."""
    parts = ["\n\n## Active Skills:\n"]
    for s in skills:
        if s in SKILL_PROMPTS:
            parts.append(f"{SKILL_PROMPTS[s]}\n\n")
    return "".join(parts)


def _build_tools_section(tools: list) -> str:
    """Return the formatted tools block for the system prompt (non-Anthropic providers)."""
    lines = ["\n\n## Available Tools:\n"]
    for t in tools:
        lines.append(f"- **{t.name}**: {t.description} ({t.method} {t.url})\n")
    lines.append("\nDescribe needed tool calls in your response; the user will execute them and share results.")
    return "".join(lines)


def build_system(body: "ChatBody") -> str:
    """Compose the system prompt from agent, skills, rules, file context, and session memory."""
    if getattr(body, 'instructions', '') and body.instructions.strip():
        base = body.instructions.strip()
    else:
        base = AGENT_PROMPTS.get(body.agent, AGENT_PROMPTS["code"])
    if body.owner and body.repo:
        branch_info = f", branch: {body.branch}" if getattr(body, 'branch', '') else ""
        base += (
            f"\n\nRepository: {body.owner}/{body.repo}{branch_info}. "
            "Before EVERY code block that creates or modifies a file, place the full file path "
            "in a Markdown heading using inline code — e.g. `### \\`src/utils/api.ts\\``. "
            "Alternatively, write it as a comment on the very first line of the code block — "
            "e.g. `// src/components/Button.tsx` or `# app/models/user.py`. "
            "This enables one-click GitHub commit for each file. Always use full paths, never relative."
        )
    skills = getattr(body, 'skills', []) or []
    if skills:
        base += _build_skills_section(skills)
    rules = (getattr(body, 'rules', '') or '').strip()
    if rules:
        base += f"\n\n## Rules (must follow):\n{rules}"
    memory = (getattr(body, 'memory', '') or '').strip()
    if memory:
        base += f"\n\n## Previous Session Context (from last conversation on this repo):\n{memory}"
    tools = getattr(body, 'tools', []) or []
    if tools and body.provider != "anthropic":
        base += _build_tools_section(tools)
    if body.agent in ("code", "refactor", "testgen", "debug"):
        base += SECURITY_FOOTER
    fc = (getattr(body, 'file_context', '') or '').strip()
    if fc:
        base += f"\n\n---\n**Repository context:**\n{fc}"
    return base

_airllm_cache: dict = {}

def _build_airllm_prompt(tokenizer, system: str, messages: list) -> str:
    """Build a prompt string using the tokenizer's chat template or Llama-2 fallback."""
    chat_msgs = [{"role": "system", "content": system}] + messages
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None):
        return tokenizer.apply_chat_template(chat_msgs, tokenize=False, add_generation_prompt=True)
    prompt = f"[INST] <<SYS>>\n{system}\n<</SYS>>\n\n"
    for m in messages:
        if m["role"] == "user":
            prompt += f"{m['content']} [/INST] "
        elif m["role"] == "assistant":
            prompt += f"{m['content']} [INST] "
    return prompt


def _run_airllm(q, loop, system: str, messages: list, model_id: str, max_new_tokens: int = 512):
    """Thread target: run local inference via AirLLM (streams model layers from disk/CPU to GPU)."""
    try:
        try:
            from airllm import AutoModel
            import torch
        except ImportError:
            asyncio.run_coroutine_threadsafe(
                q.put(("error", "airllm not installed — run: pip install airllm")), loop
            )
            return
        if model_id not in _airllm_cache:
            asyncio.run_coroutine_threadsafe(
                q.put(("text", f"⏳ Loading **{model_id}** — first run downloads and caches the model, may take several minutes…\n\n")), loop
            )
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            _airllm_cache[model_id] = AutoModel.from_pretrained(model_id, device=device)
        model = _airllm_cache[model_id]
        tokenizer = model.tokenizer
        device = next(iter(model.parameters())).device if hasattr(model, "parameters") else "cpu"
        prompt = _build_airllm_prompt(tokenizer, system, messages)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        input_ids = inputs["input_ids"].to(device)
        input_len = input_ids.shape[-1]
        generation_output = model.generate(
            input_ids,
            max_new_tokens=max(1, min(int(max_new_tokens), 4096)),
            use_cache=True,
            return_dict_in_generate=True,
        )
        new_ids = generation_output.sequences[0][input_len:]
        result = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
        for i in range(0, max(len(result), 1), 8):
            chunk = result[i:i + 8]
            if chunk:
                asyncio.run_coroutine_threadsafe(q.put(("text", chunk)), loop)
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

def _friendly_anthropic_error(e: Exception) -> str:
    msg = str(e)
    if "401" in msg or "authentication_error" in msg or "invalid x-api-key" in msg.lower():
        return "Anthropic API key is invalid or missing. Check your key at console.anthropic.com."
    if "429" in msg or "rate_limit_error" in msg:
        return "Anthropic rate limit reached. Wait a moment and try again."
    if "529" in msg or "overloaded_error" in msg:
        return "Anthropic API is temporarily overloaded. Try again in a few seconds."
    if "403" in msg or "permission_error" in msg:
        return "Anthropic API key does not have permission for this model or feature."
    return msg

def _run_anthropic_thinking(q, loop, system, messages, api_key, model, thinking_budget):
    """Run Anthropic with extended thinking enabled; emits ('thinking', text) chunks."""
    try:
        client = Anthropic(api_key=api_key)
        actual_model = model or "claude-opus-4-8"
        budget = max(1024, min(int(thinking_budget or 2000), 16000))
        max_tokens = budget + 4096

        with client.messages.stream(
            model=actual_model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            thinking={"type": "enabled", "budget_tokens": budget},
        ) as stream:
            for event in stream:
                etype = getattr(event, 'type', None)
                if etype == 'content_block_delta':
                    delta = getattr(event, 'delta', None)
                    dtype = getattr(delta, 'type', None)
                    if dtype == 'thinking_delta':
                        asyncio.run_coroutine_threadsafe(
                            q.put(("thinking", getattr(delta, 'thinking', ''))), loop
                        )
                    elif dtype == 'text_delta':
                        asyncio.run_coroutine_threadsafe(
                            q.put(("text", getattr(delta, 'text', ''))), loop
                        )
            try:
                msg = stream.get_final_message()
                usage = {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}
                asyncio.run_coroutine_threadsafe(q.put(("usage", usage)), loop)
            except Exception:
                pass
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", _friendly_anthropic_error(e))), loop)

def _build_anth_tools(tools: list) -> list:
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema or {"type": "object", "properties": {}},
        }
        for t in tools
    ]


def _execute_http_tool(tool_def, block) -> str:
    if not re.match(r"^https?://", tool_def.url or ""):
        return "Error: Tool URL must start with http:// or https://"
    hdrs = dict(tool_def.headers or {})
    url = tool_def.url
    inp = block.input or {}
    for k, v in inp.items():
        url = url.replace(f"{{{k}}}", _urlquote(str(v), safe=""))
    method = (tool_def.method or "GET").upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return f"Error: Unsupported method {method}"
    if method == "GET":
        params = {k: v for k, v in inp.items() if f"{{{k}}}" not in tool_def.url}
        r = requests.get(url, headers=hdrs, params=params, timeout=15)
        return r.text[:2000]
    hdrs.setdefault("Content-Type", "application/json")
    r = requests.request(method, url, headers=hdrs, json=inp, timeout=15)
    return r.text[:2000]


def _execute_tool_call(block, tools: list) -> str:
    tool_def = next((t for t in tools if t.name == block.name), None)
    if not tool_def:
        return f"Error: Tool '{block.name}' not found"
    try:
        return _execute_http_tool(tool_def, block)
    except Exception as e:
        return f"Error: {e}"


def _collect_assistant_turn(msg) -> list:
    content = []
    for block in msg.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
    return content


def _run_anthropic_with_tools(q, loop, system, messages, api_key, tools, model="claude-sonnet-4-6"):
    """Run Anthropic with native tool use, executing HTTP calls and looping until done."""
    try:
        client = Anthropic(api_key=api_key)
        anth_tools = _build_anth_tools(tools)
        current_messages = list(messages)
        total_usage = {"input": 0, "output": 0}
        for _ in range(5):
            with client.messages.stream(
                model=model or "claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=current_messages,
                tools=anth_tools,
            ) as stream:
                for text in stream.text_stream:
                    asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
                msg = stream.get_final_message()
                try:
                    total_usage["input"] += msg.usage.input_tokens
                    total_usage["output"] += msg.usage.output_tokens
                except Exception:
                    pass
                if msg.stop_reason != "tool_use":
                    break
            current_messages.append({"role": "assistant", "content": _collect_assistant_turn(msg)})
            tool_results = []
            for block in msg.content:
                if block.type != "tool_use":
                    continue
                asyncio.run_coroutine_threadsafe(
                    q.put(("tool_call", {"id": block.id, "name": block.name, "input": block.input})), loop
                )
                result_content = _execute_tool_call(block, tools)
                asyncio.run_coroutine_threadsafe(
                    q.put(("tool_result", {"id": block.id, "name": block.name, "result": result_content})), loop
                )
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_content})
            current_messages.append({"role": "user", "content": tool_results})
        asyncio.run_coroutine_threadsafe(q.put(("usage", total_usage)), loop)
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", _friendly_anthropic_error(e))), loop)

def _run_anthropic(q, loop, system, messages, api_key, model="claude-sonnet-4-6"):
    try:
        client = Anthropic(api_key=api_key)
        with client.messages.stream(model=model or "claude-sonnet-4-6", max_tokens=4096,
                system=system, messages=messages) as stream:
            for text in stream.text_stream:
                asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
            try:
                msg = stream.get_final_message()
                usage = {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}
                asyncio.run_coroutine_threadsafe(q.put(("usage", usage)), loop)
            except Exception:
                pass
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", _friendly_anthropic_error(e))), loop)

def _run_groq(q, loop, system, messages, api_key, model):
    try:
        full_msgs = [{"role": "system", "content": system}] + messages
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": full_msgs, "max_tokens": 4096, "stream": True},
            stream=True, timeout=90,
        )
        if not r.ok:
            asyncio.run_coroutine_threadsafe(q.put(("error", f"Groq {r.status_code}: {r.text[:300]}")), loop)
            return
        for line in r.iter_lines():
            if not line: continue
            decoded = line.decode("utf-8") if isinstance(line, bytes) else line
            if decoded.startswith("data: "):
                data = decoded[6:].strip()
                if data == "[DONE]": break
                try:
                    obj = json.loads(data)
                    text = obj["choices"][0]["delta"].get("content") or ""
                    if text:
                        asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
                except json.JSONDecodeError:
                    pass  # Skip malformed or partial SSE chunk
                except (KeyError, IndexError):
                    pass  # Skip chunk with unexpected structure
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

def _run_hf(q, loop, system, messages, token, model):
    try:
        tok = (token or "").strip()
        if not tok:
            asyncio.run_coroutine_threadsafe(
                q.put(("error", "HF_TOKEN is not set. Add it to the Space secrets in HuggingFace settings.")),
                loop,
            )
            return
        hf = InferenceClient(model=model, token=tok)
        msgs = [{"role": "system", "content": system}] + messages
        for chunk in hf.chat_completion(messages=msgs, max_tokens=4096, stream=True):
            text = chunk.choices[0].delta.content or ""
            if text:
                asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        err = str(e)
        if "401" in err or "Unauthorized" in err or "Invalid username" in err:
            err = "HuggingFace token is invalid or expired. Update the HF_TOKEN Space secret."
        elif "402" in err or "Payment Required" in err or "depleted" in err or "credits" in err.lower():
            err = "HuggingFace credits exhausted. Purchase pre-paid credits or subscribe to HF PRO at huggingface.co/pricing."
        asyncio.run_coroutine_threadsafe(q.put(("error", err)), loop)

def _parse_sse_line(decoded: str) -> "str | None":
    """Parse one SSE line; return text chunk, '[DONE]' sentinel, or None to skip."""
    if not decoded.startswith("data: "):
        return None
    data = decoded[6:].strip()
    if data == "[DONE]":
        return "[DONE]"
    try:
        obj = json.loads(data)
        return obj["choices"][0]["delta"].get("content") or ""
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def _run_openai_compat(q, loop, system, messages, api_key, base_url, model):
    """Thread target: stream completions from any OpenAI-compatible endpoint."""
    try:
        url = base_url.rstrip("/") + "/chat/completions"
        hdrs = {"Content-Type": "application/json"}
        if api_key:
            hdrs["Authorization"] = f"Bearer {api_key}"
        full_msgs = [{"role": "system", "content": system}] + messages
        r = requests.post(
            url, headers=hdrs,
            json={"model": model, "messages": full_msgs, "max_tokens": 4096, "stream": True},
            stream=True, timeout=90,
        )
        if not r.ok:
            asyncio.run_coroutine_threadsafe(q.put(("error", f"API {r.status_code}: {r.text[:300]}")), loop)
            return
        for line in r.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8") if isinstance(line, bytes) else line
            text = _parse_sse_line(decoded)
            if text == "[DONE]":
                break
            if text:
                asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

async def _stream_anthropic_sse(body, system: str, user_prompt: str, max_tokens: int, timeout: int):
    """Anthropic streaming branch for _stream_ai_sse."""
    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    model = (getattr(body, 'anthropic_model', '') or 'claude-haiku-4-5-20251001').strip() or 'claude-haiku-4-5-20251001'

    def _run():
        try:
            client = Anthropic(api_key=body.anthropic_key)
            with client.messages.stream(model=model, max_tokens=max_tokens, system=system,
                    messages=[{"role": "user", "content": user_prompt}]) as stream:
                for text in stream.text_stream:
                    asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
            asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
        except Exception as e:
            asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

    threading.Thread(target=_run, daemon=True).start()
    while True:
        try:
            kind, val = await asyncio.wait_for(q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'t':'error','v':'Request timed out'})}\n\n"; return
        if kind == "text":
            yield f"data: {json.dumps({'t':'text','v':val})}\n\n"
        elif kind == "done":
            break
        else:
            yield f"data: {json.dumps({'t':'error','v':val})}\n\n"; return


async def _stream_groq_sse(body, system: str, user_prompt: str, max_tokens: int, timeout: int):
    """Groq streaming branch for _stream_ai_sse."""
    r = requests.post(  # nosec B113
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {body.groq_key}", "Content-Type": "application/json"},
        json={"model": getattr(body, 'groq_model', '') or "llama-3.3-70b-versatile", "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user_prompt}]},
        timeout=max(30, timeout // 2),
    )
    if not r.ok:
        yield f"data: {json.dumps({'t':'error','v':r.text[:200]})}\n\n"; return
    _choices = r.json().get("choices") or []
    text = ((_choices[0].get("message") or {}).get("content") or "") if _choices else ""
    if not text:
        yield f"data: {json.dumps({'t':'error','v':'Empty response from Groq'})}\n\n"; return
    for chunk in [text[i:i+80] for i in range(0, len(text), 80)]:
        yield f"data: {json.dumps({'t':'text','v':chunk})}\n\n"


async def _stream_ai_sse(body, system: str, user_prompt: str, max_tokens: int = 1024, timeout: int = 60):
    """Async generator yielding SSE chunks for Anthropic and Groq providers."""
    if body.provider == "anthropic" and body.anthropic_key:
        async for chunk in _stream_anthropic_sse(body, system, user_prompt, max_tokens, timeout):
            yield chunk
    elif body.provider == "groq" and body.groq_key:
        async for chunk in _stream_groq_sse(body, system, user_prompt, max_tokens, timeout):
            yield chunk
    else:
        yield f"data: {json.dumps({'t':'error','v':'No provider key'})}\n\n"; return
    yield f"data: {json.dumps({'t':'done'})}\n\n"

async def stream_one(runner, system: str, messages: list):
    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    threading.Thread(target=runner, args=(q, loop, system, messages), daemon=True).start()
    while True:
        try:
            kind, val = await asyncio.wait_for(q.get(), timeout=120)
            if kind in ("text", "usage", "tool_call", "tool_result", "thinking"): yield kind, val
            elif kind == "done": break
            else: yield "error", val; break
        except asyncio.TimeoutError:
            yield "error", "Request timed out"; break

@app.get("/")
async def root():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.get("/api/config")
async def get_config():
    """Return public client-side configuration (safe to expose)."""
    return JSONResponse({
        "sentry_dsn": os.environ.get("SENTRY_DSN_PUBLIC", ""),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "rollbar_token": _ROLLBAR_TOKEN,
        "rollbar_env": os.environ.get("ROLLBAR_ENVIRONMENT", "production"),
        "posthog_key": os.environ.get("POSTHOG_API_KEY", ""),
        "posthog_project_id": os.environ.get("POSTHOG_PROJECT_ID", ""),
    })

@app.get("/api/hf/models")
async def search_hf_models(q: str = Query(default="", max_length=200), limit: int = Query(default=25, ge=1, le=100)):
    params = {"pipeline_tag": "text-generation", "sort": "downloads", "direction": -1, "limit": limit, "full": False}
    if q.strip(): params["search"] = q.strip()
    try:
        r = requests.get("https://huggingface.co/api/models", params=params, timeout=10)
        if not r.ok: return JSONResponse({"error": f"HF API {r.status_code}"}, status_code=500)
        out = []
        for m in r.json():
            mid = m.get("modelId") or m.get("id", "")
            if mid: out.append({"id": mid, "name": mid.split("/")[-1],
                "author": mid.split("/")[0] if "/" in mid else "",
                "likes": m.get("likes", 0), "downloads": m.get("downloads", 0), "gated": m.get("gated", False)})
        return out
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

_oauth_states: dict[str, float] = {}  # state token -> creation timestamp (TTL 10 min)

@app.get("/api/github/auth/redirect")
async def github_auth_redirect(request: Request):
    """Step 1: redirect the browser to GitHub's OAuth consent page."""
    if not GITHUB_CLIENT_ID:
        return JSONResponse({"error": "GITHUB_CLIENT_ID not configured"}, status_code=500)
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time()
    # Prune states older than 10 minutes to prevent unbounded growth
    now = time.time()
    for k in [k for k, v in list(_oauth_states.items()) if now - v > 600]:
        _oauth_states.pop(k, None)
    callback = str(request.base_url).rstrip("/") + "/api/github/auth/callback"
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        "&scope=repo%20read%3Auser"
        f"&state={state}"
        f"&redirect_uri={_urlquote(callback, safe='')}"
    )
    return RedirectResponse(url)

@app.get("/api/github/auth/callback")
async def github_auth_callback(code: str = "", state: str = "", error: str = ""):
    """Step 2: GitHub redirects here with a code; exchange it for an access token."""
    if error:
        return RedirectResponse("/?auth_error=" + _urlquote(error, safe=""))
    if not code or state not in _oauth_states:
        return RedirectResponse("/?auth_error=invalid_state")
    _oauth_states.pop(state, None)
    try:
        r = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET, "code": code},
            timeout=15,
        )
        data = r.json()
    except Exception:
        return RedirectResponse("/?auth_error=github_unreachable")
    token = data.get("access_token", "")
    if not token:
        err = _urlquote(data.get("error_description") or data.get("error") or "no_token", safe="")
        return RedirectResponse(f"/?auth_error={err}")
    # Pass token in the URL fragment — fragments are never sent to servers, so it
    # won't appear in access logs.  The frontend reads and immediately clears it.
    return RedirectResponse(f"/#token={token}")

class TokenBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)

@app.post("/api/github/user")
async def github_user(body: TokenBody):
    r = requests.get("https://api.github.com/user",
        headers={"Authorization": f"token {body.token}", "Accept": "application/vnd.github.v3+json"}, timeout=10)
    try:
        return JSONResponse(r.json(), status_code=200 if r.ok else 400)
    except Exception:
        return JSONResponse({"error": "GitHub returned an unexpected response"}, status_code=400)

@app.post("/api/github/repos")
async def github_repos(body: TokenBody):
    repos, page = [], 1
    hdrs = {"Authorization": f"token {body.token}", "Accept": "application/vnd.github.v3+json"}
    while len(repos) < 300:
        r = requests.get(f"https://api.github.com/user/repos?per_page=100&sort=pushed&page={page}", headers=hdrs, timeout=15)
        if not r.ok: break
        data = r.json()
        if not data: break
        repos.extend(data)
        if len(data) < 100: break
        page += 1
    return [{"full_name": r.get("full_name", ""), "name": r.get("name", ""), "description": r.get("description") or "",
             "private": r.get("private", False), "language": r.get("language") or ""} for r in repos]

def parse_gh_url(url: str) -> "tuple[str | None, str | None]":
    """Extract GitHub owner and repo name from a URL or 'owner/repo' shorthand.

    Args:
        url: Full GitHub URL or 'owner/repo' string.

    Returns:
        Tuple of (owner, repo), or (None, None) if no match found.
    """
    m = re.search(r"github\.com/([^/\s]+)/([^/\s]+)", url.strip())
    if not m:
        m2 = re.match(r"^([^/\s]+)/([^/\s]+)$", url.strip())
        if m2: return m2.group(1), m2.group(2).removesuffix(".git")
        return None, None
    return m.group(1), m.group(2).removesuffix(".git").rstrip("/")

def _valid_http_url(url: str) -> bool:
    return bool(url and re.match(r"^https?://", url))

def gh_hdrs(token: str) -> dict:
    """Build GitHub API request headers for an authenticated token.

    Args:
        token: Personal access token or OAuth token for GitHub API calls.

    Returns:
        Dict with Authorization and Accept headers.
    """
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _gh_base(owner: str, repo: str) -> str:
    """Build the GitHub API repos base URL with owner/repo safely encoded."""
    return f"https://api.github.com/repos/{_urlquote(owner, safe='')}/{_urlquote(repo, safe='')}"

def _gh_path(p: str) -> str:
    """Sanitise a file path for GitHub API URLs: drop ./.., encode special chars."""
    segments = [_urlquote(s, safe="") for s in p.lstrip("/").split("/") if s not in (".", "..")]
    return "/".join(segments) or "_"

class RepoBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    url: str = Field(max_length=300)
    branch: Optional[str] = Field(default="", max_length=255)


@app.get("/api/repo/branches")
async def list_branches(token: str = Query(..., min_length=1, max_length=500), owner: str = Query(..., min_length=1, max_length=100), repo: str = Query(..., min_length=1, max_length=100)):
    """List all branches for a repository."""
    r = requests.get(
        f"{_gh_base(owner, repo)}/branches?per_page=100",
        headers=gh_hdrs(token), timeout=15,
    )
    if not r.ok:
        return JSONResponse({"error": "Failed to fetch branches"}, status_code=400)
    return [{"name": b.get("name", ""), "sha": (b.get("commit") or {}).get("sha", "")[:7]} for b in r.json()]


@app.post("/api/repo/connect")
async def repo_connect(body: RepoBody):
    owner, repo = parse_gh_url(body.url)
    if not owner: return JSONResponse({"error": "Invalid repository"}, status_code=400)
    r = requests.get(f"{_gh_base(owner, repo)}", headers=gh_hdrs(body.token), timeout=10)
    if not r.ok:
        try:
            msg = r.json().get("message", "Not found")
        except Exception:
            msg = "Not found"
        return JSONResponse({"error": msg}, status_code=400)
    repo_data = r.json()
    default_branch = repo_data.get("default_branch", "main")
    branch = (body.branch or "").strip() or default_branch
    t = requests.get(f"{_gh_base(owner, repo)}/git/trees/{_urlquote(branch, safe='')}?recursive=1",
        headers=gh_hdrs(body.token), timeout=15)
    if not t.ok: return JSONResponse({"error": "Failed to fetch file tree"}, status_code=400)
    files = sorted([{"path": f["path"], "size": f.get("size", 0)} for f in t.json().get("tree", [])
        if f["type"] == "blob" and f.get("size", 999999) < 150000], key=lambda x: x["path"])
    return {"owner": owner, "repo": repo, "branch": branch, "default_branch": default_branch, "files": files}

class FileBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=1000)
    branch: str = Field(default="", max_length=255)

@app.post("/api/repo/file")
async def repo_file(body: FileBody):
    ref_param = f"?ref={_urlquote(body.branch, safe='')}" if body.branch else ""
    r = requests.get(f"{_gh_base(body.owner, body.repo)}/contents/{_gh_path(body.path)}{ref_param}",
        headers=gh_hdrs(body.token), timeout=10)
    if not r.ok: return JSONResponse({"error": f"Cannot fetch {body.path}"}, status_code=400)
    try:
        content = base64.b64decode(r.json()["content"].replace("\n", "")).decode("utf-8", errors="replace")
    except Exception:
        return JSONResponse({"error": "Binary file"}, status_code=400)
    return {"path": body.path, "content": content}

class WriteFileBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=1000)
    content: str = Field(max_length=2_000_000)
    message: str = Field(min_length=1, max_length=500)
    branch: str = Field(min_length=1, max_length=255)

@app.post("/api/repo/write")
async def repo_write(body: WriteFileBody):
    """Create or update a file in the repository via the GitHub Contents API."""
    sha = None
    _safe_p = _gh_path(body.path)
    existing = requests.get(
        f"{_gh_base(body.owner, body.repo)}/contents/{_safe_p}",
        headers=gh_hdrs(body.token), params={"ref": body.branch}, timeout=10,
    )
    if existing.ok:
        try:
            sha = existing.json().get("sha")
        except Exception:
            pass

    payload: dict = {
        "message": body.message,
        "content": base64.b64encode(body.content.encode("utf-8")).decode("utf-8"),
        "branch": body.branch,
    }
    if sha:
        payload["sha"] = sha

    w = requests.put(
        f"{_gh_base(body.owner, body.repo)}/contents/{_safe_p}",
        headers=gh_hdrs(body.token), json=payload, timeout=15,
    )
    if not w.ok:
        try:
            err_msg = w.json().get("message", "Write failed")
        except Exception:
            err_msg = "Write failed"
        return JSONResponse({"error": err_msg}, status_code=400)

    data = w.json()
    commit = data.get("commit", {})
    content_meta = data.get("content", {})
    return {
        "sha": commit.get("sha", ""),
        "html_url": content_meta.get("html_url", ""),
        "commit_url": commit.get("html_url", ""),
    }

class SuggestFilesBody(BaseModel):
    provider: str = Field(max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    groq_model: Optional[str] = Field(default="llama-3.3-70b-versatile", max_length=200)
    openai_compat_key: Optional[str] = Field(default="", max_length=500)
    openai_compat_base_url: Optional[str] = Field(default="", max_length=2000)
    openai_compat_model: Optional[str] = Field(default="", max_length=200)
    hf_token: Optional[str] = Field(default="", max_length=500)
    hf_model: Optional[str] = Field(default="", max_length=200)
    task: str = Field(min_length=1, max_length=2000)
    files: List[str] = Field(max_length=500)
    max_suggestions: int = Field(default=6, ge=1, le=20)

def _call_anthropic_sync(body, system: str, prompt: str, max_tokens: int) -> tuple[bool, str]:
    """Non-streaming Anthropic call; returns (success, text)."""
    client = Anthropic(api_key=body.anthropic_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=max_tokens,
        system=system, messages=[{"role": "user", "content": prompt}],
    )
    return True, msg.content[0].text if msg.content else ""


def _call_openai_compat_sync(body, system: str, prompt: str, max_tokens: int) -> tuple[bool, str]:
    """Non-streaming OpenAI-compat call; returns (success, text)."""
    if not _valid_http_url(body.openai_compat_base_url):
        return False, "openai_compat_base_url must be http:// or https://"
    url = body.openai_compat_base_url.rstrip("/") + "/chat/completions"
    hdrs = {"Content-Type": "application/json"}
    if body.openai_compat_key:
        hdrs["Authorization"] = f"Bearer {body.openai_compat_key}"
    r = requests.post(url, headers=hdrs, json={
        "model": body.openai_compat_model or "llama3",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "stream": False,
    }, timeout=20)
    if r.ok:
        _choices = r.json().get("choices") or []
        return True, ((_choices[0].get("message") or {}).get("content") or "") if _choices else ""
    return False, ""


def _call_groq_sync(body, system: str, prompt: str, max_tokens: int) -> tuple[bool, str]:
    """Non-streaming Groq call; returns (success, text)."""
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {body.groq_key}", "Content-Type": "application/json"},
        json={"model": body.groq_model or "llama-3.1-8b-instant",
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
              "max_tokens": max_tokens, "stream": False},
        timeout=20,
    )
    if r.ok:
        _choices = r.json().get("choices") or []
        return True, ((_choices[0].get("message") or {}).get("content") or "") if _choices else ""
    return False, ""


def _call_ai_provider(body, system: str, prompt: str, max_tokens: int = 256) -> tuple[bool, str]:
    """Dispatch a single-turn AI call to the configured provider; returns (success, text)."""
    try:
        if body.provider == "anthropic" and body.anthropic_key:
            return _call_anthropic_sync(body, system, prompt, max_tokens)
        if body.provider == "groq" and body.groq_key:
            return _call_groq_sync(body, system, prompt, max_tokens)
        if body.provider == "openai_compat" and body.openai_compat_base_url:
            return _call_openai_compat_sync(body, system, prompt, max_tokens)
        return False, "No usable provider configured"
    except Exception as e:
        return False, str(e)

@app.post("/api/repo/suggest-files")
async def suggest_files(body: SuggestFilesBody):
    """Use AI to suggest the most relevant files for a given task."""
    file_list = "\n".join(body.files[:600])
    prompt = (
        f'Task: "{body.task}"\n\n'
        f"From the file list below, pick the {body.max_suggestions} most relevant files.\n"
        "Return ONLY a JSON array of file paths. No prose, no markdown, just the array.\n"
        "Example: [\"src/auth.ts\", \"src/middleware.ts\"]\n\n"
        f"Files:\n{file_list}"
    )
    system = "You are a file relevance expert. Return only a valid JSON array of file paths."

    success, result = _call_ai_provider(body, system, prompt, max_tokens=256)
    if not success:
        return JSONResponse({"error": result}, status_code=400)

    try:
        # Extract JSON array from result (strip any surrounding text)
        m = re.search(r'\[.*?\]', result, re.DOTALL)
        if not m:
            return JSONResponse({"error": "AI returned non-parseable response"}, status_code=400)
        suggested = json.loads(m.group(0))
        # Filter to only files that actually exist in the repo
        file_set = set(body.files)
        valid = [f for f in suggested if f in file_set]
        return {"files": valid[:body.max_suggestions]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class SummarizeFileBody(BaseModel):
    content: str = Field(min_length=1, max_length=200_000)
    filename: str = Field(max_length=500)
    provider: str = Field(max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    groq_model: Optional[str] = Field(default="llama-3.3-70b-versatile", max_length=200)
    openai_compat_key: Optional[str] = Field(default="", max_length=500)
    openai_compat_base_url: Optional[str] = Field(default="", max_length=2000)
    openai_compat_model: Optional[str] = Field(default="", max_length=200)


@app.post("/api/repo/summarize-file")
async def summarize_file(body: SummarizeFileBody):
    """Condense a large file to a short AI-generated summary for context injection."""
    system = "You are a code summarizer. Produce a concise summary (under 400 words) of the file: its purpose, key exports/functions/classes, and important patterns. Be specific and technical."
    prompt = f"File: {body.filename}\n\n```\n{body.content[:8000]}\n```\n\nSummarize this file for AI context."

    success, result = _call_ai_provider(body, system, prompt, max_tokens=600)
    if not success:
        return JSONResponse({"error": result}, status_code=400)
    if not result:
        return JSONResponse({"error": "Empty summary returned"}, status_code=400)
    return {"summary": result}


class BatchWriteItem(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    content: str = Field(max_length=2_000_000)
    message: str = Field(min_length=1, max_length=500)

class BatchWriteBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    branch: str = Field(min_length=1, max_length=255)
    files: List[BatchWriteItem] = Field(min_length=1, max_length=50)

def _gh_write_file(item, owner: str, repo: str, branch: str, token: str) -> tuple:
    """PUT a single file to GitHub Contents API; returns ("ok"|"error", result_dict)."""
    safe_p = _gh_path(item.path)
    sha = None
    try:
        existing = requests.get(
            f"{_gh_base(owner, repo)}/contents/{safe_p}",
            headers=gh_hdrs(token), params={"ref": branch}, timeout=10,
        )
        if existing.ok:
            sha = existing.json().get("sha")
    except Exception:
        pass
    payload = {
        "message": item.message,
        "content": base64.b64encode(item.content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    try:
        w = requests.put(
            f"{_gh_base(owner, repo)}/contents/{safe_p}",
            headers=gh_hdrs(token), json=payload, timeout=15,
        )
        if w.ok:
            return ("ok", {"path": item.path, "commit_url": w.json().get("commit", {}).get("html_url", "")})
        try:
            err_msg = w.json().get("message", "Write failed")
        except Exception:
            err_msg = "Write failed"
        return ("error", {"path": item.path, "error": err_msg})
    except Exception as e:
        return ("error", {"path": item.path, "error": str(e)})


@app.post("/api/repo/write/batch")
async def repo_write_batch(body: BatchWriteBody):
    """Commit multiple files to the repository, reporting per-file results."""
    committed, errors = [], []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(_gh_write_file, item, body.owner, body.repo, body.branch, body.token): item for item in body.files}
        for future in _futs_done(futures, timeout=60):
            try:
                status, result = future.result()
                if status == "ok":
                    committed.append(result)
                else:
                    errors.append(result)
            except Exception as e:
                item = futures[future]
                errors.append({"path": item.path, "error": str(e)})
    return {"committed": committed, "errors": errors}


class GistBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    filename: str = Field(max_length=255)
    content: str = Field(max_length=1_000_000)
    description: Optional[str] = Field(default="", max_length=255)
    public: Optional[bool] = False

@app.post("/api/github/gist/create")
async def create_gist(body: GistBody):
    """Create a GitHub Gist from a code block."""
    fname = (body.filename or "snippet.txt").strip() or "snippet.txt"
    r = requests.post(
        "https://api.github.com/gists",
        headers=gh_hdrs(body.token),
        json={
            "description": (body.description or f"DevForge snippet: {fname}")[:255],
            "public": bool(body.public),
            "files": {fname: {"content": body.content}},
        },
        timeout=15,
    )
    if not r.ok:
        try:
            err = r.json().get("message", "Failed to create gist")
        except Exception:
            err = "Failed to create gist"
        return JSONResponse({"error": err}, status_code=400)
    data = r.json()
    return {"url": data.get("html_url", ""), "id": data.get("id", "")}


class IssueBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(max_length=65_536)
    labels: Optional[List[str]] = Field(default=[], max_length=10)

@app.post("/api/github/issue/create")
async def create_issue(body: IssueBody):
    """Create a GitHub issue in the connected repository."""
    r = requests.post(
        f"{_gh_base(body.owner, body.repo)}/issues",
        headers=gh_hdrs(body.token),
        json={"title": body.title, "body": body.body, "labels": body.labels},
        timeout=15,
    )
    if not r.ok:
        try:
            err = r.json().get("message", "Failed to create issue")
        except Exception:
            err = "Failed to create issue"
        return JSONResponse({"error": err}, status_code=400)
    data = r.json()
    return {"url": data.get("html_url", ""), "number": data.get("number")}


class PRBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(max_length=65_536)
    head: str = Field(min_length=1, max_length=255)
    base: str = Field(min_length=1, max_length=255)

@app.post("/api/github/pr/create")
async def create_pr(body: PRBody):
    """Create a GitHub pull request from head branch into base branch."""
    r = requests.post(
        f"{_gh_base(body.owner, body.repo)}/pulls",
        headers=gh_hdrs(body.token),
        json={"title": body.title, "body": body.body, "head": body.head, "base": body.base},
        timeout=15,
    )
    if not r.ok:
        try:
            err = r.json().get("message", "Failed to create PR")
        except Exception:
            err = "Failed to create PR"
        return JSONResponse({"error": err}, status_code=400)
    data = r.json()
    return {"url": data.get("html_url", ""), "number": data.get("number")}


class PRDiffBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    pr_number: int = Field(ge=1)

@app.post("/api/github/pr/diff")
async def get_pr_diff(body: PRDiffBody):
    """Fetch a pull request's metadata and unified diff."""
    # Get PR metadata
    pr_r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/pulls/{body.pr_number}",
        headers=gh_hdrs(body.token),
        timeout=15,
    )
    if not pr_r.ok:
        return JSONResponse({"error": f"PR #{body.pr_number} not found"}, status_code=404)
    pr = pr_r.json()
    # Get diff (cap at 40KB)
    diff_r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/pulls/{body.pr_number}",
        headers={**gh_hdrs(body.token), "Accept": "application/vnd.github.diff"},
        timeout=20,
    )
    diff_text = diff_r.text[:40000] if diff_r.ok else ""
    return {
        "number": pr.get("number"),
        "title": pr.get("title", ""),
        "body": (pr.get("body") or "")[:1000],
        "author": pr.get("user", {}).get("login", ""),
        "head": pr.get("head", {}).get("ref", ""),
        "base": pr.get("base", {}).get("ref", ""),
        "changed_files": pr.get("changed_files", 0),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "diff": diff_text,
        "url": pr.get("html_url", ""),
    }


class RepoSearchBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=500)
    max_results: int = Field(default=10, ge=1, le=30)


@app.post("/api/repo/search")
async def repo_search(body: RepoSearchBody):
    """Search code in a repository using GitHub code search API."""
    if not body.query.strip():
        return JSONResponse({"error": "Empty query"}, status_code=400)
    hdrs = {
        "Authorization": f"token {body.token}",
        "Accept": "application/vnd.github.v3.text-match+json",
    }
    r = requests.get(
        "https://api.github.com/search/code",
        headers=hdrs,
        params={"q": f"{body.query.strip()} repo:{body.owner}/{body.repo}", "per_page": min(body.max_results, 20)},
        timeout=15,
    )
    if not r.ok:
        try:
            err = r.json().get("message", "Search failed")
        except Exception:
            err = "Search failed"
        return JSONResponse({"error": err}, status_code=400)
    data = r.json()
    items = []
    for item in data.get("items", []):
        snippets = []
        for tm in item.get("text_matches", []):
            for m in tm.get("matches", []):
                t = (m.get("text") or "").strip()
                if t:
                    snippets.append(t[:120])
        items.append({
            "path": item.get("path", ""),
            "sha": (item.get("sha") or "")[:7],
            "url": item.get("html_url", ""),
            "snippets": snippets[:3],
        })
    return {"items": items, "total": data.get("total_count", 0)}


class RepoCommitsBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    branch: Optional[str] = Field(default="main", max_length=255)
    max_results: int = Field(default=10, ge=1, le=50)


@app.post("/api/repo/commits")
async def repo_commits(body: RepoCommitsBody):
    """Fetch recent commits for a branch."""
    r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/commits",
        headers=gh_hdrs(body.token),
        params={"sha": body.branch or "main", "per_page": min(body.max_results, 30)},
        timeout=15,
    )
    if not r.ok:
        return JSONResponse({"error": "Failed to fetch commits"}, status_code=400)
    return [
        {
            "sha": (c.get("sha") or "")[:7],
            "message": ((c.get("commit") or {}).get("message", "").split("\n")[0])[:80],
            "author": ((c.get("commit") or {}).get("author") or {}).get("name", "")[:30],
            "date": ((c.get("commit") or {}).get("author") or {}).get("date", "")[:10],
            "url": c.get("html_url", ""),
        }
        for c in r.json()
    ]


class RepoDiffBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    base: str = Field(min_length=1, max_length=255)
    head: str = Field(min_length=1, max_length=255)


@app.post("/api/repo/diff")
async def repo_diff(body: RepoDiffBody):
    """Return the unified diff between two refs (branch names, tags, or SHAs)."""
    base_safe = _urlquote(body.base, safe="")
    head_safe = _urlquote(body.head, safe="")
    r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/compare/{base_safe}...{head_safe}",
        headers={**gh_hdrs(body.token), "Accept": "application/vnd.github.v3.diff"},
        timeout=20,
    )
    if not r.ok:
        try:
            err = r.json().get("message", "Diff failed")
        except Exception:
            err = f"HTTP {r.status_code}"
        return JSONResponse({"error": err}, status_code=400)
    diff_text = r.text[:50_000]
    files: list = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" b/", 1)
            if len(parts) == 2:
                files.append(parts[1])
    return {"diff": diff_text, "files_changed": files, "truncated": len(r.text) > 50_000}


class RepoTreeBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    branch: str = Field(default="main", max_length=255)
    max_files: int = Field(default=500, ge=1, le=2000)


@app.post("/api/repo/tree")
async def repo_tree(body: RepoTreeBody):
    """Return the recursive file tree for a branch (paths only, no content)."""
    ref = _urlquote(body.branch, safe="")
    r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/git/trees/{ref}?recursive=1",
        headers=gh_hdrs(body.token),
        timeout=15,
    )
    if not r.ok:
        try:
            err = r.json().get("message", "Failed to fetch tree")
        except Exception:
            err = f"HTTP {r.status_code}"
        return JSONResponse({"error": err}, status_code=400)
    data = r.json()
    tree = data.get("tree", [])
    files = [
        {"path": item["path"], "type": item["type"], "size": item.get("size", 0)}
        for item in tree
        if item.get("type") in ("blob", "tree")
    ][:body.max_files]
    return {
        "files": files,
        "total": len(data.get("tree", [])),
        "truncated": data.get("truncated", False) or len(tree) > body.max_files,
        "branch": body.branch,
    }


class WorkflowRunsBody(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    max_results: int = Field(default=10, ge=1, le=50)


@app.post("/api/repo/workflow-runs")
async def repo_workflow_runs(body: WorkflowRunsBody):
    """Fetch recent GitHub Actions workflow runs."""
    r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/actions/runs",
        headers=gh_hdrs(body.token),
        params={"per_page": min(body.max_results, 20)},
        timeout=15,
    )
    if not r.ok:
        return JSONResponse({"error": "Failed to fetch workflow runs"}, status_code=400)
    runs = r.json().get("workflow_runs", [])
    return [
        {
            "id": run.get("id"),
            "name": (run.get("name") or run.get("display_title") or "Workflow")[:60],
            "status": run.get("status", ""),        # queued / in_progress / completed
            "conclusion": run.get("conclusion") or "",  # success / failure / cancelled / ...
            "branch": (run.get("head_branch") or "")[:40],
            "sha": (run.get("head_sha") or "")[:7],
            "date": (run.get("updated_at") or "")[:10],
            "url": run.get("html_url", ""),
        }
        for run in runs
    ]


RELEASE_NOTES_SYSTEM = (
    "You are a technical writer creating release notes for developers. "
    "Given a list of Git commit messages, generate a concise, well-structured release notes document. "
    "Group commits into sections: ✨ New Features, 🐛 Bug Fixes, ♻️ Improvements, 🔧 Maintenance. "
    "Skip merge commits and bumps. Use bullet points. Start with a 1-sentence summary of the release. "
    "Output Markdown."
)

class ReleaseNotesBody(BaseModel):
    provider: str = Field(default="anthropic", max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    token: str = Field(min_length=1, max_length=500)
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)
    since: Optional[str] = Field(default="", max_length=255)
    until: Optional[str] = Field(default="", max_length=255)
    max_commits: int = Field(default=50, ge=1, le=100)
    anthropic_model: Optional[str] = Field(default="claude-sonnet-4-6", max_length=200)

@app.post("/api/repo/release-notes")
async def generate_release_notes(body: ReleaseNotesBody):
    """Stream AI-generated release notes from recent commits."""
    # Fetch commits
    params: dict = {"per_page": min(body.max_commits, 50)}
    if body.until:
        params["sha"] = body.until
    r = requests.get(
        f"{_gh_base(body.owner, body.repo)}/commits",
        headers=gh_hdrs(body.token),
        params=params,
        timeout=15,
    )
    if not r.ok:
        return JSONResponse({"error": "Failed to fetch commits"}, status_code=400)
    all_commits = r.json()
    # If since is provided, truncate at that SHA
    if body.since:
        since_sha = body.since
        # Also handle tags — resolve to SHA
        tag_r = requests.get(
            f"{_gh_base(body.owner, body.repo)}/git/refs/tags/{_urlquote(since_sha, safe='')}",
            headers=gh_hdrs(body.token), timeout=10,
        )
        if tag_r.ok:
            obj = tag_r.json().get("object", {})
            since_sha = obj.get("sha", since_sha)[:40]
        trimmed = []
        for c in all_commits:
            csha = (c.get("sha") or "")
            if csha.startswith(since_sha) or since_sha.startswith(csha[:len(since_sha)]):
                break
            trimmed.append(c)
        all_commits = trimmed
    if not all_commits:
        return JSONResponse({"error": "No commits found in range"}, status_code=400)
    commit_list = "\n".join(
        f"- {(c.get('sha') or '')[:7]} {((c.get('commit') or {}).get('message', '').split(chr(10))[0])[:100]}"
        for c in all_commits
        if "Merge" not in ((c.get("commit") or {}).get("message", ""))[:10]
    )
    user_prompt = (
        f"Repository: {body.owner}/{body.repo}\n"
        f"Commits ({len(all_commits)} total):\n{commit_list}"
    )
    return StreamingResponse(
        _stream_ai_sse(body, RELEASE_NOTES_SYSTEM, user_prompt, max_tokens=1024, timeout=60),
        media_type="text/event-stream",
    )


COMMIT_MSG_SYSTEM = (
    "You are a Git commit message expert. Given a file path and its new content (or a diff), "
    "write a concise conventional commit message (type(scope): description). "
    "Keep it under 72 characters. Return ONLY the commit message — no explanations, no quotes."
)

class CommitMsgBody(BaseModel):
    provider: str = Field(default="anthropic", max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    groq_model: Optional[str] = Field(default="", max_length=200)
    openai_compat_key: Optional[str] = Field(default="", max_length=500)
    openai_compat_base_url: Optional[str] = Field(default="", max_length=2000)
    openai_compat_model: Optional[str] = Field(default="", max_length=200)
    path: str = Field(max_length=1000)
    content: Optional[str] = Field(default="", max_length=50_000)
    diff: Optional[str] = Field(default="", max_length=50_000)

@app.post("/api/commit/suggest-message")
async def suggest_commit_message(body: CommitMsgBody):
    """Generate a conventional commit message for a file change."""
    try:
        snippet = (body.diff or body.content or "")[:2000]
        user_prompt = f"File: {body.path}\n\n{snippet}"
        success, result = _call_ai_provider(body, COMMIT_MSG_SYSTEM, user_prompt, max_tokens=80)
        if not success:
            return JSONResponse({"error": result}, status_code=400)
        return {"message": result.strip()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


SECURITY_PATTERNS: dict = {
    "python": [
        (r'shell\s*=\s*True', "high", "shell=True creates command injection risk — pass args as a list"),
        (r'hashlib\.(md5|sha1)\b', "medium", "MD5/SHA-1 are weak hash functions — use SHA-256 or stronger"),
        (r'\brandom\.(random|randint|choice|uniform)\(', "low", "random module is not cryptographically secure — use secrets for tokens"),
    ],
    "javascript": [
        (r'\beval\s*\(', "high", "eval() executes arbitrary code — avoid it entirely"),
        (r'\.innerHTML\s*=(?!=)', "high", "innerHTML assignment can cause XSS — use textContent or DOMPurify"),
        (r'document\.write\s*\(', "high", "document.write() can cause XSS"),
        (r'new\s+Function\s*\(', "high", "new Function() executes arbitrary code"),
        (r'setTimeout\s*\(\s*["\']', "medium", "setTimeout with string argument is equivalent to eval()"),
        (r'dangerouslySetInnerHTML', "medium", "dangerouslySetInnerHTML — ensure content is sanitized first"),
        (r'Math\.random\s*\(', "low", "Math.random() is not cryptographically secure — use crypto.getRandomValues()"),
        (r'localStorage\.setItem', "low", "localStorage stores data in plaintext — avoid storing sensitive data"),
    ],
    "typescript": [
        (r'\beval\s*\(', "high", "eval() executes arbitrary code — avoid it entirely"),
        (r'\.innerHTML\s*=(?!=)', "high", "innerHTML assignment can cause XSS — use textContent or DOMPurify"),
        (r'new\s+Function\s*\(', "high", "new Function() executes arbitrary code"),
        (r'dangerouslySetInnerHTML', "medium", "dangerouslySetInnerHTML — ensure content is sanitized first"),
        (r':\s*any\b', "low", "TypeScript 'any' bypasses type safety — use explicit types"),
        (r'Math\.random\s*\(', "low", "Math.random() is not cryptographically secure — use crypto.getRandomValues()"),
    ],
    "sql": [
        (r'(?:SELECT|INSERT|UPDATE|DELETE)[^;]*["\'].*\+', "high", "String concatenation in SQL — use parameterized queries"),
        (r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*\{', "high", "f-string SQL query — use parameterized queries"),
    ],
    "go": [
        (r'fmt\.Sprintf.*(?:SELECT|INSERT|UPDATE|DELETE)', "high", "fmt.Sprintf in SQL — use database/sql parameterized queries"),
        (r'exec\.Command\(.*\+', "high", "String concatenation in exec.Command — validate all inputs"),
    ],
    "bash": [
        (r'\beval\s+', "high", "eval in bash executes arbitrary code — avoid with user-controlled input"),
        (r'curl\s+.*\|\s*(?:bash|sh)\b', "high", "Piping curl to bash is a security risk — verify script integrity first"),
    ],
}

GENERIC_SECURITY_PATTERNS = [
    (r'(?i)(?:password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']', "high", "Hardcoded password — use environment variables"),
    (r'(?i)(?:secret|api_?key|private_?key)\s*=\s*["\'][^"\']{6,}["\']', "high", "Hardcoded secret/key — use environment variables"),
    (r'(?i)token\s*=\s*["\'][a-zA-Z0-9_\-]{10,}["\']', "high", "Possible hardcoded token — use environment variables"),
    (r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)', "low", "Non-HTTPS external URL — use HTTPS for all connections"),
]

_DANGEROUS_CALLS: dict = {
    "eval": "high", "exec": "high", "__import__": "medium", "compile": "medium",
}
_DANGEROUS_ATTRS: dict = {
    ("os", "system"): "high", ("os", "popen"): "high",
    ("subprocess", "call"): "medium", ("subprocess", "run"): "medium",
    ("subprocess", "Popen"): "medium",
    ("pickle", "loads"): "high", ("pickle", "load"): "high",
}


class CodeScanBody(BaseModel):
    code: str = Field(max_length=100_000)
    language: str = Field(default="text", max_length=50)


_SECRET_KEYWORDS = ("password", "secret", "api_key", "token", "private_key")


def _ast_check_call(node: "_ast.Call", ln: "int | None", issues: list) -> None:
    """Inspect an AST Call node for dangerous function/attribute calls and shell=True."""
    func = node.func
    if isinstance(func, _ast.Name) and func.id in _DANGEROUS_CALLS:
        sev = _DANGEROUS_CALLS[func.id]
        issues.append({"severity": sev, "pattern": f"{func.id}()",
            "message": f"{func.id}() can execute arbitrary code — avoid or restrict carefully",
            "line": ln, "source": "ast"})
    elif isinstance(func, _ast.Attribute) and isinstance(func.value, _ast.Name):
        pair = (func.value.id, func.attr)
        if pair in _DANGEROUS_ATTRS:
            sev = _DANGEROUS_ATTRS[pair]
            issues.append({"severity": sev, "pattern": f"{pair[0]}.{pair[1]}()",
                "message": f"{pair[0]}.{pair[1]}() is a high-risk call — validate all inputs",
                "line": ln, "source": "ast"})
    for kw in node.keywords:
        if kw.arg == "shell" and isinstance(kw.value, _ast.Constant) and kw.value.value is True:
            issues.append({"severity": "high", "pattern": "shell=True",
                "message": "shell=True creates command injection risk — pass args as a list",
                "line": ln, "source": "ast"})


def _ast_check_assign(node: "_ast.Assign", ln: "int | None", issues: list) -> None:
    """Inspect an AST Assign node for hardcoded secret-like string values."""
    for target in node.targets:
        if not isinstance(target, _ast.Name):
            continue
        nm = target.id.lower()
        if not any(kw in nm for kw in _SECRET_KEYWORDS):
            continue
        if isinstance(node.value, _ast.Constant) and isinstance(node.value.value, str) and len(node.value.value) >= 6:
            issues.append({"severity": "high", "pattern": f"{target.id} = '...'",
                "message": f"Hardcoded {target.id} — use os.environ or a secrets manager",
                "line": ln, "source": "ast"})


def _python_ast_issues(code: str) -> list:
    """Return security issues found via AST walk of Python source (max 50K chars)."""
    issues: list = []
    try:
        tree = _ast.parse(code[:50_000])
        for node in _ast.walk(tree):
            ln = getattr(node, "lineno", None)
            if isinstance(node, _ast.Call):
                _ast_check_call(node, ln, issues)
            elif isinstance(node, _ast.Assign):
                _ast_check_assign(node, ln, issues)
    except SyntaxError as e:
        issues.append({"severity": "medium", "pattern": "SyntaxError",
            "message": f"Code has syntax errors: {e.msg}", "line": e.lineno, "source": "ast"})
    return issues


@app.post("/api/code/scan")
async def scan_code(body: CodeScanBody):
    """Scan code for security issues using AST analysis (Python) and pattern matching."""
    code = (body.code or "").strip()[:100_000]
    lang = (body.language or "text").lower()
    if not code:
        return {"issues": [], "safe": True, "language": lang, "total": 0}
    issues: list = _python_ast_issues(code) if lang == "python" else []
    lang_patterns = SECURITY_PATTERNS.get(lang, [])
    ast_high_lines = {i["line"] for i in issues if i.get("source") == "ast" and i.get("severity") == "high"}
    seen: set = set()
    for lineno, line in enumerate(code.split("\n"), 1):
        for pat, sev, msg in lang_patterns + GENERIC_SECURITY_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                key = (lineno, pat)
                if key not in seen and not (lang == "python" and lineno in ast_high_lines and sev == "high"):
                    seen.add(key)
                    clean_pat = re.sub(r'[\\^$.*+?()\[\]{}|]', '', pat)[:30].strip()
                    issues.append({"severity": sev, "pattern": clean_pat, "message": msg, "line": lineno, "source": "pattern"})
    sev_order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda x: (sev_order.get(x.get("severity", "low"), 3), x.get("line") or 9999))
    issues = issues[:15]
    safe = not any(i["severity"] in ("high", "medium") for i in issues)
    return {"issues": issues, "safe": safe, "language": lang, "total": len(issues)}


README_SYSTEM = (
    "You are a technical writer. Generate a comprehensive, well-structured README.md for the given "
    "repository based on its code files. Include: project name and one-line description, "
    "features, tech stack, installation instructions (inferred from code), usage examples, "
    "API reference if applicable, and contribution guidelines. Use GitHub-flavored Markdown with "
    "badges where appropriate. Make it professional and developer-friendly."
)

class ReadmeBody(BaseModel):
    provider: str = Field(default="anthropic", max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    anthropic_model: Optional[str] = Field(default="claude-sonnet-4-6", max_length=200)
    groq_key: Optional[str] = Field(default="", max_length=500)
    repo_name: Optional[str] = Field(default="", max_length=200)
    file_context: str = Field(max_length=500_000)

@app.post("/api/repo/generate-readme")
async def generate_readme(body: ReadmeBody):
    """Stream an AI-generated README.md based on repo file context."""
    if not (body.file_context or "").strip():
        return JSONResponse({"error": "file_context required"}, status_code=400)
    user_prompt = (
        f"Repository: {body.repo_name or 'Unknown'}\n\n"
        f"Files:\n{body.file_context[:12000]}"
    )
    return StreamingResponse(
        _stream_ai_sse(body, README_SYSTEM, user_prompt, max_tokens=2048, timeout=90),
        media_type="text/event-stream",
    )


DEPS_AUDIT_SYSTEM = (
    "You are a software security auditor reviewing project dependencies. "
    "Given a list of packages with their pinned and latest versions, identify: "
    "known security vulnerabilities (CVEs) in outdated packages, "
    "packages that are deprecated or unmaintained, supply-chain risks, and update recommendations. "
    "Group findings by severity: 🔴 Critical, 🟡 Warning, 🟢 Info. "
    "Be specific about package names and versions. Keep it concise and actionable."
)

def _pypi_latest(name: str) -> dict:
    try:
        r = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=3)
        if r.ok:
            return {"name": name, "latest": r.json().get("info", {}).get("version")}
    except Exception:
        pass
    return {"name": name, "latest": None}

def _npm_latest(name: str) -> dict:
    try:
        r = requests.get(f"https://registry.npmjs.org/{name}/latest", timeout=3)
        if r.ok:
            return {"name": name, "latest": r.json().get("version")}
    except Exception:
        pass
    return {"name": name, "latest": None}

def _parse_requirements(content: str) -> list:
    pkgs: list = []
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith(("#", "-r", "--", "http", "git+")):
            continue
        line = re.sub(r"\[.*?\]", "", line)
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*([>=<!~^,\s][^\s#]*)?", line)
        if m:
            pkgs.append({"name": m.group(1).lower().replace("_", "-"), "constraint": (m.group(2) or "").strip()})
    return pkgs

def _parse_package_json(content: str) -> list:
    try:
        data = json.loads(content)
        pkgs: list = []
        for section in ("dependencies", "devDependencies"):
            for name, ver in (data.get(section) or {}).items():
                pkgs.append({"name": name, "constraint": str(ver)})
        return pkgs
    except Exception:
        return []

def _parse_go_mod(content: str) -> list:
    pkgs: list = []
    in_req = False
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("require ("):
            in_req = True; continue
        if line == ")":
            in_req = False; continue
        if in_req or line.startswith("require "):
            parts = line.replace("require ", "").split()
            if len(parts) >= 2 and not parts[0].startswith("//"):
                pkgs.append({"name": parts[0], "constraint": parts[1]})
    return pkgs

_PEP508_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*([>=<!~^,][^\s#;]*)?")


def _pep508_add(dep: str, pkgs: list, seen: set) -> None:
    """Parse one PEP 508 dependency string and append to pkgs if not seen."""
    m = _PEP508_RE.match(str(dep).strip())
    if m:
        key = m.group(1).lower().replace("_", "-")
        if key not in seen:
            seen.add(key)
            pkgs.append({"name": key, "constraint": (m.group(2) or "").strip()})


def _add_poetry_deps(data: dict, pkgs: list, seen: set) -> None:
    """Extract poetry dependencies from parsed pyproject.toml data."""
    poetry_deps = (((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {})
    for name, ver in poetry_deps.items():
        if name.lower() == "python":
            continue
        key = name.lower().replace("_", "-")
        if key not in seen:
            seen.add(key)
            constraint = str(ver) if not isinstance(ver, dict) else (ver.get("version") or "")
            pkgs.append({"name": key, "constraint": constraint})


def _parse_pyproject_toml(content: str) -> list:
    try:
        import tomllib
    except ImportError:
        return _parse_requirements(content)
    try:
        data = tomllib.loads(content)
    except Exception:
        return []
    pkgs: list = []
    seen: set = set()
    for dep in ((data.get("project") or {}).get("dependencies") or []):
        _pep508_add(dep, pkgs, seen)
    _add_poetry_deps(data, pkgs, seen)
    for dep in ((data.get("build-system") or {}).get("requires") or []):
        _pep508_add(dep, pkgs, seen)
    return pkgs

def _parse_cargo_toml(content: str) -> list:
    pkgs: list = []
    in_deps = False
    for line in content.split("\n"):
        line = line.strip()
        if re.match(r'^\[(dependencies|dev-dependencies)', line, re.I):
            in_deps = True; continue
        if line.startswith("[") and in_deps:
            in_deps = False
        if in_deps:
            m = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']?([^"\'#\s,}]+)', line)
            if m:
                constraint = m.group(2).strip()
                if constraint.startswith("{"):
                    vm = re.search(r'version\s*=\s*["\']([^"\']+)', line)
                    constraint = vm.group(1) if vm else constraint
                pkgs.append({"name": m.group(1), "constraint": constraint})
    return pkgs


class ScanDepsBody(BaseModel):
    filename: str = Field(max_length=255)
    content: str = Field(max_length=200_000)
    provider: str = Field(default="anthropic", max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    anthropic_model: Optional[str] = Field(default="claude-haiku-4-5-20251001", max_length=200)


_DEPS_ECOSYSTEM_MAP: dict = {
    "pyproject.toml": ("python", _parse_pyproject_toml, _pypi_latest),
    "package.json": ("javascript", _parse_package_json, _npm_latest),
    "go.mod": ("go", _parse_go_mod, None),
    "cargo.toml": ("rust", _parse_cargo_toml, None),
}


def _detect_deps_ecosystem(fname: str, content: str) -> tuple:
    """Return (ecosystem, packages, checker) for the given dependency filename."""
    if fname in _DEPS_ECOSYSTEM_MAP:
        ecosystem, parser, checker = _DEPS_ECOSYSTEM_MAP[fname]
        return ecosystem, parser(content), checker
    if fname == "requirements.txt" or fname.endswith("requirements.txt"):
        return "python", _parse_requirements(content), _pypi_latest
    return "unknown", _parse_requirements(content), None


def _parallel_version_check(packages: list, checker) -> dict:
    """Return {name: latest_version} for the first 20 packages using a thread pool."""
    version_map: dict = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(checker, p["name"]): p["name"] for p in packages[:20]}
        for f in _futs_done(futs, timeout=12):
            try:
                rv = f.result()
                if rv.get("latest"):
                    version_map[rv["name"]] = rv["latest"]
            except Exception:
                pass
    return version_map


def _build_pkg_results(packages: list, version_map: dict, ecosystem: str) -> list:
    """Build per-package result dicts with pinned/latest/outdated/unpinned fields."""
    def _extract_pinned(constraint: str) -> "str | None":
        m = re.search(r'==\s*([^\s,;]+)', constraint)
        return m.group(1) if m else None
    results = []
    for p in packages[:20]:
        pinned = _extract_pinned(p["constraint"])
        latest = version_map.get(p["name"])
        results.append({
            "name": p["name"], "constraint": p["constraint"],
            "pinned": pinned, "latest": latest,
            "outdated": bool(pinned and latest and pinned != latest),
            "unpinned": not pinned and ecosystem == "python",
        })
    return results


@app.post("/api/repo/scan-deps")
async def scan_deps(body: ScanDepsBody):
    """Parse a dependency file, check latest versions, and stream an AI security audit."""
    fname = (body.filename or "").lower().strip().split("/")[-1]
    content = (body.content or "").strip()[:200_000]
    if not content:
        return JSONResponse({"error": "content required"}, status_code=400)
    ecosystem, packages, checker = _detect_deps_ecosystem(fname, content)
    if not packages:
        return JSONResponse({"error": "No packages found in file"}, status_code=400)
    version_map = _parallel_version_check(packages, checker) if checker else {}
    pkg_results = _build_pkg_results(packages, version_map, ecosystem)
    audit_lines = "\n".join(
        f"- {p['name']}: {p['pinned'] or p['constraint']} (latest: {p['latest'] or '?'})"
        + (" ⚠️ OUTDATED" if p["outdated"] else "")
        + (" ⚠️ UNPINNED" if p["unpinned"] else "")
        for p in pkg_results
    )
    ai_prompt = f"Ecosystem: {ecosystem}\nFile: {body.filename}\n\nPackages:\n{audit_lines}"

    async def _stream():
        yield f"data: {json.dumps({'t':'packages','v':{'ecosystem':ecosystem,'packages':pkg_results}})}\n\n"
        async for chunk in _stream_ai_sse(body, DEPS_AUDIT_SYSTEM, ai_prompt, max_tokens=1024, timeout=60):
            yield chunk

    return StreamingResponse(_stream(), media_type="text/event-stream")


class ToolDef(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=1000)
    url: str = Field(max_length=2000)
    method: str = Field(default="GET", max_length=10)
    headers: Optional[dict] = {}
    input_schema: Optional[dict] = None


class ToolCallBody(BaseModel):
    url: str = Field(max_length=2000)
    method: str = Field(default="GET", max_length=10)
    headers: Optional[dict] = {}
    body_json: Optional[dict] = None


_SSRF_BLOCKED = re.compile(
    r"^https?://"
    r"(?:localhost|127\.|0\.0\.0\.0|"
    r"10\.\d+\.\d+\.\d+|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|"
    r"192\.168\.\d+\.\d+|"
    r"169\.254\.\d+\.\d+|"   # link-local / AWS metadata
    r"\[::1\])",              # IPv6 loopback
    re.IGNORECASE,
)

_BLOCKED_HDRS = frozenset({
    "host", "transfer-encoding", "connection", "upgrade",
    "proxy-authorization", "te", "trailers", "keep-alive",
})


def _validate_body_json(body_json) -> "JSONResponse | None":
    """Return error JSONResponse if body_json is invalid or oversized, else None."""
    if body_json is None:
        return None
    try:
        size = len(json.dumps(body_json))
    except Exception:
        return JSONResponse({"error": "body_json is not JSON-serialisable"}, status_code=400)
    if size > 65_536:
        return JSONResponse({"error": "body_json exceeds 64 KB limit"}, status_code=413)
    return None


def _validate_tool_call(body) -> "JSONResponse | None":
    """Return an error JSONResponse for an invalid tool call request, or None if valid."""
    if not re.match(r"^https?://", body.url):
        return JSONResponse({"error": "Only http:// and https:// URLs are supported"}, status_code=400)
    if _SSRF_BLOCKED.match(body.url):
        return JSONResponse({"error": "Requests to internal/private addresses are not allowed"}, status_code=400)
    if body.method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        return JSONResponse({"error": f"Unsupported method: {body.method}"}, status_code=400)
    body_err = _validate_body_json(body.body_json)
    if body_err is not None:
        return body_err
    return None


@app.post("/api/tools/call")
async def call_tool(body: ToolCallBody):
    """Proxy a user-defined tool HTTP call to avoid CORS issues."""
    err = _validate_tool_call(body)
    if err is not None:
        return err
    method = body.method.upper()
    try:
        raw_hdrs = dict(list((body.headers or {}).items())[:50])
        hdrs = {str(k)[:200]: str(v)[:2000] for k, v in raw_hdrs.items() if str(k).lower() not in _BLOCKED_HDRS}
        if method != "GET":
            hdrs.setdefault("Content-Type", "application/json")
        if method == "GET":
            r = requests.get(body.url, headers=hdrs, timeout=15)
        else:
            r = requests.request(method, body.url, headers=hdrs, json=body.body_json, timeout=15)
        return {"status": r.status_code, "response": r.text[:2000]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


ENHANCE_SYSTEM = (
    "You are a prompt engineering expert. The user will give you a coding task description. "
    "Rewrite it to be more specific, actionable, and complete. Mention relevant files, functions, "
    "or patterns when implied. Return ONLY the improved prompt text — no preamble, no explanation."
)

class PromptEnhanceBody(BaseModel):
    provider: str = Field(default="anthropic", max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    groq_model: Optional[str] = Field(default="", max_length=200)
    openai_compat_key: Optional[str] = Field(default="", max_length=500)
    openai_compat_base_url: Optional[str] = Field(default="", max_length=2000)
    openai_compat_model: Optional[str] = Field(default="", max_length=200)
    hf_token: Optional[str] = Field(default="", max_length=500)
    prompt: str = Field(max_length=4000)

def _enhance_with_hf(p: str, hf_token: str) -> tuple[bool, str]:
    """Run HF-based prompt enhancement; returns (success, text)."""
    token = hf_token.strip() or HF_TOKEN
    if not token:
        return False, "no provider key"
    hf = InferenceClient(token=token)
    result = hf.chat_completion(
        model="meta-llama/Llama-3.1-8B-Instruct", max_tokens=512,
        messages=[{"role": "system", "content": ENHANCE_SYSTEM}, {"role": "user", "content": p}],
    )
    return True, result.choices[0].message.content.strip()


@app.post("/api/prompt/enhance")
async def enhance_prompt(body: PromptEnhanceBody):
    """Use a fast AI model to improve a user's coding prompt."""
    try:
        p = (body.prompt or "").strip()
        if not p:
            return JSONResponse({"error": "prompt required"}, status_code=400)
        if body.provider in ("anthropic", "groq", "openai_compat"):
            success, result = _call_ai_provider(body, ENHANCE_SYSTEM, p, max_tokens=512)
        else:
            success, result = _enhance_with_hf(p, body.hf_token or "")
        if not success:
            return JSONResponse({"error": result}, status_code=400)
        return {"enhanced": result.strip()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class Msg(BaseModel):
    role: str = Field(max_length=20)
    content: str = Field(max_length=200_000)

class ChatBody(BaseModel):
    provider: str = Field(max_length=50)
    anthropic_key: Optional[str] = Field(default="", max_length=500)
    groq_key: Optional[str] = Field(default="", max_length=500)
    groq_model: Optional[str] = Field(default="llama-3.3-70b-versatile", max_length=200)
    hf_token: Optional[str] = Field(default="", max_length=500)
    hf_model: Optional[str] = Field(default="Qwen/Qwen2.5-Coder-32B-Instruct", max_length=200)
    openai_compat_key: Optional[str] = Field(default="", max_length=500)
    openai_compat_base_url: Optional[str] = Field(default="http://localhost:11434/v1", max_length=2000)
    openai_compat_model: Optional[str] = Field(default="llama3", max_length=200)
    agent: str = Field(default="code", max_length=50)
    messages: List[Msg] = Field(max_length=500)
    file_context: Optional[str] = Field(default="", max_length=500_000)
    owner: Optional[str] = Field(default="", max_length=100)
    repo: Optional[str] = Field(default="", max_length=100)
    branch: Optional[str] = Field(default="", max_length=255)
    skills: Optional[List[str]] = Field(default=[], max_length=12)
    rules: Optional[str] = Field(default="", max_length=10_000)
    instructions: Optional[str] = Field(default="", max_length=10_000)
    multi_agent: Optional[bool] = False
    # Per-stage provider overrides for multi-agent (empty = use body.provider)
    ma_plan_provider: Optional[str] = Field(default="", max_length=50)
    ma_code_provider: Optional[str] = Field(default="", max_length=50)
    ma_test_provider: Optional[str] = Field(default="", max_length=50)
    ma_review_provider: Optional[str] = Field(default="", max_length=50)
    ma_include_test_stage: Optional[bool] = False
    memory: Optional[str] = Field(default="", max_length=50_000)
    tools: Optional[List[ToolDef]] = Field(default=[], max_length=20)
    anthropic_model: Optional[str] = Field(default="claude-sonnet-4-6", max_length=200)
    thinking_mode: Optional[bool] = False
    thinking_budget: Optional[int] = Field(default=2000, ge=1000, le=100_000)
    airllm_model: Optional[str] = Field(default="meta-llama/Llama-2-7b-chat-hf", max_length=200)
    airllm_max_tokens: Optional[int] = Field(default=512, ge=1, le=4096)

_PROV_LABEL: dict = {"anthropic": "Claude", "groq": "Groq", "hf": "HF", "openai_compat": "Custom", "airllm": "AirLLM"}


def _get_anthropic_runner(body: "ChatBody") -> Callable:
    """Select the correct Anthropic run function (tools / thinking / plain)."""
    tools = getattr(body, 'tools', []) or []
    model = (getattr(body, 'anthropic_model', '') or 'claude-sonnet-4-6').strip() or 'claude-sonnet-4-6'
    thinking = bool(getattr(body, 'thinking_mode', False)) and 'opus' in model
    thinking_budget = int(getattr(body, 'thinking_budget', 2000) or 2000)
    if tools:
        return lambda q, loop, sys, msgs: _run_anthropic_with_tools(q, loop, sys, msgs, body.anthropic_key, tools, model)
    if thinking:
        return lambda q, loop, sys, msgs: _run_anthropic_thinking(q, loop, sys, msgs, body.anthropic_key, model, thinking_budget)
    return lambda q, loop, sys, msgs: _run_anthropic(q, loop, sys, msgs, body.anthropic_key, model)


def _get_openai_compat_runner(body: "ChatBody") -> Callable:
    """Validate openai_compat URL and return the run lambda."""
    oc_url = body.openai_compat_base_url or "http://localhost:11434/v1"
    if not _valid_http_url(oc_url):
        raise ValueError("openai_compat_base_url must be http:// or https://")
    return lambda q, loop, sys, msgs: _run_openai_compat(
        q, loop, sys, msgs,
        body.openai_compat_key or "",
        oc_url,
        body.openai_compat_model or "llama3",
    )


def get_runner(body: ChatBody, provider: str = "") -> Callable:
    """Return a thread-target callable bound to the chosen provider's run function.

    Args:
        body: Validated chat request carrying all credentials.
        provider: Provider key override; falls back to body.provider when empty.

    Returns:
        Callable accepting (queue, event_loop, system_prompt, messages).
    """
    p = provider if provider else body.provider
    if p == "anthropic":
        return _get_anthropic_runner(body)
    if p == "groq":
        return lambda q, loop, sys, msgs: _run_groq(q, loop, sys, msgs, body.groq_key, body.groq_model or "llama-3.3-70b-versatile")
    if p == "openai_compat":
        return _get_openai_compat_runner(body)
    if p == "airllm":
        al_model = (getattr(body, 'airllm_model', '') or 'meta-llama/Llama-2-7b-chat-hf').strip() or 'meta-llama/Llama-2-7b-chat-hf'
        al_max_tokens = int(getattr(body, 'airllm_max_tokens', 512) or 512)
        return lambda q, loop, sys, msgs: _run_airllm(q, loop, sys, msgs, al_model, al_max_tokens)
    token = (body.hf_token or "").strip() or HF_TOKEN
    return lambda q, loop, sys, msgs: _run_hf(q, loop, sys, msgs, token, body.hf_model)

def _build_ma_runners(body: "ChatBody") -> tuple:
    """Resolve multi-agent stage providers and return (prov, runner) pairs as an 8-tuple."""
    plan_prov   = body.ma_plan_provider   or body.provider
    code_prov   = body.ma_code_provider   or body.provider
    test_prov   = body.ma_test_provider   or body.provider
    review_prov = body.ma_review_provider or body.provider
    return (
        plan_prov,   get_runner(body, plan_prov),
        code_prov,   get_runner(body, code_prov),
        test_prov,   get_runner(body, test_prov),
        review_prov, get_runner(body, review_prov),
    )


async def _ma_stream_stage(runner, system: str, msgs: list, out: list):
    """Yield SSE chunks for one MA stage; append text to out (None sentinel on error)."""
    async for kind, val in stream_one(runner, system, msgs):
        if kind == "text":
            out.append(val)
            yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
        elif kind == "error":
            out.append(None)
            yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
            return


async def _multi_agent_stream(body: "ChatBody", messages: list):
    user_task = messages[-1]["content"] if messages else ""
    prior = messages[:-1]
    try:
        plan_prov, plan_runner, code_prov, code_runner, test_prov, test_runner, review_prov, review_runner = _build_ma_runners(body)
    except ValueError as exc:
        yield f"data: {json.dumps({'t': 'error', 'v': str(exc)})}\n\n"
        return

    yield f"data: {json.dumps({'t': 'step', 'v': 'plan', 'label': f'🗺️ Planning · {_PROV_LABEL.get(plan_prov, plan_prov)}'})}\n\n"
    plan_out: list = []
    plan_msgs = [{"role": "user", "content": f"Task: {user_task}\n\nCreate a clear step-by-step implementation plan. List files, key functions, and pitfalls. No code yet."}]
    async for chunk in _ma_stream_stage(plan_runner, MA_PLAN_SYSTEM, plan_msgs, plan_out):
        yield chunk
    if None in plan_out:
        return
    plan_text = "".join(plan_out)

    yield f"data: {json.dumps({'t': 'step', 'v': 'code', 'label': f'⚙️ Implementing · {_PROV_LABEL.get(code_prov, code_prov)}'})}\n\n"
    code_out: list = []
    code_msgs = prior + [{"role": "user", "content": f"{user_task}\n\n## Plan:\n{plan_text}"}]
    async for chunk in _ma_stream_stage(code_runner, build_system(body), code_msgs, code_out):
        yield chunk
    if None in code_out:
        return
    code_text = "".join(code_out)

    if body.ma_include_test_stage:
        yield f"data: {json.dumps({'t': 'step', 'v': 'test', 'label': f'🧪 Testing · {_PROV_LABEL.get(test_prov, test_prov)}'})}\n\n"
        test_out: list = []
        test_msgs = [{"role": "user", "content": f"Write comprehensive tests for this implementation:\n\n{code_text}"}]
        async for chunk in _ma_stream_stage(test_runner, MA_TEST_SYSTEM, test_msgs, test_out):
            yield chunk
        if None in test_out:
            return

    yield f"data: {json.dumps({'t': 'step', 'v': 'review', 'label': f'🔍 Reviewing · {_PROV_LABEL.get(review_prov, review_prov)}'})}\n\n"
    review_out: list = []
    review_msgs = [{"role": "user", "content": f"Review this implementation for bugs, security issues, missing error handling, and quality:\n\n{code_text}"}]
    async for chunk in _ma_stream_stage(review_runner, MA_REVIEW_SYSTEM, review_msgs, review_out):
        yield chunk
    if None in review_out:
        return

    yield f"data: {json.dumps({'t': 'done'})}\n\n"


@app.post("/api/chat/stream")
async def chat_stream(body: ChatBody):
    system = build_system(body)
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        runner = get_runner(body)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    async def single_stream():
        async for kind, val in stream_one(runner, system, messages):
            yield f"data: {json.dumps({'t': kind, 'v': val})}\n\n"
        yield f"data: {json.dumps({'t': 'done'})}\n\n"

    gen = _multi_agent_stream(body, messages) if body.multi_agent else single_stream()
    return StreamingResponse(gen, media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Agent Pipeline (LangGraph + Pinecone + Go data-plane) ────────────────────

_AGENT_NODE_LABELS: dict = {
    "retrieve":  "🔍 Retrieving context",
    "reasoning": "🧠 Planning tool calls",
    "execution": "⚡ Executing tools",
    "synthesis": "✍️ Synthesizing answer",
}

_AGENT_INITIAL_STATE: dict = {
    "messages": [],
    "rag_context": "",
    "tool_plan": None,
    "tool_results": None,
    "final_answer": "",
    "error": None,
    "retry_count": 0,
}


class AgentRunBody(BaseModel):
    task: str = Field(..., min_length=1, max_length=4000)


@app.post("/api/agent/run")
async def agent_run(body: AgentRunBody):
    if not _CONTROL_PLANE_AVAILABLE:
        return JSONResponse({"error": "control plane dependencies not installed"}, status_code=503)

    state = {**_AGENT_INITIAL_STATE, "task": body.task}

    async def event_stream():
        try:
            graph = _build_langgraph()
            async for update in graph.astream(state):
                for node_name, node_update in update.items():
                    label = _AGENT_NODE_LABELS.get(node_name, node_name)
                    yield f"data: {json.dumps({'t': 'node', 'v': node_name, 'label': label})}\n\n"
                    if node_name == "synthesis":
                        answer = (node_update or {}).get("final_answer") or ""
                        for i in range(0, max(len(answer), 1), 8):
                            chunk = answer[i:i + 8]
                            if chunk:
                                yield f"data: {json.dumps({'t': 'text', 'v': chunk})}\n\n"
                    err = (node_update or {}).get("error")
                    if err:
                        yield f"data: {json.dumps({'t': 'warn', 'v': str(err)})}\n\n"
            yield f"data: {json.dumps({'t': 'done'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'t': 'error', 'v': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class MemoryQueryBody(BaseModel):
    q: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=20)


@app.post("/api/memory/query")
async def memory_query(body: MemoryQueryBody):
    if not _CONTROL_PLANE_AVAILABLE:
        return JSONResponse({"error": "control plane dependencies not installed"}, status_code=503)
    context = _pinecone_query(body.q, top_k=body.top_k)
    return {"context": context, "found": bool(context)}


class MemoryUpsertBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    metadata: Optional[dict] = Field(default=None)


@app.post("/api/memory/upsert")
async def memory_upsert(body: MemoryUpsertBody):
    if not _CONTROL_PLANE_AVAILABLE:
        return JSONResponse({"error": "control plane dependencies not installed"}, status_code=503)
    ok = _pinecone_upsert(body.text, body.metadata)
    if ok:
        return {"stored": True}
    return JSONResponse({"stored": False, "error": "Pinecone not configured or upsert failed"}, status_code=503)


class GoToolsBody(BaseModel):
    task_id: str = Field(..., min_length=1, max_length=100)
    calls: List[dict] = Field(..., min_length=1, max_length=20)


@app.post("/api/tools/dispatch")
async def tools_dispatch(body: GoToolsBody):
    """Proxy a BatchRequest to the Go data-plane service."""
    go_url = os.environ.get("GO_DATA_PLANE_URL", "http://localhost:8080")
    if not re.match(r"^https?://", go_url):
        return JSONResponse({"error": "GO_DATA_PLANE_URL must be http:// or https://"}, status_code=400)
    timeout = int(os.environ.get("GO_CALL_TIMEOUT", "30"))
    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=float(timeout)) as http:
            resp = await http.post(f"{go_url}/tools/execute", json=body.model_dump())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=502)


class SidecarGrepBody(BaseModel):
    pattern: str = Field(..., min_length=1, max_length=500)
    root: str = Field(default=".", max_length=500)
    max_results: int = Field(default=50, ge=1, le=200)


@app.post("/api/sidecar/grep")
async def sidecar_grep(body: SidecarGrepBody):
    """Proxy regex code-search to the Go data-plane /grep endpoint."""
    go_url = os.environ.get("GO_DATA_PLANE_URL", "http://localhost:8080")
    if not re.match(r"^https?://", go_url):
        return JSONResponse(
            {"error": "GO_DATA_PLANE_URL not configured", "matches": [], "total": 0},
            status_code=503,
        )
    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.post(f"{go_url}/grep", json=body.model_dump())
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        return JSONResponse(
            {"error": str(exc), "matches": [], "total": 0}, status_code=502
        )


# ── Autonomous CI/CD: Branch creation ────────────────────────────────────────

class BranchCreateBody(BaseModel):
    token: str = Field(..., min_length=1, max_length=500)
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)
    new_branch: str = Field(..., min_length=1, max_length=255)
    from_branch: str = Field(default="main", min_length=1, max_length=255)


@app.post("/api/repo/branch/create")
async def branch_create(body: BranchCreateBody):
    """Create a new GitHub branch from an existing branch's HEAD SHA."""
    # Get the SHA of from_branch
    ref_url = f"{_gh_base(body.owner, body.repo)}/git/ref/heads/{_urlquote(body.from_branch, safe='')}"
    r = requests.get(ref_url, headers=gh_hdrs(body.token), timeout=10)
    if not r.ok:
        return JSONResponse({"error": f"Could not resolve branch '{body.from_branch}'"}, status_code=400)
    try:
        data = r.json()
        sha = data["object"]["sha"]
    except (KeyError, ValueError):
        return JSONResponse({"error": "Unexpected GitHub response resolving branch SHA"}, status_code=502)

    # Create the new branch ref
    payload = {"ref": f"refs/heads/{body.new_branch}", "sha": sha}
    r2 = requests.post(
        f"{_gh_base(body.owner, body.repo)}/git/refs",
        headers=gh_hdrs(body.token), json=payload, timeout=15,
    )
    if not r2.ok:
        try:
            msg = r2.json().get("message", "Failed to create branch")
        except Exception:
            msg = "Failed to create branch"
        return JSONResponse({"error": msg}, status_code=400)
    return {"branch": body.new_branch, "sha": sha}


# ── Autonomous CI/CD: Feature flags ──────────────────────────────────────────

from autonomous import flags as _flags_mod


class FlagCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    rollout_pct: int = Field(default=0, ge=0, le=100)


class FlagUpdateBody(BaseModel):
    description: Optional[str] = Field(default=None, max_length=500)
    enabled: Optional[bool] = Field(default=None)
    rollout_pct: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[str] = Field(default=None)


@app.get("/api/flags")
async def flags_list():
    """List all feature flags."""
    return {"flags": _flags_mod.get_all()}


@app.post("/api/flags")
async def flags_create(body: FlagCreateBody):
    """Create a new feature flag."""
    try:
        flag = _flags_mod.create(body.name, body.description, body.rollout_pct)
        return flag
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.patch("/api/flags/{name}")
async def flags_update(name: str, body: FlagUpdateBody):
    """Update fields on a feature flag."""
    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    if not kwargs:
        return JSONResponse({"error": "No fields to update"}, status_code=400)
    try:
        flag = _flags_mod.update(name, **kwargs)
        return flag
    except KeyError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.delete("/api/flags/{name}")
async def flags_delete(name: str):
    """Delete a feature flag by name."""
    deleted = _flags_mod.delete(name)
    if not deleted:
        return JSONResponse({"error": f"Flag '{name}' not found"}, status_code=404)
    return {"deleted": True, "name": name}


# ── Autonomous CI/CD: Canary analysis ────────────────────────────────────────

from autonomous import canary as _canary_mod


class CanaryAnalyzeBody(BaseModel):
    flag_name: str = Field(..., min_length=1, max_length=100)
    error_rate_canary: float = Field(..., ge=0.0)
    error_rate_baseline: float = Field(..., ge=0.0)
    latency_canary_ms: float = Field(..., ge=0.0)
    latency_baseline_ms: float = Field(..., ge=0.0)
    sample_size: int = Field(..., ge=0)


@app.post("/api/canary/analyze")
async def canary_analyze(body: CanaryAnalyzeBody):
    """Run canary health analysis and auto-update the flag's rollout_pct."""
    flag_data = next((f for f in _flags_mod.get_all() if f["name"] == body.flag_name), {})
    current_rollout_pct = int(flag_data.get("rollout_pct", 0))
    try:
        result = _canary_mod.analyze(
            flag_name=body.flag_name,
            error_rate_canary=body.error_rate_canary,
            error_rate_baseline=body.error_rate_baseline,
            latency_canary_ms=body.latency_canary_ms,
            latency_baseline_ms=body.latency_baseline_ms,
            sample_size=body.sample_size,
            current_rollout_pct=current_rollout_pct,
        )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    # Auto-update the flag rollout_pct if the flag exists
    if result["action"] in ("rollout", "rollback"):
        new_pct = result["next_rollout_pct"]
        if new_pct is not None:
            try:
                _flags_mod.update(body.flag_name, rollout_pct=new_pct)
            except KeyError:
                pass  # Flag not found — analysis result still returned
    return {**result, "flag_name": body.flag_name}


# ── Autonomous CI/CD: Rollbar webhook ────────────────────────────────────────

from fastapi import Request as _FastAPIRequest


@app.post("/api/webhooks/rollbar")
async def rollbar_webhook(request: _FastAPIRequest):
    """Receive a Rollbar error event and trigger autonomous fix."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    from autonomous.fixer import fix_from_rollbar_payload
    result = await fix_from_rollbar_payload(payload)
    return result


# ── Autonomous CI/CD: Manual fix trigger ─────────────────────────────────────

class ManualFixBody(BaseModel):
    owner: str = Field(..., min_length=1, max_length=100)
    repo: str = Field(..., min_length=1, max_length=100)
    token: str = Field(..., min_length=1, max_length=500)
    filename: str = Field(..., min_length=1, max_length=500)
    error_title: str = Field(..., min_length=1, max_length=500)
    trace_json: str = Field(default="", max_length=10000)


@app.post("/api/autonomous/fix")
async def autonomous_fix(body: ManualFixBody):
    """Manually trigger an autonomous fix for a known error."""
    payload = {
        "data": {
            "item": {
                "title": body.error_title,
                "id": "manual",
                "last_occurrence": {
                    "body": {
                        "trace": {
                            "frames": [{"filename": body.filename, "lineno": 0}]
                        }
                    }
                },
            }
        }
    }
    from autonomous.fixer import fix_from_rollbar_payload
    return await fix_from_rollbar_payload(
        payload,
        github_token=body.token,
        github_owner=body.owner,
        github_repo=body.repo,
    )


# ── Autonomous CI/CD: Evolution cycle ────────────────────────────────────────

from autonomous import audit as _audit_mod
from autonomous import evolution as _evolution_mod


class EvolutionMetrics(BaseModel):
    error_rate_canary: float = Field(..., ge=0.0, description="Canary error rate %")
    error_rate_baseline: float = Field(..., ge=0.0, description="Baseline error rate %")
    latency_canary_ms: float = Field(..., gt=0.0, description="Canary p95 latency ms")
    latency_baseline_ms: float = Field(..., gt=0.0, description="Baseline p95 latency ms")
    sample_size: int = Field(..., ge=0, description="Number of canary requests observed")


class EvolutionRunBody(BaseModel):
    metrics: EvolutionMetrics
    flag_name: Optional[str] = Field(default=None, max_length=100)
    github_token: str = Field(default="", max_length=500)
    github_owner: str = Field(default="", max_length=100)
    github_repo: str = Field(default="", max_length=100)
    use_real_metrics: bool = Field(
        default=False,
        description=(
            "When True, fetch real canary metrics from PostHog/Rollbar APIs "
            "and override the supplied metrics values. Falls back to the "
            "supplied metrics when real data is unavailable."
        ),
    )
    metrics_hours: int = Field(default=1, ge=1, le=24, description="Hours of history to query for real metrics")


def _resolve_real_metrics(flag_name: str, fallback: dict, use_real: bool, hours: int) -> dict:
    """Fetch PostHog metrics for a flag if use_real is True; fall back to supplied values."""
    if not use_real:
        return fallback
    from autonomous import metrics as _metrics_mod
    real = _metrics_mod.fetch_metrics_for_flag(flag_name, hours=hours)
    if real.get("source") == "posthog":
        return {
            "error_rate_canary": real["error_rate_canary"],
            "error_rate_baseline": real["error_rate_baseline"],
            "latency_canary_ms": max(0.001, real["latency_canary_ms"]),
            "latency_baseline_ms": max(0.001, real["latency_baseline_ms"]),
            "sample_size": real["sample_size"],
        }
    return fallback


@app.post("/api/evolution/run")
async def evolution_run(body: EvolutionRunBody):
    """Run one evolution cycle iteration for all canary flags (or a specific flag)."""
    token = body.github_token or os.environ.get("GITHUB_TOKEN", "")
    owner = body.github_owner or os.environ.get("GITHUB_OWNER", "")
    repo = body.github_repo or os.environ.get("GITHUB_REPO", "")
    metrics = body.metrics.model_dump()
    gh_kwargs = {"github_token": token, "github_owner": owner, "github_repo": repo}
    if body.flag_name:
        effective = await asyncio.to_thread(
            _resolve_real_metrics, body.flag_name, metrics, body.use_real_metrics, body.metrics_hours
        )
        result = await _evolution_mod.run_cycle(body.flag_name, effective, **gh_kwargs)
        return {"results": [result]}
    flags = [f for f in _flags_mod.get_all() if f.get("status") in ("canary", "dark") and f.get("enabled", True)]
    if body.use_real_metrics:
        tasks = [
            _evolution_mod.run_cycle(
                f["name"],
                await asyncio.to_thread(_resolve_real_metrics, f["name"], metrics, True, body.metrics_hours),
                **gh_kwargs,
            )
            for f in flags
        ]
        results = list(await asyncio.gather(*tasks)) if tasks else []
    else:
        results = await _evolution_mod.run_all_canary_flags(metrics, **gh_kwargs)
    return {"results": results}


@app.get("/api/evolution/history")
async def evolution_history(flag: Optional[str] = Query(default=None, max_length=100), limit: int = Query(default=50, ge=1, le=200)):
    """Return recent evolution cycle decisions from the audit log."""
    return {"history": _audit_mod.get_history(flag_name=flag, limit=limit)}


# ── Autonomous CI/CD: Live metrics ───────────────────────────────────────────

@app.get("/api/metrics/live")
async def metrics_live(
    flag: str = Query(..., min_length=1, max_length=100),
    hours: int = Query(default=1, ge=1, le=24),
):
    """Fetch real canary vs baseline metrics for a flag from PostHog and Rollbar.

    Returns a source indicator: 'posthog', 'rollbar_partial', or 'unavailable'.
    """
    from autonomous import metrics as _metrics_mod

    result = await asyncio.to_thread(
        _metrics_mod.fetch_metrics_for_flag,
        flag,
        hours=hours,
    )
    return result


# ── Autonomous CI/CD: Flag check ─────────────────────────────────────────────

@app.get("/api/flags/{name}/check")
async def flag_check(name: str, user_id: str = Query(default="", max_length=200)):
    """Check if a feature flag is enabled for a specific user_id (hash-based routing)."""
    enabled = _flags_mod.is_flag_enabled(name, user_id)
    flag_data = next((f for f in _flags_mod.get_all() if f["name"] == name), None)
    if flag_data is None:
        return JSONResponse({"error": f"Flag '{name}' not found"}, status_code=404)
    return {
        "flag": name,
        "enabled": enabled,
        "bucket": "canary" if enabled else "control",
        "rollout_pct": flag_data.get("rollout_pct", 0),
        "status": flag_data.get("status", "dark"),
    }


# ── HF Spaces build status ────────────────────────────────────────────────────

@app.get("/api/hf-build/status")
async def hf_build_status():
    """Proxy the HF Spaces runtime stage so the dashboard can show a live build badge."""
    try:
        r = requests.get(
            "https://huggingface.co/api/spaces/vooom/devforge/runtime",
            timeout=10,
        )
        if not r.ok:
            return JSONResponse(
                {"stage": "UNKNOWN", "error": f"HF API {r.status_code}"},
                status_code=502,
            )
        data = r.json()
        return {
            "stage": data.get("stage", "UNKNOWN"),
            "error_message": data.get("errorMessage") or "",
        }
    except Exception as exc:
        return JSONResponse({"stage": "UNKNOWN", "error": str(exc)}, status_code=502)


# ── Headless Browser endpoints ───────────────────────────────────────────────
_CHROME_EXEC = os.environ.get(
    "CHROME_EXECUTABLE",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
)
_BROWSER_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]


class BrowserScreenshotBody(BaseModel):
    url: str = Field(..., description="URL to screenshot")
    width: int = Field(1280, ge=320, le=1920)
    height: int = Field(800, ge=240, le=1080)
    full_page: bool = False
    wait_until: str = "networkidle"


class BrowserScrapeBody(BaseModel):
    url: str = Field(..., description="URL to scrape")
    wait_until: str = "networkidle"


def _check_chrome() -> str | None:
    """Return error message if Chrome is not available."""
    if not os.path.exists(_CHROME_EXEC):
        return f"Chrome not found at {_CHROME_EXEC}. Set CHROME_EXECUTABLE env var."
    return None


@app.post("/api/browser/screenshot")
async def browser_screenshot(body: BrowserScreenshotBody):
    """Take a screenshot of a URL and return it as a base64-encoded PNG."""
    if err := _check_chrome():
        return JSONResponse({"error": err}, status_code=503)
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                executable_path=_CHROME_EXEC,
                headless=True,
                args=_BROWSER_LAUNCH_ARGS,
            )
            try:
                page = await browser.new_page(
                    viewport={"width": body.width, "height": body.height}
                )
                await page.goto(body.url, wait_until=body.wait_until, timeout=30000)
                png_bytes = await page.screenshot(full_page=body.full_page)
            finally:
                await browser.close()
        return {
            "url": body.url,
            "image": base64.b64encode(png_bytes).decode(),
            "mime": "image/png",
        }
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/browser/scrape")
async def browser_scrape(body: BrowserScrapeBody):
    """Load a URL with JS rendering and return the page title and text content."""
    if err := _check_chrome():
        return JSONResponse({"error": err}, status_code=503)
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                executable_path=_CHROME_EXEC,
                headless=True,
                args=_BROWSER_LAUNCH_ARGS,
            )
            try:
                page = await browser.new_page()
                await page.goto(body.url, wait_until=body.wait_until, timeout=30000)
                title = await page.title()
                text = await page.evaluate("() => document.body.innerText")
            finally:
                await browser.close()
        return {"url": body.url, "title": title, "text": text[:20000]}
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/admin/status")
async def admin_status():
    """Return non-sensitive server configuration status for the control panel."""
    pinecone_set = bool(os.environ.get("PINECONE_API_KEY") or os.environ.get("PINECONE_INDEX"))
    go_url = os.environ.get("GO_DATA_PLANE_URL", "http://localhost:8080")
    return {
        "env": {
            "GITHUB_CLIENT_ID": bool(GITHUB_CLIENT_ID),
            "GITHUB_CLIENT_SECRET": bool(os.environ.get("GITHUB_CLIENT_SECRET")),
            "HF_TOKEN": bool(os.environ.get("HF_TOKEN")),
            "SENTRY_DSN": bool(os.environ.get("SENTRY_DSN")),
            "ROLLBAR_ACCESS_TOKEN": bool(os.environ.get("ROLLBAR_ACCESS_TOKEN")),
            "POSTHOG_API_KEY": bool(os.environ.get("POSTHOG_API_KEY")),
            "PINECONE": pinecone_set,
            "GO_DATA_PLANE_URL": go_url,
            "CHROME_EXECUTABLE": _CHROME_EXEC,
        },
        "features": {
            "headless_browser": os.path.exists(_CHROME_EXEC),
            "memory": pinecone_set,
            "go_data_plane": go_url != "http://localhost:8080",
            "github_oauth": bool(GITHUB_CLIENT_ID),
        },
    }
