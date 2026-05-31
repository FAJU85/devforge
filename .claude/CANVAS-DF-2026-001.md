# CANVAS-DF-2026-001 — DevForge Phase 2
> Canvas Schema Version: 1.0.0 | Status: AWAITING_APPROVAL | Date: 2026-05-31

---

## 1. REALITY BOUNDARY

* **One-Sentence Problem/Pain:**
  Developers need a single browser-based AI coding workspace that connects their GitHub repos, runs multiple AI providers (including any HuggingFace model or custom API), supports MCP tools, uploadable instructions, and persistent memory — without juggling separate tools.

* **Primary Workflow (Success Path):**
  User opens DevForge → connects GitHub (one click) → selects a repo + files → chooses AI provider (Claude / Groq / HF / custom API key) → optionally enables multi-agent pipeline and skills → types a task → receives streaming AI response with code, review, and plan.

* **Strict Exclusions (WILL NOT DO):**
  1. No native code execution / sandboxed runtime (no running user code server-side)
  2. No persistent database — all state stays in browser localStorage / sessionStorage
  3. No user authentication system (no accounts, no server-side sessions)
  4. No paid hosting features (no billing, no usage metering)
  5. No multi-user / collaboration features

---

## 2. THE ABSOLUTE MINIMUM ENGINE

* **Single Stack Components:**
  * Database: None — browser localStorage for persistence
  * Backend Language/Framework: Python 3.11 / FastAPI
  * Frontend Framework: Vanilla JS (single index.html — no build step)

* **Boring Technologies Used:**
  * fastapi — mature, stable
  * uvicorn — standard ASGI server
  * anthropic SDK — official, stable
  * huggingface_hub — official, stable
  * requests — stdlib-adjacent, universally trusted
  * marked.js CDN — markdown rendering
  * highlight.js CDN — syntax highlighting

* **Static/Hardcoded Elements:**
  * AGENT_PROMPTS dict — hardcoded in main.py (no DB)
  * SKILL_PROMPTS dict — hardcoded in main.py (no DB)
  * Provider list — hardcoded in HTML (Claude, Groq, HF)

* **Dependency Compliance:**
  CURRENT VIOLATION: requirements.txt uses `>=` range specifiers.
  Must be resolved before next cycle: exact pins + SHA-256 hashes required.

---

## 3. VALUE MATRIX

* **Core User Outcome:**
  User can connect a GitHub repo, paste their API key, and get a streaming AI code response with file context in under 60 seconds.

* **Time-to-Value Bottleneck:**
  GitHub OAuth setup complexity + needing to enter API key every session (sessionStorage cleared on tab close) — localStorage persistence for keys/settings is the primary fix.

* **Manual Testing Protocol:**
  1. Open app → sidebar visible → "Connect GitHub" button present → PASS if rendered correctly
  2. Enter Anthropic key → type message → click Send → PASS if streaming response appears
  3. Connect GitHub → select repo → select 1 file → send message referencing file → PASS if AI references file content
  4. Enable Multi-Agent toggle → send message → PASS if three stages (Plan/Implement/Review) render
  5. Select Groq provider + key → send message → PASS if Groq response streams correctly
  6. Refresh page → PASS if API keys and settings are still populated (requires localStorage fix)

---

## 4. AI CO-PILOT GUARDRAILS

* Max 50 logical lines per file change
* One file mutation per prompt response
* No placeholder comments or TODO markers
* All Python: explicit type annotations + docstrings with Args/Returns
* Verification loop before any commit:
  1. flake8 + bandit + vulture + detect-secrets on mutated file
  2. pytest --cov ≥85% line, ≥75% branch

---

## 5. ANTI-COMPLEXITY WATCHLIST

* Tooling Parking Lot (do not implement this cycle):
  ```
  - Full MCP protocol implementation — 2026-05-31
  - Cross-provider multi-agent (different AI per stage) — 2026-05-31
  - File upload for context/instructions — 2026-05-31
  - OpenAI-compatible custom base URL provider — 2026-05-31
  - Direct GitHub commit from AI output — 2026-05-31
  - Fine-tune preset library — 2026-05-31
  ```

---

## 6. ENGINEERING HYGIENE

* **Dependency Budget:** 6 / 8 packages
  Justification: FastAPI stack (fastapi+uvicorn+pydantic), AI clients (anthropic+huggingface_hub), HTTP (requests). Budget of 8 leaves 2 slots for future providers without amendment.

* **Branch:** claude/exciting-galileo-7UDWc

---

## 7. PSYCHOLOGICAL ANCHORS

* **Focus Window:** Fix all PROTOCOL violations (bare except, dependency pinning, model ID) and migrate sessionStorage → localStorage for key persistence.

* **Architectural Regret Disclosures:**

  | Shortcut | Why Tolerated | Repayment Trigger |
  |---|---|---|
  | Single index.html (no build) | No Node.js in Docker image; HF Spaces prefers simplicity | When JS exceeds 1000 lines or component count > 10 |
  | Hardcoded provider list | No registry needed yet | When 4th provider is added |
  | No tests (legacy) | Initial commit predates governance | First cycle — tests must ship with first fix |
