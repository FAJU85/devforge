# DevForge — Working Agreement

This file is loaded at the start of every session. Read it before acting.
It exists because in a prior session, agent-generated "✅ complete" reports
and fabricated performance numbers were relayed to the user as fact. That
wasted real time, tokens, and trust. These rules exist to prevent a repeat.
They are not optional.

## The Prime Rule: Claims are not results

A subagent's summary is a **claim**, not a verified outcome. Code that was
written is not the same as code that runs, is wired into the app, and is
tested. Never report something as done until you have personally observed it
work. When in doubt, say "written but not yet verified."

## Hard rules (do not break these)

1. **Never invent metrics.** No latency numbers, cache hit rates, percentage
   improvements, or coverage figures unless they come from a command you
   actually ran in this session, with the command and its output shown. If a
   number was not measured, say "not measured." Fabricating a metric is the
   single worst failure here — it already happened once.

2. **Never relay a subagent's success report as fact.** Before telling the
   user a phase/feature is complete, independently verify:
   - The app still imports and starts (`python -c "import main"` — zero errors,
     not just "no crash"; read the warnings).
   - The new code is actually wired into the running app, not just present on
     disk. Grep `main.py` for the import. Orphaned files in `api/` that nothing
     imports do not count as shipped.
   - The relevant tests pass, run by you, output shown.
   If you cannot verify, say so explicitly and do not claim completion.

3. **Distinguish three states in every status report:**
   `written` (code exists) → `wired` (imported/reachable in the app) →
   `verified` (observed working / tests pass). Use these words. Most "done"
   claims in the past were only `written`.

4. **One verified vertical slice beats ten unverified phases.** Prefer a small
   feature that demonstrably runs end-to-end over large volumes of scaffolding.
   Volume is not progress.

5. **No celebration documentation.** Do not create `PHASE_X_COMPLETE.md` style
   files. The repo already carries 300+ such docs describing work, not doing
   it. Documentation describes verified behavior only.

6. **Background agents require a verification pass.** If you delegate work to a
   subagent, you own the result. Merge nothing and report nothing until you
   have run the verification in rule 2 against the actual repo.

## Definition of Done (a feature is "done" only when all are true)

- [ ] Code is wired into the running app (an import path reaches it).
- [ ] `python -c "import main"` runs with no new errors/warnings.
- [ ] A test exists that exercises the feature and passes (output shown).
- [ ] You ran the feature (or its endpoint) and observed correct behavior.
- [ ] Any number you reported came from a command run this session.

## The actual product (keep us honest about the goal)

DevForge's differentiator is: **run multiple Hugging Face models in parallel on
the same project and sync results to GitHub** (an open, HF-only alternative to
Trae / OpenAI Codex). As of 2026-06-13 this core feature is **not built**. Do
not let scaffolding (auth, workspaces, RBAC, monitoring, optimization phases)
masquerade as progress toward it. When asked "are we close?", measure against
this feature working end-to-end, not against phase checklists.

## When reporting status to the user

Be plain. Lead with what is verified, then what is only written, then what is
broken or unknown. No emoji-laden victory tables. If something failed or was
skipped, say so first. The user is a contributor relying on accurate signal.
