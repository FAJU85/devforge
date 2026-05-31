# DevForge — Orchestrator Memory
> Last updated: 2026-05-31 | Branch: claude/exciting-galileo-7UDWc | Governance: WIKI 1.2.0 / PROTOCOL 1.1.0 / PLAYBOOK 1.1.0 / GLOSSARY 1.0.0

## Project Identity
- **Name:** DevForge
- **Type:** AI coding agent web interface (similar to Codex, Open Hands)
- **Deployed:** HuggingFace Spaces (Docker, port 7860)
- **Repo:** github.com/FAJU85/devforge
- **HF Space:** huggingface.co/spaces/vooom/devforge
- **Sync:** GitHub Actions bidirectional (sync-to-hf.yml, sync-from-hf.yml)

## Architecture (Current)
```
devforge/
├── main.py                  # FastAPI backend (Python 3.11)
├── static/index.html        # Single-file frontend (HTML + CSS + JS)
├── requirements.txt         # Full pip-compile lock file (exact pins + SHA-256)
├── Dockerfile               # python:3.11-slim, EXPOSE 7860
├── tests/
│   ├── __init__.py
│   └── test_main.py         # 172 tests
└── .github/workflows/
    ├── sync-to-hf.yml
    └── sync-from-hf.yml
```

## Stack
- **Backend:** Python 3.11 / FastAPI / Uvicorn
- **Frontend:** Single HTML file (Vanilla JS, marked.js, highlight.js)
- **AI Providers:** Anthropic Claude, Groq, HuggingFace Inference API, OpenAI-compat
- **Auth:** GitHub OAuth Device Flow (GITHUB_CLIENT_ID + GITHUB_CLIENT_SECRET env vars)
- **HF Token:** HF_TOKEN env var (optional)

## Features Implemented (Cycles 1-20 Complete)
- [x] GitHub OAuth one-click (Device Flow)
- [x] Repo browser + file tree (up to 8 files in context)
- [x] AI Provider: Anthropic Claude (haiku/sonnet/opus selector)
- [x] AI Provider: Groq (llama, mixtral, gemma, deepseek, qwen)
- [x] AI Provider: HuggingFace (any text-generation model)
- [x] Multi-agent pipeline (Plan → Implement → Test → Review, same or cross-provider)
- [x] Skills: Go, Zod, Tests, Errors, Security, Docs, Perf, SOLID, React, Next.js, Docker, SQL
- [x] Custom Rules + Custom Instructions textareas
- [x] SSE streaming responses + AbortController stop
- [x] Light/Dark theme
- [x] localStorage persistence
- [x] OpenAI-compatible custom endpoint (Ollama, OpenRouter, LM Studio)
- [x] GitHub write-back: agent commits generated code directly to repo
- [x] File upload for context
- [x] Cross-provider multi-agent
- [x] Instruction Presets (7 built-in + custom)
- [x] Endpoint quick-fill presets
- [x] Session Memory (per-repo localStorage context)
- [x] Chat Export (.md)
- [x] Token stats display
- [x] Quick Stacks (Full-Stack TS, Python API, Go Service, Secure Review)
- [x] Agent Tabs: Code/Review/Arch/Debug/Docs/Refactor/Tests
- [x] Code diff view in write panel
- [x] Message copy/delete/regenerate actions
- [x] Conversation auto-save/restore per repo
- [x] GitHub Issue creation modal
- [x] GitHub PR creation modal
- [x] Repo quick-scan card
- [x] 4-stage multi-agent pipeline (Plan→Code→Test→Review)
- [x] Batch file commit
- [x] POST /api/repo/write/batch
- [x] AI file suggestions (POST /api/repo/suggest-files)
- [x] File tree search / live filter
- [x] Streaming timer
- [x] Keyboard shortcuts (Escape, Cmd+/, Cmd+Shift+Backspace, Ctrl+F)
- [x] HTTP Tools (define/call custom endpoints, Anthropic tool use)
- [x] Anthropic model selector (Haiku/Sonnet/Opus)
- [x] Branch management + switch branch
- [x] Code search in repo (POST /api/repo/search)
- [x] Commit history panel
- [x] File summarization (POST /api/repo/summarize-file)
- [x] Conversation tabs (per-repo named threads)
- [x] Prompt history (up/down arrow, last 50)
- [x] Token budget bar (color-coded, 80K warning)
- [x] Extended Thinking Mode (Opus only) ← Cycle 15
- [x] Prompt Enhancement ✨ (POST /api/prompt/enhance) ← Cycle 16
- [x] Response Regeneration 🔄 ← Cycle 16
- [x] GitHub Actions Workflow Status (POST /api/repo/workflow-runs) ← Cycle 17
- [x] File Peek Modal (👁 hover button) ← Cycle 18
- [x] Smart Context Trimming (auto-drop oldest msgs >90K) ← Cycle 18
- [x] Snippet Library 📌 (save/load/delete prompts) ← Cycle 19
- [x] AI Commit Messages ✨ (POST /api/commit/suggest-message) ← Cycle 19
- [x] Code Explain Button ? (fills prompt with explain request) ← Cycle 20
- [x] Chat Search Ctrl+F (highlight matches, navigate ▼▲) ← Cycle 20

## Features NOT Yet Implemented (Target)
- [ ] MCP (Model Context Protocol) tool support
- [ ] Persistent server-side memory (beyond localStorage)
- [ ] Smart context window management — server-side chunking

## Cumulative Scope Ledger
```
totalCyclesCompleted: 20
totalFilesMutated: 4   (main.py, requirements.txt, static/index.html, tests/test_main.py)
totalPackagesAdded: 0
```

## Git State
- Branch: claude/exciting-galileo-7UDWc
- Last commit: ab47b49 — Cycle 20: Code Explain Button + Chat Search
- Remote: origin/claude/exciting-galileo-7UDWc ✓ tracked
