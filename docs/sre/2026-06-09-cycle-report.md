# SRE Duty Cycle Report — 2026-06-09

Scope: FAJU85/devforge (GitHub) → vooom/devforge (HF Space). Telemetry:
Sentry (org `tococolors`), GitHub Actions, repo/IaC audit.

## Phase 1 — Observe & Detect

**Golden signals (as available on this stack):**

- **Errors:** 1,262 Sentry error events over 30 days. Last 24 h: ~15 events —
  12 from one frontend crash class (PYTHON-1D et al.), 3 from a backend port
  bind race.
- **Traffic / Latency / Saturation:** no request-volume or latency telemetry
  is queryable (frontend traces sampled at 0.1, no backend transaction
  metrics). **Gap — see KPI section.**

**Incidents triaged:**

| ID | Incident | Sev | Disposition |
|---|---|---|---|
| INC-1 | Provider-switch crash (`saveEnhance` null deref), 6 Sentry issues, user-facing | P1 | Root-caused from stack trace; fixed + regression test; needs merge to main. Post-mortem: `docs/postmortems/2026-06-09-provider-switch-crash.md` |
| INC-2 | `[Errno 98] port 7860 in use` ×3 during Space restart | P3 | Transient restart race, self-healed; no action — known HF Spaces behavior during rebuilds |
| INC-3 | Playwright E2E red on every run (stale assertions) | P2 | Alert-fatigue generator masking real regressions; spec fixed |
| INC-4 | monitor-hf-build workflow startup-failure on every deploy (0 jobs) | P2 | Our detection layer was dead → direct MTTD impact; YAML repaired |

## Phase 2 — Maintain & Harden

- **Reliability-pattern audit (main.py):** outbound HTTP calls consistently
  carry timeouts (10–90 s) ✅; graceful provider-error messaging present ✅;
  **rate limiting was absent** ❌ → added brute-force protection to
  `/api/admin/login` (5 failed attempts / 5 min / IP → 429) plus
  constant-time credential comparison. 6 new tests.
- **Infrastructure parity:** `git diff origin/main` over Dockerfile,
  requirements, workflows, configs → **zero drift**. Branch diverges from
  main only by this cycle's fix commits. ✅
- **Golden paths:** all infrastructure lives in `.github/workflows/`; no
  rogue/manual provisioning found. One workflow file was syntactically dead
  (INC-4) — repaired and all 7 workflows now parse.

## Phase 3 — Release & Deploy

- **Gate added:** `sync-to-hf.yml` now runs a pytest gate job before any
  push to the Space. Previously deploy and CI raced — a red build could ship.
- **Automated rollback added:** if the post-deploy HF build poll fails, the
  pipeline force-pushes the previous main commit back to the Space.
- **Canary:** a true 1–5 % traffic canary is not platform-possible on a
  single free HF Space. Compensating controls: test gate + post-deploy
  health poll + auto-rollback + (now working) build monitor with AI
  auto-fix. Flagged as accepted deviation.

## Phase 4 — Optimize & Forecast

- **FinOps:** `evolution.yml` cron tuned `*/30 * * * *` → `0 */3 * * *`.
  GitHub was already throttling actual delivery to ~every 3 h; the
  30-minute cron only queued churn. Removes ~40 phantom scheduled runs/day.
  Fixing the always-red Playwright job also stops wasted runner minutes
  (3 retries × every push).
- **Error budget:** with a 99.9 % SLO, the 30-day budget in *events* cannot
  be computed without request totals. Error-event trend: 1,262/30 d ≈ 42/day
  average; the last-24 h count (~15) is *below* trend. **Budget is burning
  but not critically; circuit-breaker condition (0 % remaining) not met —
  feature deploys may continue once INC-1 fix is merged.**

## Phase 5 — Learn & Document

- Post-mortem written for INC-1 with owners/deadlines (see file above).
- **DR readiness:** source of truth is GitHub (re-deployable to any Space in
  minutes; HF Space storage is ephemeral by design). Gaps flagged:
  1. `main` lacks branch protection — history is not WORM; a force-push can
     destroy "backups". *Recommend: protect main, require PRs.*
  2. `feature_flags.json` (runtime flag state) is gitignored and lives only
     on the Space — lost on every rebuild. *Recommend: persist flags to HF
     dataset repo or accept reset-on-deploy.*
  3. No DR game day on record. *Recommend: 30-min exercise — delete and
     recreate the Space from repo + secrets checklist (HF_TOKEN,
     ANTHROPIC_API_KEY, GITHUB_CLIENT_ID/SECRET, SENTRY_DSN, ADMIN_*).*

## Standing KPIs

| KPI | Target | Current | Verdict |
|---|---|---|---|
| SLO compliance | ≥99.9 % requests OK | **Not measurable** — no request-volume telemetry | ❌ Instrument first (PostHog pageviews or Sentry transactions) |
| Error-budget burn | Linear, no depletion | ~15 events/24 h vs 42/day 30-d mean — sub-linear | ✅ No circuit breaker |
| MTTD | Minimize | INC-1: ~7 min (Sentry) but no alert routing; INC-4 proved the auto-monitor was dead | ⚠️ Fixed monitor; add Sentry alert rule → GitHub issue |
| MTTR | Minimize | INC-1: fix authored same cycle; restoration blocked on human merge | ⚠️ Merge to main is the bottleneck |
| Toil % | <50 % | This cycle ≈ 30 % toil (telemetry pulls) / 70 % engineering (fixes, gates, docs) | ✅ |

## Carried Actions for Next Cycle

1. **Merge `claude/exciting-galileo-7UDWc` → `main`** (restores production, INC-1).
2. Resolve the six Sentry issues once the deploy is verified RUNNING.
3. Add a Sentry alert rule (new issue → GitHub issue) to close the MTTD gap.
4. Instrument request counts to make the SLO computable.
5. Branch-protect `main`; schedule the first DR game day.
