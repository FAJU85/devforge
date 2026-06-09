# Blameless Post-Mortem: Provider-Switch Crash in Production

**Date of incident:** 2026-06-08 ~23:46 UTC → ongoing until fix deploy
**Severity:** P1 (core user journey broken — AI provider selection)
**Detected by:** Sentry (issues PYTHON-1D/1E/1F/1G/1H/1J — 6 grouped issues, 12 events, ≥1 unique user)
**Status:** Fix merged to `claude/exciting-galileo-7UDWc` (commit `3a13324`); production restoration requires merge to `main`.

## Impact

Any user who clicked the **External API** provider button (and several adjacent
config controls) hit an unhandled `TypeError: Cannot read properties of null
(reading 'value')`. The click handler chain `setProvGroup → setProv →
saveEnhance` aborted mid-flight, so provider settings were not persisted and
no visible feedback was shown. Confirmed user impact from Riyadh, SA (4
repeat attempts — a classic "it's broken, try again" signature).

## Timeline

| Time (UTC) | Event |
|---|---|
| 2026-06-08 23:39 | Deploy to HF Space (Sync workflow run on main) |
| 2026-06-08 23:46 | First Sentry event (PYTHON-1D) |
| 2026-06-08 23:46–23:51 | 12 events across 6 stack-position groups |
| 2026-06-09 (this cycle) | Detected during SRE telemetry review; root cause from Sentry stack trace; fix authored, tested, pushed |

## Root Cause

`saveEnhance()` serializes ~20 form fields to localStorage by reading
`$('id').value` / `$('id').checked` **without null guards**. The UI has been
through several large refactors (panels moved, sections removed) and the
function's element list silently drifted out of sync with the DOM. The first
missing element turns every settings save into an unhandled exception.

This is the second occurrence of this *class* of failure (a previous cycle
shipped duplicate element IDs after a layout refactor). The systemic flaw is
not any single missing element — it is that **the settings-persistence layer
assumed DOM shape instead of tolerating drift**, while the UI layer is under
continuous autonomous + manual refactoring.

## What Went Well

- Sentry captured the full stack trace with snippet context — root cause was
  identifiable from telemetry alone, no reproduction needed.
- The error was contained to settings persistence; chat itself kept working.

## What Went Poorly

- The Playwright E2E suite was red on every run for unrelated stale
  assertions ("Canary Analysis section"), so a *new* red signal had no chance
  of standing out — alert fatigue by design.
- The deploy pipeline pushed to production in parallel with CI rather than
  gated on it.
- The HF build monitor workflow (our auto-detection layer) had been dead for
  every run due to a YAML startup failure, so no automated issue was filed.

## Action Items

| # | Action | Owner | Status / Due |
|---|---|---|---|
| 1 | Null-safe DOM accessors (`gv`/`gc`/`sv`) in `saveEnhance`, `restoreEnhance`, `updBadge`, `send` | SRE cycle (this) | ✅ Done — `3a13324` |
| 2 | Regression e2e test: switch provider groups, assert zero page errors | SRE cycle (this) | ✅ Done — `3a13324` |
| 3 | Remove stale e2e assertions so the suite can go green and regain signal value | SRE cycle (this) | ✅ Done — `3a13324` |
| 4 | Gate HF deploys on a passing test job; auto-rollback on failed build poll | SRE cycle (this) | ✅ Done — `4a0870a` |
| 5 | Repair monitor-hf-build.yml YAML so auto-detection works again | SRE cycle (this) | ✅ Done — `4a0870a` |
| 6 | **Merge branch to `main` to restore production** | Repo owner (@FAJU85) | ⏳ Pending — required for user-facing fix |
| 7 | Resolve Sentry issues PYTHON-1D/1E/1F/1G/1H/1J after deploy verifies | Repo owner | ⏳ After #6 |
| 8 | Consider a `pageerror`-asserting smoke test for every panel/tab as a deploy gate | Next cycle | Proposed |
