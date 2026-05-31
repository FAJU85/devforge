from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Callable, List, Optional
import json, os, requests, base64, re, asyncio, threading

from anthropic import Anthropic
from huggingface_hub import InferenceClient

app = FastAPI(title="DevForge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

GITHUB_CLIENT_ID     = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
HF_TOKEN             = os.environ.get("HF_TOKEN", "")

AGENT_PROMPTS = {
    "code":      "You are an expert coding agent. Write high-quality, production-ready code. Always show the full file path before every code block. Explain every change clearly.",
    "review":    "You are an expert code reviewer. Find bugs, security vulnerabilities, performance issues, and bad patterns. Give specific, actionable feedback with improved code snippets.",
    "architect": "You are a software architect. Design scalable, maintainable systems. Provide folder structures, interfaces, and tech decisions with clear reasoning.",
    "debug":     "You are a debugging specialist. Find root causes of errors. Provide complete, tested fixes with clear explanations.",
    "docs":      "You are a technical writer. Write clear, comprehensive documentation with usage examples, parameter descriptions, return values, and edge cases.",
    "refactor":  "You are a refactoring expert. Restructure code to improve readability, maintainability, and performance without changing behavior. Identify code smells, apply SOLID principles, extract methods, reduce complexity, and eliminate duplication. Always show the full file path before code blocks and explain each refactoring decision.",
    "testgen":   "You are a test generation expert. Write comprehensive test suites that cover all code paths. Include unit tests, integration tests, edge cases, and error conditions. Use the appropriate testing framework for the language. Show full file paths before every test file. Aim for high coverage and clear test names that document behavior.",
}

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

def build_system(body: "ChatBody") -> str:
    """Compose the system prompt from agent, skills, rules, file context, and session memory."""
    if getattr(body, 'instructions', '') and body.instructions.strip():
        base = body.instructions.strip()
    else:
        base = AGENT_PROMPTS.get(body.agent, AGENT_PROMPTS["code"])
    if body.owner and body.repo:
        base += f"\n\nRepository: {body.owner}/{body.repo}. Always specify full file paths."
    skills = getattr(body, 'skills', []) or []
    if skills:
        base += "\n\n## Active Skills:\n"
        for s in skills:
            if s in SKILL_PROMPTS:
                base += f"{SKILL_PROMPTS[s]}\n\n"
    rules = (getattr(body, 'rules', '') or '').strip()
    if rules:
        base += f"\n\n## Rules (must follow):\n{rules}"
    memory = (getattr(body, 'memory', '') or '').strip()
    if memory:
        base += f"\n\n## Previous Session Context (from last conversation on this repo):\n{memory}"
    tools = getattr(body, 'tools', []) or []
    if tools and body.provider != "anthropic":
        base += "\n\n## Available Tools:\n"
        for t in tools:
            base += f"- **{t.name}**: {t.description} ({t.method} {t.url})\n"
        base += "\nDescribe needed tool calls in your response; the user will execute them and share results."
    fc = (getattr(body, 'file_context', '') or '').strip()
    if fc:
        base += f"\n\n---\n**Repository context:**\n{fc}"
    return base

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
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

def _run_anthropic_with_tools(q, loop, system, messages, api_key, tools, model="claude-sonnet-4-6"):
    """Run Anthropic with native tool use, executing HTTP calls and looping until done."""
    try:
        client = Anthropic(api_key=api_key)
        anth_tools = [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema or {"type": "object", "properties": {}},
            }
            for t in tools
        ]
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

            # Serialize assistant content for next turn
            assistant_content = []
            for block in msg.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
            current_messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in msg.content:
                if block.type != "tool_use":
                    continue
                asyncio.run_coroutine_threadsafe(
                    q.put(("tool_call", {"id": block.id, "name": block.name, "input": block.input})), loop
                )
                tool_def = next((t for t in tools if t.name == block.name), None)
                if not tool_def:
                    result_content = f"Error: Tool '{block.name}' not found"
                else:
                    try:
                        hdrs = dict(tool_def.headers or {})
                        url = tool_def.url
                        inp = block.input or {}
                        for k, v in inp.items():
                            url = url.replace(f"{{{k}}}", str(v))
                        if tool_def.method.upper() == "GET":
                            params = {k: v for k, v in inp.items() if f"{{{k}}}" not in tool_def.url}
                            r = requests.get(url, headers=hdrs, params=params, timeout=15)
                        else:
                            hdrs.setdefault("Content-Type", "application/json")
                            r = requests.request(tool_def.method.upper(), url, headers=hdrs, json=inp, timeout=15)
                        result_content = r.text[:2000]
                    except Exception as e:
                        result_content = f"Error: {e}"
                asyncio.run_coroutine_threadsafe(
                    q.put(("tool_result", {"id": block.id, "name": block.name, "result": result_content})), loop
                )
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_content})
            current_messages.append({"role": "user", "content": tool_results})

        asyncio.run_coroutine_threadsafe(q.put(("usage", total_usage)), loop)
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

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
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

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
        hf = InferenceClient(model=model, token=token) if token else InferenceClient(model=model)
        msgs = [{"role": "system", "content": system}] + messages
        for tok in hf.chat_completion(messages=msgs, max_tokens=4096, stream=True):
            text = tok.choices[0].delta.content or ""
            if text:
                asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

def _run_openai_compat(q, loop, system, messages, api_key, base_url, model):
    """Thread target: stream completions from any OpenAI-compatible endpoint.

    Args:
        q: asyncio.Queue for (kind, value) tuples sent back to the async caller.
        loop: Running event loop used to schedule coroutines thread-safely.
        system: System prompt string.
        messages: List of {role, content} message dicts.
        api_key: Bearer token; omitted from headers when empty (e.g. Ollama).
        base_url: Root URL of the endpoint, e.g. http://localhost:11434/v1.
        model: Model identifier forwarded in the request body.

    Returns:
        None. Results are placed on q as ("text", chunk), ("done", None),
        or ("error", message).
    """
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
            if decoded.startswith("data: "):
                data = decoded[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    text = obj["choices"][0]["delta"].get("content") or ""
                    if text:
                        asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
                except json.JSONDecodeError:
                    pass
                except (KeyError, IndexError):
                    pass
        asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)
    except Exception as e:
        asyncio.run_coroutine_threadsafe(q.put(("error", str(e))), loop)

async def stream_one(runner, system: str, messages: list):
    q: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
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

@app.get("/api/hf/models")
async def search_hf_models(q: str = Query(default=""), limit: int = Query(default=25)):
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

@app.post("/api/github/auth/start")
async def github_auth_start():
    if not GITHUB_CLIENT_ID: return JSONResponse({"error": "GITHUB_CLIENT_ID not set."}, status_code=500)
    r = requests.post("https://github.com/login/device/code", headers={"Accept": "application/json"},
        data={"client_id": GITHUB_CLIENT_ID, "scope": "repo read:user"}, timeout=10)
    return JSONResponse(r.json(), status_code=200 if r.ok else 500)

class DeviceCodeBody(BaseModel):
    device_code: str

@app.post("/api/github/auth/poll")
async def github_auth_poll(body: DeviceCodeBody):
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return JSONResponse({"error": "credentials_missing"}, status_code=500)
    r = requests.post("https://github.com/login/oauth/access_token", headers={"Accept": "application/json"},
        data={"client_id": GITHUB_CLIENT_ID, "client_secret": GITHUB_CLIENT_SECRET,
              "device_code": body.device_code, "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}, timeout=10)
    return JSONResponse(r.json())

class TokenBody(BaseModel):
    token: str

@app.post("/api/github/user")
async def github_user(body: TokenBody):
    r = requests.get("https://api.github.com/user",
        headers={"Authorization": f"token {body.token}", "Accept": "application/vnd.github.v3+json"}, timeout=10)
    return JSONResponse(r.json(), status_code=200 if r.ok else 400)

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
    return [{"full_name": r["full_name"], "name": r["name"], "description": r.get("description") or "",
             "private": r["private"], "language": r.get("language") or ""} for r in repos]

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
        if m2: return m2.group(1), m2.group(2).replace(".git", "")
        return None, None
    return m.group(1), m.group(2).replace(".git", "").rstrip("/")

def gh_hdrs(token: str) -> dict:
    """Build GitHub API request headers for an authenticated token.

    Args:
        token: Personal access token or OAuth token for GitHub API calls.

    Returns:
        Dict with Authorization and Accept headers.
    """
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

class RepoBody(BaseModel):
    token: str
    url: str
    branch: Optional[str] = ""


@app.get("/api/repo/branches")
async def list_branches(token: str = Query(...), owner: str = Query(...), repo: str = Query(...)):
    """List all branches for a repository."""
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/branches?per_page=100",
        headers=gh_hdrs(token), timeout=15,
    )
    if not r.ok:
        return JSONResponse({"error": "Failed to fetch branches"}, status_code=400)
    return [{"name": b["name"], "sha": b["commit"]["sha"][:7]} for b in r.json()]


@app.post("/api/repo/connect")
async def repo_connect(body: RepoBody):
    owner, repo = parse_gh_url(body.url)
    if not owner: return JSONResponse({"error": "Invalid repository"}, status_code=400)
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=gh_hdrs(body.token), timeout=10)
    if not r.ok: return JSONResponse({"error": r.json().get("message", "Not found")}, status_code=400)
    default_branch = r.json()["default_branch"]
    branch = (body.branch or "").strip() or default_branch
    t = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=gh_hdrs(body.token), timeout=15)
    if not t.ok: return JSONResponse({"error": "Failed to fetch file tree"}, status_code=400)
    files = sorted([{"path": f["path"], "size": f.get("size", 0)} for f in t.json().get("tree", [])
        if f["type"] == "blob" and f.get("size", 999999) < 150000], key=lambda x: x["path"])
    return {"owner": owner, "repo": repo, "branch": branch, "default_branch": default_branch, "files": files}

class FileBody(BaseModel):
    token: str; owner: str; repo: str; path: str

@app.post("/api/repo/file")
async def repo_file(body: FileBody):
    r = requests.get(f"https://api.github.com/repos/{body.owner}/{body.repo}/contents/{body.path}",
        headers=gh_hdrs(body.token), timeout=10)
    if not r.ok: return JSONResponse({"error": f"Cannot fetch {body.path}"}, status_code=400)
    try:
        content = base64.b64decode(r.json()["content"].replace("\n", "")).decode("utf-8", errors="replace")
    except Exception:
        return JSONResponse({"error": "Binary file"}, status_code=400)
    return {"path": body.path, "content": content}

class WriteFileBody(BaseModel):
    token: str
    owner: str
    repo: str
    path: str
    content: str
    message: str
    branch: str

@app.post("/api/repo/write")
async def repo_write(body: WriteFileBody):
    """Create or update a file in the repository via the GitHub Contents API."""
    sha = None
    existing = requests.get(
        f"https://api.github.com/repos/{body.owner}/{body.repo}/contents/{body.path}",
        headers=gh_hdrs(body.token), params={"ref": body.branch}, timeout=10,
    )
    if existing.ok:
        try:
            sha = existing.json().get("sha")
        except (KeyError, json.JSONDecodeError):
            pass

    payload: dict = {
        "message": body.message,
        "content": base64.b64encode(body.content.encode("utf-8")).decode("utf-8"),
        "branch": body.branch,
    }
    if sha:
        payload["sha"] = sha

    w = requests.put(
        f"https://api.github.com/repos/{body.owner}/{body.repo}/contents/{body.path}",
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
    provider: str
    anthropic_key: Optional[str] = ""
    groq_key: Optional[str] = ""
    groq_model: Optional[str] = "llama-3.3-70b-versatile"
    openai_compat_key: Optional[str] = ""
    openai_compat_base_url: Optional[str] = ""
    openai_compat_model: Optional[str] = ""
    hf_token: Optional[str] = ""
    hf_model: Optional[str] = ""
    task: str
    files: List[str]
    max_suggestions: int = 6

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

    result = ""
    try:
        if body.provider == "anthropic" and body.anthropic_key:
            from anthropic import Anthropic as _Anth
            client = _Anth(api_key=body.anthropic_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            result = msg.content[0].text if msg.content else "[]"
        elif body.provider == "groq" and body.groq_key:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {body.groq_key}", "Content-Type": "application/json"},
                json={"model": body.groq_model or "llama-3.1-8b-instant", "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ], "max_tokens": 256, "stream": False},
                timeout=20,
            )
            result = r.json()["choices"][0]["message"]["content"] if r.ok else "[]"
        elif body.provider == "openai_compat" and body.openai_compat_base_url:
            url = body.openai_compat_base_url.rstrip("/") + "/chat/completions"
            hdrs = {"Content-Type": "application/json"}
            if body.openai_compat_key:
                hdrs["Authorization"] = f"Bearer {body.openai_compat_key}"
            r = requests.post(url, headers=hdrs, json={
                "model": body.openai_compat_model or "llama3",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "max_tokens": 256, "stream": False,
            }, timeout=20)
            result = r.json()["choices"][0]["message"]["content"] if r.ok else "[]"
        else:
            return JSONResponse({"error": "No usable provider configured"}, status_code=400)

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
    content: str
    filename: str
    provider: str
    anthropic_key: Optional[str] = ""
    groq_key: Optional[str] = ""
    groq_model: Optional[str] = "llama-3.3-70b-versatile"
    openai_compat_key: Optional[str] = ""
    openai_compat_base_url: Optional[str] = ""
    openai_compat_model: Optional[str] = ""


@app.post("/api/repo/summarize-file")
async def summarize_file(body: SummarizeFileBody):
    """Condense a large file to a short AI-generated summary for context injection."""
    system = "You are a code summarizer. Produce a concise summary (under 400 words) of the file: its purpose, key exports/functions/classes, and important patterns. Be specific and technical."
    prompt = f"File: {body.filename}\n\n```\n{body.content[:8000]}\n```\n\nSummarize this file for AI context."
    try:
        if body.provider == "anthropic" and body.anthropic_key:
            client = Anthropic(api_key=body.anthropic_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            result = msg.content[0].text if msg.content else ""
        elif body.provider == "groq" and body.groq_key:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {body.groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-8b-instant", "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ], "max_tokens": 600, "stream": False},
                timeout=20,
            )
            result = r.json()["choices"][0]["message"]["content"] if r.ok else ""
        elif body.provider == "openai_compat" and body.openai_compat_base_url:
            url = body.openai_compat_base_url.rstrip("/") + "/chat/completions"
            hdrs = {"Content-Type": "application/json"}
            if body.openai_compat_key:
                hdrs["Authorization"] = f"Bearer {body.openai_compat_key}"
            r = requests.post(url, headers=hdrs, json={
                "model": body.openai_compat_model or "llama3",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "max_tokens": 600, "stream": False,
            }, timeout=20)
            result = r.json()["choices"][0]["message"]["content"] if r.ok else ""
        else:
            return JSONResponse({"error": "No usable provider configured"}, status_code=400)
        if not result:
            return JSONResponse({"error": "Empty summary returned"}, status_code=400)
        return {"summary": result}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class BatchWriteItem(BaseModel):
    path: str
    content: str
    message: str

class BatchWriteBody(BaseModel):
    token: str
    owner: str
    repo: str
    branch: str
    files: List[BatchWriteItem]

@app.post("/api/repo/write/batch")
async def repo_write_batch(body: BatchWriteBody):
    """Commit multiple files to the repository, reporting per-file results."""
    committed, errors = [], []
    for item in body.files:
        sha = None
        existing = requests.get(
            f"https://api.github.com/repos/{body.owner}/{body.repo}/contents/{item.path}",
            headers=gh_hdrs(body.token), params={"ref": body.branch}, timeout=10,
        )
        if existing.ok:
            try:
                sha = existing.json().get("sha")
            except Exception:
                pass
        payload: dict = {
            "message": item.message,
            "content": base64.b64encode(item.content.encode("utf-8")).decode("utf-8"),
            "branch": body.branch,
        }
        if sha:
            payload["sha"] = sha
        w = requests.put(
            f"https://api.github.com/repos/{body.owner}/{body.repo}/contents/{item.path}",
            headers=gh_hdrs(body.token), json=payload, timeout=15,
        )
        if w.ok:
            data = w.json()
            committed.append({
                "path": item.path,
                "commit_url": data.get("commit", {}).get("html_url", ""),
            })
        else:
            try:
                err_msg = w.json().get("message", "Write failed")
            except Exception:
                err_msg = "Write failed"
            errors.append({"path": item.path, "error": err_msg})
    return {"committed": committed, "errors": errors}


class IssueBody(BaseModel):
    token: str
    owner: str
    repo: str
    title: str
    body: str
    labels: Optional[List[str]] = []

@app.post("/api/github/issue/create")
async def create_issue(body: IssueBody):
    """Create a GitHub issue in the connected repository."""
    r = requests.post(
        f"https://api.github.com/repos/{body.owner}/{body.repo}/issues",
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
    token: str
    owner: str
    repo: str
    title: str
    body: str
    head: str
    base: str

@app.post("/api/github/pr/create")
async def create_pr(body: PRBody):
    """Create a GitHub pull request from head branch into base branch."""
    r = requests.post(
        f"https://api.github.com/repos/{body.owner}/{body.repo}/pulls",
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


class RepoSearchBody(BaseModel):
    token: str
    owner: str
    repo: str
    query: str
    max_results: int = 10


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
    items = []
    for item in r.json().get("items", []):
        snippets = []
        for tm in item.get("text_matches", []):
            for m in tm.get("matches", []):
                t = (m.get("text") or "").strip()
                if t:
                    snippets.append(t[:120])
        items.append({
            "path": item["path"],
            "sha": (item.get("sha") or "")[:7],
            "url": item.get("html_url", ""),
            "snippets": snippets[:3],
        })
    return {"items": items, "total": r.json().get("total_count", 0)}


class RepoCommitsBody(BaseModel):
    token: str
    owner: str
    repo: str
    branch: Optional[str] = "main"
    max_results: int = 10


@app.post("/api/repo/commits")
async def repo_commits(body: RepoCommitsBody):
    """Fetch recent commits for a branch."""
    r = requests.get(
        f"https://api.github.com/repos/{body.owner}/{body.repo}/commits",
        headers=gh_hdrs(body.token),
        params={"sha": body.branch or "main", "per_page": min(body.max_results, 30)},
        timeout=15,
    )
    if not r.ok:
        return JSONResponse({"error": "Failed to fetch commits"}, status_code=400)
    return [
        {
            "sha": c["sha"][:7],
            "message": (c["commit"]["message"].split("\n")[0])[:80],
            "author": c["commit"]["author"]["name"][:30],
            "date": c["commit"]["author"]["date"][:10],
            "url": c.get("html_url", ""),
        }
        for c in r.json()
    ]


class ToolDef(BaseModel):
    name: str
    description: str
    url: str
    method: str = "GET"
    headers: Optional[dict] = {}
    input_schema: Optional[dict] = None


class ToolCallBody(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = {}
    body_json: Optional[dict] = None


@app.post("/api/tools/call")
async def call_tool(body: ToolCallBody):
    """Proxy a user-defined tool HTTP call to avoid CORS issues."""
    try:
        hdrs = dict(body.headers or {})
        if body.method.upper() != "GET":
            hdrs.setdefault("Content-Type", "application/json")
        if body.method.upper() == "GET":
            r = requests.get(body.url, headers=hdrs, timeout=15)
        else:
            r = requests.request(body.method.upper(), body.url, headers=hdrs, json=body.body_json, timeout=15)
        return {"status": r.status_code, "response": r.text[:2000]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class Msg(BaseModel):
    role: str; content: str

class ChatBody(BaseModel):
    provider: str
    anthropic_key: Optional[str] = ""
    groq_key: Optional[str] = ""
    groq_model: Optional[str] = "llama-3.3-70b-versatile"
    hf_token: Optional[str] = ""
    hf_model: Optional[str] = "Qwen/Qwen2.5-Coder-32B-Instruct"
    openai_compat_key: Optional[str] = ""
    openai_compat_base_url: Optional[str] = "http://localhost:11434/v1"
    openai_compat_model: Optional[str] = "llama3"
    agent: str = "code"
    messages: List[Msg]
    file_context: Optional[str] = ""
    owner: Optional[str] = ""
    repo: Optional[str] = ""
    skills: Optional[List[str]] = []
    rules: Optional[str] = ""
    instructions: Optional[str] = ""
    multi_agent: Optional[bool] = False
    # Per-stage provider overrides for multi-agent (empty = use body.provider)
    ma_plan_provider: Optional[str] = ""
    ma_code_provider: Optional[str] = ""
    ma_test_provider: Optional[str] = ""
    ma_review_provider: Optional[str] = ""
    ma_include_test_stage: Optional[bool] = False
    memory: Optional[str] = ""
    tools: Optional[List[ToolDef]] = []
    anthropic_model: Optional[str] = "claude-sonnet-4-6"
    thinking_mode: Optional[bool] = False
    thinking_budget: Optional[int] = 2000

_PROV_LABEL: dict = {"anthropic": "Claude", "groq": "Groq", "hf": "HF", "openai_compat": "Custom"}

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
        tools = getattr(body, 'tools', []) or []
        model = (getattr(body, 'anthropic_model', '') or 'claude-sonnet-4-6').strip() or 'claude-sonnet-4-6'
        thinking = bool(getattr(body, 'thinking_mode', False)) and 'opus' in model
        thinking_budget = int(getattr(body, 'thinking_budget', 2000) or 2000)
        if tools:
            return lambda q, loop, sys, msgs: _run_anthropic_with_tools(q, loop, sys, msgs, body.anthropic_key, tools, model)
        if thinking:
            return lambda q, loop, sys, msgs: _run_anthropic_thinking(q, loop, sys, msgs, body.anthropic_key, model, thinking_budget)
        return lambda q, loop, sys, msgs: _run_anthropic(q, loop, sys, msgs, body.anthropic_key, model)
    elif p == "groq":
        return lambda q, loop, sys, msgs: _run_groq(q, loop, sys, msgs, body.groq_key, body.groq_model or "llama-3.3-70b-versatile")
    elif p == "openai_compat":
        return lambda q, loop, sys, msgs: _run_openai_compat(
            q, loop, sys, msgs,
            body.openai_compat_key or "",
            body.openai_compat_base_url or "http://localhost:11434/v1",
            body.openai_compat_model or "llama3",
        )
    else:
        token = (body.hf_token or "").strip() or HF_TOKEN
        return lambda q, loop, sys, msgs: _run_hf(q, loop, sys, msgs, token, body.hf_model)

@app.post("/api/chat/stream")
async def chat_stream(body: ChatBody):
    system = build_system(body)
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    runner = get_runner(body)

    async def single_stream():
        async for kind, val in stream_one(runner, system, messages):
            yield f"data: {json.dumps({'t': kind, 'v': val})}\n\n"
        yield f"data: {json.dumps({'t': 'done'})}\n\n"

    async def multi_agent_stream():
        user_task = messages[-1]["content"] if messages else ""
        prior = messages[:-1]

        plan_prov   = body.ma_plan_provider   or body.provider
        code_prov   = body.ma_code_provider   or body.provider
        test_prov   = body.ma_test_provider   or body.provider
        review_prov = body.ma_review_provider or body.provider
        plan_runner   = get_runner(body, plan_prov)
        code_runner   = get_runner(body, code_prov)
        test_runner   = get_runner(body, test_prov)
        review_runner = get_runner(body, review_prov)

        yield f"data: {json.dumps({'t': 'step', 'v': 'plan', 'label': f'🗺️ Planning · {_PROV_LABEL.get(plan_prov, plan_prov)}'})}\n\n"
        plan_text = ""
        plan_msgs = [{"role": "user", "content": f"Task: {user_task}\n\nCreate a clear step-by-step implementation plan. List files, key functions, and pitfalls. No code yet."}]
        async for kind, val in stream_one(plan_runner, MA_PLAN_SYSTEM, plan_msgs):
            if kind == "text":
                plan_text += val
                yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                return

        yield f"data: {json.dumps({'t': 'step', 'v': 'code', 'label': f'⚙️ Implementing · {_PROV_LABEL.get(code_prov, code_prov)}'})}\n\n"
        code_text = ""
        code_system = build_system(body)
        code_msgs = prior + [{"role": "user", "content": f"{user_task}\n\n## Plan:\n{plan_text}"}]
        async for kind, val in stream_one(code_runner, code_system, code_msgs):
            if kind == "text":
                code_text += val
                yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                return

        if body.ma_include_test_stage:
            yield f"data: {json.dumps({'t': 'step', 'v': 'test', 'label': f'🧪 Testing · {_PROV_LABEL.get(test_prov, test_prov)}'})}\n\n"
            test_msgs = [{"role": "user", "content": f"Write comprehensive tests for this implementation:\n\n{code_text}"}]
            async for kind, val in stream_one(test_runner, MA_TEST_SYSTEM, test_msgs):
                if kind == "text":
                    yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
                elif kind == "error":
                    yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                    return

        yield f"data: {json.dumps({'t': 'step', 'v': 'review', 'label': f'🔍 Reviewing · {_PROV_LABEL.get(review_prov, review_prov)}'})}\n\n"
        review_msgs = [{"role": "user", "content": f"Review this implementation for bugs, security issues, missing error handling, and quality:\n\n{code_text}"}]
        async for kind, val in stream_one(review_runner, MA_REVIEW_SYSTEM, review_msgs):
            if kind == "text":
                yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                return

        yield f"data: {json.dumps({'t': 'done'})}\n\n"

    gen = multi_agent_stream() if body.multi_agent else single_stream()
    return StreamingResponse(gen, media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
