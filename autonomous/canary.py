"""Canary health analysis — decides rollout / hold / rollback based on metrics."""
from __future__ import annotations


def analyze(
    flag_name: str,
    error_rate_canary: float,
    error_rate_baseline: float,
    latency_canary_ms: float,
    latency_baseline_ms: float,
    sample_size: int,
) -> dict:
    """Evaluate canary metrics and return a recommended action.

    Returns a dict with keys:
        action: "rollout" | "hold" | "rollback"
        reason: human-readable explanation
        next_rollout_pct: suggested rollout_pct after applying action
    """
    error_delta = error_rate_canary - error_rate_baseline
    latency_delta = latency_canary_ms - latency_baseline_ms
    latency_pct_increase = (
        (latency_delta / latency_baseline_ms * 100)
        if latency_baseline_ms > 0
        else 0.0
    )

    if error_delta > 2.0 or latency_pct_increase > 50.0:
        return {
            "action": "rollback",
            "reason": (
                f"Error rate increase {error_delta:.2f}% > 2% "
                f"or latency increase {latency_pct_increase:.1f}% > 50%"
            ),
            "next_rollout_pct": 0,
        }

    if error_delta < 0.5 and latency_pct_increase < 10.0 and sample_size >= 50:
        current_pct = _infer_current_pct_from_sample(sample_size)
        return {
            "action": "rollout",
            "reason": (
                f"Error rate increase {error_delta:.2f}% < 0.5%, "
                f"latency increase {latency_pct_increase:.1f}% < 10%, "
                f"sample_size {sample_size} >= 50"
            ),
            "next_rollout_pct": _next_pct(current_pct),
        }

    return {
        "action": "hold",
        "reason": (
            f"Metrics in grey zone: error_delta={error_delta:.2f}%, "
            f"latency_pct={latency_pct_increase:.1f}%, "
            f"sample_size={sample_size}"
        ),
        "next_rollout_pct": None,
    }


def _next_pct(current: int) -> int:
    """Progression: 0/1 → 5 → 25 → 100."""
    progression = [1, 5, 25, 100]
    for step in progression:
        if current < step:
            return step
    return 100


def _infer_current_pct_from_sample(sample_size: int) -> int:
    """Approximate current rollout pct from sample size (best-effort)."""
    if sample_size >= 1000:
        return 100
    if sample_size >= 250:
        return 25
    if sample_size >= 50:
        return 5
    return 1
