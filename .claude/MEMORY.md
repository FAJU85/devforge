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
│   └── test_main.py         # 69 tests, 92% line/branch coverage
└── .github/workflows/
    ├── sync-to-hf.yml
    └── sync-from-hf.yml
```

## Stack
- **Backend:** Python 3.11 / FastAPI / Uvicorn
- **Frontend:** Single HTML file (Vanilla JS, marked.js, highlight.js)
- **AI Providers:** Anthropic Claude, Groq, HuggingFace Inference API
- **Auth:** GitHub OAuth Device Flow (GITHUB_CLIENT_ID + GITHUB_CLIENT_SECRET env vars)
- **HF Token:** HF_TOKEN env var (optional)

## Features Implemented (v1 — Cycles 1-5 Complete)
- [x] GitHub OAuth one-click (Device Flow)
- [x] Repo browser + file tree (up to 8 files in context)
- [x] AI Provider: Anthropic Claude (current model)
- [x] AI Provider: Groq (llama, mixtral, gemma, deepseek, qwen)
- [x] AI Provider: HuggingFace (any text-generation model)
- [x] Multi-agent pipeline (Plan → Implement → Review, same provider)
- [x] Skills: Go, Zod, Tests, Errors, Security, Docs, Perf, SOLID ← Cycles 1-3
- [x] Custom Rules textarea
- [x] Custom Instructions textarea
- [x] SSE streaming responses
- [x] Light/Dark theme
- [x] localStorage persistence (survives page refresh) ← fixed Cycle 1
- [x] OpenAI-compatible custom endpoint (Ollama, OpenRouter, LM Studio…) ← added Cycle 2
- [x] GitHub write-back: agent commits generated code directly to repo ← added Cycle 3
- [x] File upload for instructions/rules/local context ← added Cycle 4
- [x] Cross-provider multi-agent (different AI per stage: Plan/Code/Review) ← added Cycle 4
- [x] Instruction Presets (7 built-in + save/load/delete custom) ← added Cycle 5
- [x] Endpoint quick-fill: Vercel AI Gateway, OpenRouter, Ollama, LM Studio ← added Cycle 5
- [x] Session Memory: per-repo localStorage context injected across sessions ← added Cycle 5
- [x] Chat Export: download conversation as .md ← added Cycle 5
- [x] Token stats: real (Anthropic) + estimated (other providers) display ← added Cycle 5
- [x] Expanded Skills: React, Next.js, Docker, SQL ← added Cycle 5
- [x] Quick Stacks: Full-Stack TS, Python API, Go Service, Secure Review ← added Cycle 5
- [x] New Agent Tabs: Refactor + Test Gen ← added Cycle 5

## Features NOT Yet Implemented (Target)
- [ ] MCP (Model Context Protocol) tool support
- [ ] Persistent server-side memory (beyond localStorage)
- [ ] Mistral / Cohere / Gemini providers (can now use via Custom endpoint)

## Known Construction Errors
> All Cycle 1 violations resolved. No outstanding PROTOCOL violations.

## Cumulative Scope Ledger
```
totalCyclesCompleted: 5
totalFilesCreated: 3   (tests/__init__.py, tests/test_main.py, .gitignore)
totalFilesMutated: 4   (main.py, requirements.txt, static/index.html, tests/test_main.py)
totalPackagesAdded: 0
scopeFreeze: false
conservativeMode: false
```

## Cycle 5 Summary (2026-05-31) — Vercel Ecosystem Upgrades
| Area | Change |
|---|---|
| Backend | `refactor` + `testgen` agent prompts; `react`/`nextjs`/`docker`/`sql` skills; `memory` field in `ChatBody`; `build_system` injects memory; `_run_anthropic` emits `("usage",{input,output})`; `stream_one` passes through usage |
| Frontend | Endpoint quick-fills (Vercel AI Gateway, OpenRouter, Ollama, LM Studio); 7 built-in instruction presets + save/load/delete custom; 4 Quick Stacks; session memory (per-repo localStorage, injected as context); chat export (.md); token stats pill; 🔀 Refactor + 🧪 Tests agent tabs; 4 new skill chips |
| Tests | 18 new tests; 105 total |

## Cycle 3 Summary (2026-05-31)
| Area | Change |
|---|---|
| Backend | `WriteFileBody` + `POST /api/repo/write` (create/update via GitHub Contents API) |
| Frontend | `rmd()` detects `### \`path\`` headings → injects `📤 Write` button; `showWritePanel()` + `commitFile()` |
| Tests | 4 new cases; 82 total |

## Cycle 2 Summary (2026-05-31) — SESSION_APPROVED
| Area | Change |
|---|---|
| Backend | `_run_openai_compat()` + `ChatBody` fields + `get_runner` routing |
| Frontend | Custom provider button, custom endpoint panel, provider/badge/enhance/send updated |
| Tests | New tests covering custom endpoint paths |

## Cycle 1 Summary (2026-05-31) — SESSION_APPROVED
| Priority | Fix | Result |
|---|---|---|
| CRITICAL | Bare `except: pass` → typed `json.JSONDecodeError` / `(KeyError, IndexError)` | ✓ |
| HIGH | requirements.txt → full pip-compile lock with SHA-256 hashes | ✓ |
| MEDIUM | Model ID updated to current model | ✓ |
| MEDIUM | Test suite shipped (69 tests, 92% coverage) | ✓ |
| LOW | Type annotations + docstrings: `build_system`, `get_runner`, `parse_gh_url`, `gh_hdrs` | ✓ |
| LOW | `sessionStorage` → `localStorage` (5 occurrences) | ✓ |

## Active Canvas
> Canvas ID: CANVAS-DF-2026-003 — in progress (2026-05-31)

## Git State
- Branch: claude/exciting-galileo-7UDWc
- Last commit: 21ae09d — Add cross-provider multi-agent and file upload for instructions/context
- Remote: origin/claude/exciting-galileo-7UDWc ✓ tracked
