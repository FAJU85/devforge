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
├── requirements.txt         # Dependencies (range-pinned — see errors)
├── Dockerfile               # python:3.11-slim, EXPOSE 7860
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

## Features Implemented (v1 — Initial Commit)
- [x] GitHub OAuth one-click (Device Flow)
- [x] Repo browser + file tree (up to 8 files in context)
- [x] AI Provider: Anthropic Claude (claude-sonnet-4-20250514)
- [x] AI Provider: Groq (llama, mixtral, gemma, deepseek, qwen)
- [x] AI Provider: HuggingFace (any text-generation model)
- [x] Multi-agent pipeline (Plan → Implement → Review, same provider)
- [x] Skills: Go, Zod, Tests, Errors, Security, Docs, Perf, SOLID
- [x] Custom Rules textarea
- [x] Custom Instructions textarea
- [x] SSE streaming responses
- [x] Light/Dark theme
- [x] Session state persisted in sessionStorage

## Features NOT Yet Implemented (Target)
- [ ] MCP (Model Context Protocol) tool support
- [ ] File upload for instructions/context
- [ ] Cross-provider multi-agent (different AI for each stage)
- [ ] Persistent memory (beyond sessionStorage)
- [ ] Fine-tune instruction presets
- [ ] OpenAI-compatible endpoint (custom API base)
- [ ] Mistral / Cohere / Gemini providers
- [ ] Agent output to edit/commit directly to GitHub
- [ ] localStorage persistence (survives refresh)

## Known Construction Errors (Audit 2026-05-31)

### CRITICAL — PROTOCOL §3.3 Violation
| File | Line | Error | Fix Required |
|---|---|---|---|
| main.py | 98 | `except: pass` — bare swallowed exception | Replace with typed handler + structured error payload |

### HIGH — PROTOCOL §3.5 Violation (Dependency Pinning)
| File | Issue |
|---|---|
| requirements.txt | All 6 packages use `>=` range specifiers — exact pins + SHA-256 required |

### MEDIUM — PROTOCOL §3.4 Violation (No Tests)
| Issue |
|---|
| Zero test files exist. Coverage gate: ≥85% line, ≥75% branch |

### MEDIUM — Model ID Discrepancy
| File | Line | Current | Should Be |
|---|---|---|---|
| main.py | 67 | `claude-sonnet-4-20250514` | `claude-sonnet-4-6` (current configured model) |

### LOW — Missing Type Annotations
| File | Functions Missing Return Types |
|---|---|
| main.py | `build_system`, `get_runner`, `parse_gh_url`, `gh_hdrs` |

### LOW — Missing Docstrings
| All Python functions lack `Args:` / `Returns:` blocks (CANVAS §4 requirement) |

## Cumulative Scope Ledger
```
totalCyclesCompleted: 0
totalFilesCreated: 0
totalFilesMutated: 0
totalPackagesAdded: 0
scopeFreeze: false
conservativeMode: false
```

## Active Canvas
> Canvas ID: CANVAS-DF-2026-001 — awaiting CANVAS_APPROVED

## Git State
- Branch: claude/exciting-galileo-7UDWc
- Last commit: ee72cf3 — Initial commit
- Remote: origin/claude/exciting-galileo-7UDWc ✓ tracked
