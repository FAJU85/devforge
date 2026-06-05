"""Autonomous evolution cycle: manages the full flag lifecycle.

Lifecycle: dark(0%) → canary(1%) → canary(5%) → canary(25%) → canary(50%) → live(100%)
                                        ↓ bad metrics at any canary step
                                     rollback(0%)
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from . import canary as _canary
from . import flags as _flags
from .audit import log_event

_log = logging.getLogger(__name__)


async def run_cycle(
    flag_name: str,
    metrics: dict,
    *,
    github_token: str = "",
    github_owner: str = "",
    github_repo: str = "",
) -> dict:
    """Run one evolution iteration for a single flag.

    metrics must contain:
        error_rate_canary, error_rate_baseline (float, percentage)
        latency_canary_ms, latency_baseline_ms (float, ms > 0)
        sample_size (int)
    """
    flag_data = next((f for f in _flags.get_all() if f["name"] == flag_name), None)
    if not flag_data:
        return {"flag": flag_name, "action": "skip", "reason": "Flag not found"}

    current_pct = int(flag_data.get("rollout_pct", 0))
    current_status = flag_data.get("status", "dark")

    if current_status in ("live", "rollback"):
        return {"flag": flag_name, "action": "skip", "reason": f"Flag already {current_status}"}

    try:
        result = _canary.analyze(
            flag_name=flag_name,
            current_rollout_pct=current_pct,
            error_rate_canary=float(metrics["error_rate_canary"]),
            error_rate_baseline=float(metrics["error_rate_baseline"]),
            latency_canary_ms=float(metrics["latency_canary_ms"]),
            latency_baseline_ms=float(metrics["latency_baseline_ms"]),
            sample_size=int(metrics["sample_size"]),
        )
    except (KeyError, ValueError) as exc:
        return {"flag": flag_name, "action": "error", "reason": str(exc)}

    action = result["action"]
    reason = result["reason"]
    next_pct = result.get("next_rollout_pct")

    if action == "rollback":
        _flags.update(flag_name, rollout_pct=0, status="rollback", enabled=False)
        log_event(flag_name, "rollback", reason, metrics, current_pct, 0)
        # Optionally open a rollback PR
        if all([github_token, github_owner, github_repo]):
            await _open_rollback_pr(flag_name, reason, github_token, github_owner, github_repo)
        return {"flag": flag_name, "action": "rollback", "reason": reason, "rollout_pct": 0}

    if action == "rollout" and next_pct is not None:
        new_status = "live" if next_pct >= 100 else "canary"
        _flags.update(flag_name, rollout_pct=next_pct, status=new_status)
        log_event(flag_name, "rollout" if new_status == "canary" else "promote_live", reason, metrics, current_pct, next_pct)
        return {"flag": flag_name, "action": action, "reason": reason, "rollout_pct": next_pct, "status": new_status}

    # hold
    log_event(flag_name, "hold", reason, metrics, current_pct, current_pct)
    return {"flag": flag_name, "action": "hold", "reason": reason, "rollout_pct": current_pct}


async def run_all_canary_flags(
    metrics: dict,
    *,
    github_token: str = "",
    github_owner: str = "",
    github_repo: str = "",
) -> list[dict]:
    """Run the evolution cycle for every flag currently in 'canary' or 'dark' status."""
    flags = [f for f in _flags.get_all() if f.get("status") in ("canary", "dark") and f.get("enabled", True)]
    if not flags:
        return []
    tasks = [
        run_cycle(
            f["name"], metrics,
            github_token=github_token, github_owner=github_owner, github_repo=github_repo,
        )
        for f in flags
    ]
    return list(await asyncio.gather(*tasks))


async def _open_rollback_pr(
    flag_name: str, reason: str, token: str, owner: str, repo: str,
) -> None:
    """Best-effort: open a GitHub PR to document the rollback."""
    try:
        import requests
        from .fixer import _gh_base, _gh_hdrs, _urlquote, _get_default_branch_and_sha, _create_branch, _open_pr

        default_branch, sha = await asyncio.to_thread(
            _get_default_branch_and_sha, owner, repo, token
        )
        branch = f"auto/rollback-{flag_name}"
        try:
            await asyncio.to_thread(_create_branch, owner, repo, token, branch, sha)
        except requests.RequestException:
            pass  # branch may already exist

        pr_body = (
            f"## Automated Rollback: `{flag_name}`\n\n"
            f"**Reason:** {reason}\n\n"
            "The evolution cycle detected unhealthy metrics and has automatically set "
            f"`{flag_name}` rollout to 0% and status to `rollback`.\n\n"
            "Review the metrics, fix the underlying issue, and delete this PR "
            "when ready to re-enable the feature."
        )
        import requests as _req
        payload = {"title": f"[Rollback] {flag_name}", "head": branch, "base": default_branch, "body": pr_body}
        r = await asyncio.to_thread(
            lambda: _req.post(
                f"{_gh_base(owner, repo)}/pulls",
                headers=_gh_hdrs(token), json=payload, timeout=15,
            )
        )
        r.raise_for_status()
    except Exception as exc:
        _log.warning("Could not open rollback PR for %s: %s", flag_name, exc)
