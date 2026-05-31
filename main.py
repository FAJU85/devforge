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
}

MA_PLAN_SYSTEM   = "You are a software architect. Analyze the task and create a clear, concise step-by-step implementation plan. List files to create/modify, key functions, and potential pitfalls. Do NOT write actual code yet."
MA_CODE_SYSTEM   = "You are an expert coding agent. Implement the task following the provided plan. Write complete, production-ready code with full file paths before every code block."
MA_REVIEW_SYSTEM = "You are a senior code reviewer. Review the implementation for bugs, security issues, performance problems, missing error handling, and code quality. Be specific and constructive."

def build_system(body: "ChatBody") -> str:
    """Compose the system prompt from agent, skills, rules, and file context.

    Args:
        body: Validated chat request containing agent mode, skills, rules, and context.

    Returns:
        Assembled system prompt string ready to pass to any provider.
    """
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
    fc = (getattr(body, 'file_context', '') or '').strip()
    if fc:
        base += f"\n\n---\n**Repository context:**\n{fc}"
    return base

def _run_anthropic(q, loop, system, messages, api_key):
    try:
        client = Anthropic(api_key=api_key)
        with client.messages.stream(model="claude-sonnet-4-6", max_tokens=4096,
                system=system, messages=messages) as stream:
            for text in stream.text_stream:
                asyncio.run_coroutine_threadsafe(q.put(("text", text)), loop)
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
            if kind == "text": yield kind, val
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
    token: str; url: str

@app.post("/api/repo/connect")
async def repo_connect(body: RepoBody):
    owner, repo = parse_gh_url(body.url)
    if not owner: return JSONResponse({"error": "Invalid repository"}, status_code=400)
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=gh_hdrs(body.token), timeout=10)
    if not r.ok: return JSONResponse({"error": r.json().get("message", "Not found")}, status_code=400)
    branch = r.json()["default_branch"]
    t = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=gh_hdrs(body.token), timeout=15)
    if not t.ok: return JSONResponse({"error": "Failed to fetch file tree"}, status_code=400)
    files = sorted([{"path": f["path"], "size": f.get("size", 0)} for f in t.json().get("tree", [])
        if f["type"] == "blob" and f.get("size", 999999) < 150000], key=lambda x: x["path"])
    return {"owner": owner, "repo": repo, "branch": branch, "files": files}

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

def get_runner(body: ChatBody) -> Callable:
    """Return a thread-target callable bound to the chosen provider's run function.

    Args:
        body: Validated chat request with provider selection and credentials.

    Returns:
        Callable accepting (queue, event_loop, system_prompt, messages).
    """
    if body.provider == "anthropic":
        return lambda q, loop, sys, msgs: _run_anthropic(q, loop, sys, msgs, body.anthropic_key)
    elif body.provider == "groq":
        return lambda q, loop, sys, msgs: _run_groq(q, loop, sys, msgs, body.groq_key, body.groq_model or "llama-3.3-70b-versatile")
    elif body.provider == "openai_compat":
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

        yield f"data: {json.dumps({'t': 'step', 'v': 'plan', 'label': '🗺️ Planning'})}\n\n"
        plan_text = ""
        plan_msgs = [{"role": "user", "content": f"Task: {user_task}\n\nCreate a clear step-by-step implementation plan. List files, key functions, and pitfalls. No code yet."}]
        async for kind, val in stream_one(runner, MA_PLAN_SYSTEM, plan_msgs):
            if kind == "text":
                plan_text += val
                yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                return

        yield f"data: {json.dumps({'t': 'step', 'v': 'code', 'label': '⚙️ Implementing'})}\n\n"
        code_text = ""
        code_system = build_system(body)
        code_msgs = prior + [{"role": "user", "content": f"{user_task}\n\n## Plan:\n{plan_text}"}]
        async for kind, val in stream_one(runner, code_system, code_msgs):
            if kind == "text":
                code_text += val
                yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                return

        yield f"data: {json.dumps({'t': 'step', 'v': 'review', 'label': '🔍 Reviewing'})}\n\n"
        review_msgs = [{"role": "user", "content": f"Review this implementation for bugs, security issues, missing error handling, and quality:\n\n{code_text}"}]
        async for kind, val in stream_one(runner, MA_REVIEW_SYSTEM, review_msgs):
            if kind == "text":
                yield f"data: {json.dumps({'t': 'text', 'v': val})}\n\n"
            elif kind == "error":
                yield f"data: {json.dumps({'t': 'error', 'v': val})}\n\n"
                return

        yield f"data: {json.dumps({'t': 'done'})}\n\n"

    gen = multi_agent_stream() if body.multi_agent else single_stream()
    return StreamingResponse(gen, media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
