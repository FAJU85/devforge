"""Real metric collection from PostHog and Rollbar APIs.

The flag routing middleware in main.py captures `request_completed` events to
PostHog with `flag`, `bucket` (canary | control), `latency_ms`, and
`status_code` properties.  This module queries those events to produce the
canary-vs-baseline metrics that drive the evolution cycle.

Rollbar is used as a secondary source for total active error counts when
PostHog is not configured.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

_log = logging.getLogger(__name__)


# ── PostHog ───────────────────────────────────────────────────────────────────

def fetch_posthog_metrics(
    api_key: str,
    project_id: str,
    flag_name: str,
    hours: int = 1,
) -> Optional[dict]:
    """Query PostHog via HogQL for canary vs control error rates and p95 latency.

    Requires events captured by the flag routing middleware with properties:
        flag=flag_name, bucket='canary'|'control', latency_ms=float,
        status_code=int.

    Returns None when the API is unreachable or returns no data.
    """
    if not api_key or not project_id:
        return None

    try:
        import requests as _req

        host = os.environ.get("POSTHOG_HOST", "https://us.posthog.com")

        # Sanitise flag_name for safe embedding in HogQL
        safe_flag = flag_name.replace("'", "\\'").replace("\\", "\\\\")

        hql = f"""
            SELECT
                properties.bucket AS bucket,
                count()                                              AS requests,
                countIf(toInt32OrNull(properties.status_code) >= 500) AS errors,
                quantile(0.95)(toFloat64OrNull(properties.latency_ms)) AS p95_latency_ms
            FROM events
            WHERE event = 'request_completed'
              AND properties.flag = '{safe_flag}'
              AND timestamp >= now() - interval {int(hours)} hour
            GROUP BY bucket
        """

        r = _req.post(
            f"{host}/api/projects/{project_id}/query",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": {"kind": "HogQLQuery", "query": hql}},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        rows = data.get("results") or []
        if not rows:
            return None

        buckets: dict[str, dict] = {}
        for row in rows:
            bucket, req_count, err_count, p95 = row[0], row[1], row[2], row[3]
            req_count = req_count or 0
            if req_count > 0:
                buckets[str(bucket)] = {
                    "requests": req_count,
                    "errors": err_count or 0,
                    "error_rate_pct": (err_count or 0) / req_count * 100.0,
                    "p95_latency_ms": p95 or 0.0,
                }

        canary = buckets.get("canary", {})
        control = buckets.get("control", {})

        if not canary and not control:
            return None

        return {
            "error_rate_canary": round(canary.get("error_rate_pct", 0.0), 4),
            "error_rate_baseline": round(control.get("error_rate_pct", 0.0), 4),
            "latency_canary_ms": round(canary.get("p95_latency_ms", 100.0), 2),
            "latency_baseline_ms": round(control.get("p95_latency_ms", 100.0) or 100.0, 2),
            "sample_size": int(canary.get("requests", 0)),
            "source": "posthog",
            "hours": hours,
            "buckets": buckets,
        }

    except Exception as exc:
        _log.warning("PostHog metrics unavailable for %s: %s", flag_name, exc)
        return None


# ── Rollbar ───────────────────────────────────────────────────────────────────

def fetch_rollbar_error_count(token: str, hours: int = 1) -> Optional[int]:
    """Return total active Rollbar item count for the last *hours* hours.

    This gives aggregate error volume but cannot segment by flag bucket without
    custom tags.  Used as a secondary signal when PostHog is not configured.
    """
    if not token:
        return None

    try:
        import requests as _req

        now = int(time.time())
        r = _req.get(
            "https://api.rollbar.com/api/1/items",
            headers={"X-Rollbar-Access-Token": token},
            params={
                "status": "active",
                "environment": os.environ.get("ROLLBAR_ENVIRONMENT", "production"),
                "from_timestamp": now - hours * 3600,
                "per_page": 1,
                "page": 1,
            },
            timeout=10,
        )
        r.raise_for_status()
        return int(r.json().get("result", {}).get("total_count", 0))

    except Exception as exc:
        _log.warning("Rollbar error count unavailable: %s", exc)
        return None


# ── Combined ──────────────────────────────────────────────────────────────────

def fetch_metrics_for_flag(
    flag_name: str,
    *,
    posthog_api_key: str = "",
    posthog_project_id: str = "",
    rollbar_token: str = "",
    hours: int = 1,
) -> dict:
    """Fetch real canary metrics for *flag_name* from PostHog and/or Rollbar.

    Tries PostHog first (full canary/control segmentation).
    Falls back to Rollbar (aggregate error count only).
    Returns a 'source' key indicating data origin:
        'posthog'           — full metrics from PostHog events
        'rollbar_partial'   — only total error count from Rollbar
        'unavailable'       — no APIs configured or reachable

    The return dict is always safe to merge into an EvolutionMetrics payload;
    callers should check 'source' before trusting the values.
    """
    ph_key = posthog_api_key or os.environ.get("POSTHOG_API_KEY", "")
    ph_proj = posthog_project_id or os.environ.get("POSTHOG_PROJECT_ID", "")

    if ph_key and ph_proj:
        result = fetch_posthog_metrics(ph_key, ph_proj, flag_name, hours)
        if result:
            return result

    rb_token = rollbar_token or os.environ.get("ROLLBAR_ACCESS_TOKEN", "")
    count = fetch_rollbar_error_count(rb_token, hours)
    if count is not None:
        # We can't split errors by bucket without PostHog, so surface the raw
        # count and let the caller decide what to do with it.
        return {
            "error_rate_canary": 0.0,
            "error_rate_baseline": 0.0,
            "latency_canary_ms": 100.0,
            "latency_baseline_ms": 100.0,
            "sample_size": 0,
            "source": "rollbar_partial",
            "hours": hours,
            "total_errors": count,
            "note": (
                "Only aggregate error count available from Rollbar. "
                "Configure POSTHOG_API_KEY + POSTHOG_PROJECT_ID for full "
                "canary/control segmentation."
            ),
        }

    return {
        "source": "unavailable",
        "note": (
            "No metrics APIs are reachable. "
            "Set POSTHOG_API_KEY + POSTHOG_PROJECT_ID (recommended) "
            "or ROLLBAR_ACCESS_TOKEN."
        ),
    }
