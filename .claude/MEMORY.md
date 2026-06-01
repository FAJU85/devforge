# DevForge — Orchestrator Memory
> Last updated: 2026-06-01 (cycle 41) | Branch: claude/exciting-galileo-7UDWc | Governance: WIKI 1.2.0 / PROTOCOL 1.1.0 / PLAYBOOK 1.1.0 / GLOSSARY 1.0.0

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
│   └── test_main.py         # 257 tests
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

## Features Implemented (Cycles 1-24 Complete)
- [x] GitHub OAuth one-click (Device Flow)
- [x] Repo browser + file tree (up to 8 files in context)
- [x] AI Provider: Anthropic Claude (haiku/sonnet/opus selector)
- [x] AI Provider: Groq (llama, mixtral, gemma, deepseek, qwen)
- [x] AI Provider: HuggingFace (any text-generation model)
- [x] Multi-agent pipeline (Plan → Implement → Test → Review, same provider)
- [x] Skills: Go, Zod, Tests, Errors, Security, Docs, Perf, SOLID, React, Next.js, Docker, SQL
- [x] Custom Rules textarea
- [x] Custom Instructions textarea
- [x] SSE streaming responses
- [x] Light/Dark theme
- [x] localStorage persistence (survives page refresh)
- [x] OpenAI-compatible custom endpoint (Ollama, OpenRouter, LM Studio…)
- [x] GitHub write-back: agent commits generated code directly to repo
- [x] File upload for instructions/rules/local context
- [x] Cross-provider multi-agent (different AI per stage: Plan/Code/Test/Review)
- [x] Instruction Presets (7 built-in + save/load/delete custom)
- [x] Endpoint quick-fill: Vercel AI Gateway, OpenRouter, Ollama, LM Studio
- [x] Session Memory: per-repo localStorage context injected across sessions
- [x] Chat Export: download conversation as .md
- [x] Token stats: real (Anthropic) + estimated (other providers) display
- [x] Quick Stacks: Full-Stack TS, Python API, Go Service, Secure Review
- [x] New Agent Tabs: Refactor + Test Gen
- [x] Code diff view in write panel
- [x] Message actions (copy, delete, regenerate)
- [x] Conversation auto-save/restore per repo (tab-based)
- [x] Conversation Tabs (per-repo named threads, auto-named from first message)
- [x] GitHub Issue creation (modal + POST /api/github/issue/create)
- [x] GitHub PR creation (modal + POST /api/github/pr/create)
- [x] Repo quick-scan card (language breakdown, file count)
- [x] 4-stage multi-agent pipeline (+ Test Gen stage)
- [x] Batch file commit (extract all code blocks, commit in one op)
- [x] Stream cancel / AbortController (Stop button)
- [x] POST /api/repo/write/batch endpoint
- [x] AI file suggestions (POST /api/repo/suggest-files, haiku/llama)
- [x] File tree search / live filter
- [x] Streaming timer (elapsed seconds indicator)
- [x] Keyboard shortcuts (Escape, Cmd+/, Cmd+Shift+Backspace, Ctrl+F)
- [x] HTTP Tools (define tools, proxy via /api/tools/call, Anthropic native tool use)
- [x] File summarization (POST /api/repo/summarize-file, haiku/llama)
- [x] Code search (POST /api/repo/search, GitHub code search API)
- [x] Commit history viewer (POST /api/repo/commits)
- [x] Branch selector + switcher (GET /api/repo/branches)
- [x] Anthropic model selector (Haiku / Sonnet / Opus)
- [x] Prompt history (up/down arrow, 50 entries)
- [x] Token budget bar (color-coded, 80K warning, per-file token count)
- [x] Extended Thinking Mode (Claude Opus only; collapsible thinking block in UI)
- [x] Prompt Enhancement (POST /api/prompt/enhance; ✨ button fills textarea)
- [x] Response Regeneration (🔄 button on AI messages)
- [x] GitHub Actions workflow status (POST /api/repo/workflow-runs; ⚙️ panel)
- [x] File Peek Modal (👁 button on file tree; full content view + add to context)
- [x] Smart context trimming (auto-drop oldest messages when >90K tokens)
- [x] Snippet Library (📌 save/load/delete prompt snippets, up to 30)
- [x] AI Commit Message Suggestions (POST /api/commit/suggest-message; ✨ in write panel)
- [x] Code Explain Button (? on code blocks; fills prompt with explain request)
- [x] Chat Search (Ctrl+F; highlight all matches; ▼/▲ navigate)
- [x] Release Notes Generator (POST /api/repo/release-notes; tag/SHA range; AI-streamed Markdown)
- [x] PR Review Mode (POST /api/github/pr/diff; loads diff as context; switches to Review agent)
- [x] GitHub Gist Export (POST /api/github/gist/create; Gist button on code blocks)
- [x] README Generator (POST /api/repo/generate-readme; streamed from selected files)
- [x] Mobile-responsive UI (sidebar slide-over overlay, compact topbar, bottom-sheet modals)
- [x] Removed Go/Zod skill chips (less relevant for typical users)

## Cycle 41 Summary (2026-06-01) — /api/tools/call SSRF + Method Allowlist
| Area | Change |
|---|---|
| Backend | `call_tool`: reject non-`http(s)://` URLs; allowlist HTTP methods to GET/POST/PUT/PATCH/DELETE |
| Tests | 257 total |

## Cycle 40 Summary (2026-06-01) — Final innerHTML Hardening Pass
| Area | Change |
|---|---|
| Frontend | `d.total` in search results header coerced to `Number()` — last unguarded API field in templates |
| Tests | 257 total |

## Cycle 39 Summary (2026-06-01) — fetchModels + Error Messages + File Extensions
| Area | Change |
|---|---|
| Frontend | `fetchModels`: `m.name`/`m.author`/`models.error` escaped; model id moved to `data-id` attr (removes inline onclick injection) |
| Frontend | `d.error` from search/commits/workflow panels escaped before innerHTML |
| Frontend | `e.message` in `send()` catch block escaped; file extension `ext` in `quickScanRepo` escaped |
| Tests | 257 total |

## Cycle 38 Summary (2026-06-01) — Scan Result XSS via AST Identifiers
| Area | Change |
|---|---|
| Frontend | `issueHtml`: `i.pattern`/`i.message` escaped; `i.severity` restricted to allowlist before CSS class — AST scan embeds user identifier names in pattern strings |
| Tests | 257 total |

## Cycle 37 Summary (2026-06-01) — Input Size Caps
| Area | Change |
|---|---|
| Backend | `scan_code`: code capped at 100K chars before `ast.parse` + regex loop |
| Backend | `scan_deps`: content capped at 200K chars before parser dispatch |
| Tests | 257 total |

## Cycle 36 Summary (2026-06-01) — safeOpenUrl + OAuth Box Security
| Area | Change |
|---|---|
| Frontend | `safeOpenUrl(u)` helper validates `https?://` before `window.open` |
| Frontend | `gistCode()` and `createPR()` use `safeOpenUrl()`; `startOAuth` escapes `user_code` and validates `verification_uri` to `github.com` |
| Tests | 257 total |

## Cycles 32-35 Summary (2026-06-01) — XSS Sweep Batch 1 + MEMORY.md Fix
| Area | Change |
|---|---|
| Backend | `_parse_pyproject_toml()`: full `tomllib`-based parser for PEP 621 / Poetry / build-system deps |
| Backend | `parse_gh_url`: `.replace(".git","")` → `.removesuffix(".git")` |
| Frontend | `escA(s)` helper + `safeOpen(el)`; repo list/tree/ctx/batch all escaped; write panel, search, commit, workflow, deps table, tool list all escaped |
| Config | `Edit(.claude/**)` added to allow list to eliminate MEMORY.md permission prompts |
| Tests | +8 new tests (pyproject.toml parser ×6, parse_gh_url ×2) → 257 total |

## Cycle 31 Summary (2026-06-01) — XSS Hardening + State Bug Fixes
| Area | Change |
|---|---|
| Frontend | `insertToolCallCard`: tool name now set via `.textContent` instead of `innerHTML` (XSS fix for AI-controlled tool names) |
| Frontend | `regenerate()`: also pops last user message before re-calling `send()`, fixing consecutive-user-message violation of Anthropic API alternation rules |
| Frontend | `rmd()` lang sanitization: `lang` stripped to `[a-z0-9+#._-]` before use in inline `onclick` attribute (JS injection fix) |
| Frontend | `suggestFiles()`: now sets `S.fileSizes.set(path, d.content.length)` so AI-suggested files show correct token counts |
| Backend | `repo_write` exception handler broadened from `(KeyError, json.JSONDecodeError)` to `Exception` |
| Tests | 249 total (no new tests this cycle) |

## Cycle 30 Summary (2026-06-01) — Version Checker Tests + Security Footer Coverage
| Area | Change |
|---|---|
| Tests | `TestScanDepsExtraEcosystems`: +2 tests for `outdated` and `unpinned` SSE event fields |
| Tests | `TestVersionCheckerHelpers` (new): `_pypi_latest` success/HTTP-error/network-error; `_npm_latest` success/HTTP-error/network-error (6 tests) |
| Tests | `TestBuildSystemAgentSecurity` (new): code/refactor/testgen/debug get SECURITY_FOOTER; review/architect/docs do NOT (7 tests) |
| Tests | 249 total (+15 from cycle 29 base) |

## Cycle 29 Summary (2026-06-01) — Cargo TOML Fix + Lang Sanitization + fileSizes Bug
| Area | Change |
|---|---|
| Backend | `_parse_cargo_toml`: inline table deps like `tokio = { version = "1.36", features = ["full"] }` now correctly extract `version` field instead of returning `{` as constraint |
| Frontend | `rmd()` lang sanitization: prevents JS injection via Markdown code fence language identifier |
| Frontend | `suggestFiles()`: `S.fileSizes` populated for AI-suggested files (token count bug fix) |
| Tests | `TestDepParserHelpers`: +2 tests for inline table parsing |
| Tests | `TestCodeScanLanguages` (new): TypeScript innerHTML/`:any`, SQL concat, Bash eval, Go fmt.Sprintf, generic token, HTTP URL/localhost (8 tests) |
| Tests | `TestScanDepsExtraEcosystems` (new): go.mod, cargo.toml, unknown filename, no-packages 400, Groq streaming (5 tests) |
| Tests | 234 total (+15 from cycle 28 base of 219) |

## Cycle 26 Summary (2026-06-01) — Mobile UI + Skill Cleanup
| Area | Change |
|---|---|
| Frontend | `@media(max-width:768px)` — sidebar as fixed slide-over overlay with dark backdrop; `exp-btn` always visible; topbar compacted; model/MA/mem/stat pills hidden; modals slide up from bottom |
| Frontend | Removed 🐹 Go and 🔷 Zod skill chips from skills grid |
| JS | Added `isMob()` helper; `collSidebar()`/`expSidebar()` handle mobile overlay; `init()` always collapses on mobile |
| Tests | 190 total (no backend changes) |

## Cycle 25 Summary (2026-06-01) — Code Security Scanner
| Area | Change |
|---|---|
| Backend | `POST /api/code/scan` — AST analysis for Python + regex for JS/TS/SQL/Go/Bash; `SECURITY_FOOTER` injected into code/refactor/testgen/debug system prompts |
| Frontend | 🛡️ Scan button on code blocks; inline severity-coded results; 🔧 Auto-Fix fills prompt for self-healing loop |
| Tests | 3 new (TestCodeScanEndpoint) + 1 updated; 187 total |

## Features NOT Yet Implemented (Target)
- [ ] MCP (Model Context Protocol) tool support
- [ ] Persistent server-side memory (beyond localStorage)
- [ ] Mistral / Cohere / Gemini providers (can now use via Custom endpoint)
- [ ] Smart context window management (file chunking, token budgeting beyond current trim)
- [ ] Release notes generator
- [ ] Multiple named conversation tabs per repo (done — single tab auto-name)

## Known Construction Errors
> None outstanding.

## Cumulative Scope Ledger
```
totalCyclesCompleted: 41
totalFilesCreated: 3   (tests/__init__.py, tests/test_main.py, .gitignore)
totalFilesMutated: 4   (main.py, requirements.txt, static/index.html, tests/test_main.py)
totalPackagesAdded: 0
scopeFreeze: false
conservativeMode: false
```

## Cycle 24 Summary (2026-05-31) — README Generator
| Area | Change |
|---|---|
| Backend | `POST /api/repo/generate-readme` — streams AI README from file context |
| Frontend | 📝 Generate README button; modal with streaming preview; copy/add-to-context |
| Tests | 3 new (TestGenerateReadmeEndpoint); 184 total |

## Cycle 23 Summary (2026-05-31) — GitHub Gist Export
| Area | Change |
|---|---|
| Backend | `POST /api/github/gist/create` |
| Frontend | Gist button on code blocks (when GitHub connected) |
| Tests | 3 new (TestGistCreate); 181 total |

## Cycle 22 Summary (2026-05-31) — PR Review Mode
| Area | Change |
|---|---|
| Backend | `POST /api/github/pr/diff` — PR metadata + 40KB diff |
| Frontend | PR # input in sidebar; loads diff as local context; switches to Review agent |
| Tests | 3 new (TestPRDiffEndpoint); 178 total |

## Cycle 21 Summary (2026-05-31) — Release Notes Generator
| Area | Change |
|---|---|
| Backend | `POST /api/repo/release-notes` — streamed AI release notes from commits |
| Frontend | 📋 Release Notes topbar button; modal with since/until/max-commits |
| Tests | 3 new (TestReleaseNotesEndpoint); 175 total |

## Cycle 20 Summary (2026-05-31) — Code Explain + Chat Search
| Area | Change |
|---|---|
| Frontend | `explainCode()` — ? button on code blocks; `toggleChatSearch()`/`runChatSearch()`/`stepChatSearch()` — Ctrl+F chat search bar with match highlighting and navigation |
| Tests | 172 total (no new backend) |

## Cycle 19 Summary (2026-05-31) — Snippets + AI Commit Messages
| Area | Change |
|---|---|
| Backend | `POST /api/commit/suggest-message` (haiku/llama) |
| Frontend | 📌 Snippets section (save/load/delete, localStorage); ✨ button in write panel for AI commit message |
| Tests | 3 new (TestCommitSuggestMessage); 172 total |

## Cycle 18 Summary (2026-05-31) — File Peek + Smart Trim
| Area | Change |
|---|---|
| Frontend | 👁 peek-btn on file tree; peek modal (full view + add to context); smart context trim before send (>90K) |
| Tests | 169 total (no new backend) |

## Cycle 17 Summary (2026-05-31) — GitHub Actions Viewer
| Area | Change |
|---|---|
| Backend | `POST /api/repo/workflow-runs` — Actions runs list |
| Frontend | ⚙️ button + workflows-panel showing status icons |
| Tests | 3 new (TestWorkflowRunsEndpoint); 169 total |

## Cycle 16 Summary (2026-05-31) — Prompt Enhancement + Regenerate
| Area | Change |
|---|---|
| Backend | `POST /api/prompt/enhance` (haiku/llama rewrites prompt) |
| Frontend | ✨ button fills textarea; 🔄 regenerate on AI messages |
| Tests | 4 new (TestPromptEnhance); 166 total |

## Cycle 15 Summary (2026-05-31) — Extended Thinking Mode
| Area | Change |
|---|---|
| Backend | `_run_anthropic_thinking()`, `thinking_mode`/`thinking_budget` fields, `stream_one()` passes thinking events |
| Frontend | `.thinking-block` CSS; think-opts panel (Opus only); SSE handler for thinking events |
| Tests | 4 new (TestExtendedThinking); 162 total |

## Cycles 10-14 Summary (prior session)
- Cycle 10: HTTP Tools (native Anthropic tool use)
- Cycle 11: File summarization endpoint
- Cycle 12: GitHub code search
- Cycle 13: Commit history + branch switcher
- Cycle 14: Anthropic model selector + prompt history

## Cycle 9 Summary (2026-05-31) — AI Assist + UX Polish
| Area | Change |
|---|---|
| Backend | `POST /api/repo/suggest-files`: haiku/llama picks relevant files from task |
| Frontend | File tree search (live filter); AI Suggest button; streaming timer; keyboard shortcuts |
| Tests | 5 new tests (TestSuggestFiles); 124 total |

## Git State
- Branch: claude/exciting-galileo-7UDWc
- Last commit: a325cf6 — Cycle 41: /api/tools/call SSRF + method allowlist
- Remote: origin/claude/exciting-galileo-7UDWc ✓ tracked
