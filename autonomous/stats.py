"""Statistical significance testing for canary analysis.

Implements two-proportion z-test, Wilson confidence intervals, and
minimum sample-size calculation without external dependencies.
"""
from __future__ import annotations

import math


def two_proportion_z_test(
    p1: float,
    n1: int,
    p2: float,
    n2: int,
    alpha: float = 0.05,
) -> dict:
    """Two-proportion z-test: is canary error rate p1 significantly different from baseline p2?

    p1, p2: proportions in [0..1] (NOT percentages)
    n1, n2: sample sizes (>= 1)
    alpha:   significance threshold (default 5%)

    Returns z_score, p_value, significant bool, confidence label.
    """
    if n1 < 1 or n2 < 1:
        return {
            "z_score": 0.0,
            "p_value": 1.0,
            "significant": False,
            "confidence": "insufficient_data",
        }

    p1 = max(0.0, min(1.0, p1))
    p2 = max(0.0, min(1.0, p2))

    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    denom = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))

    if denom == 0:
        return {
            "z_score": 0.0,
            "p_value": 1.0,
            "significant": False,
            "confidence": "zero_variance",
        }

    z = (p1 - p2) / denom
    p_value = 2.0 * (1.0 - _norm_cdf(abs(z)))
    significant = p_value < alpha

    if significant:
        if p_value < 0.001:
            confidence = "very_high (p<0.001)"
        elif p_value < 0.01:
            confidence = "high (p<0.01)"
        else:
            confidence = f"moderate (p={p_value:.3f})"
    else:
        confidence = f"not_significant (p={p_value:.3f})"

    return {
        "z_score": round(z, 4),
        "p_value": round(p_value, 6),
        "significant": significant,
        "confidence": confidence,
    }


def wilson_ci(rate: float, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion.

    rate: proportion [0..1]
    n:    sample size
    Returns (lower_pct, upper_pct) as percentages in [0..100].
    """
    if n < 1:
        return (0.0, 100.0)

    rate = max(0.0, min(1.0, rate))
    z = _norm_ppf((1.0 + confidence) / 2.0)
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (rate + z2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(rate * (1.0 - rate) / n + z2 / (4.0 * n * n))

    return (
        round(max(0.0, centre - margin) * 100, 4),
        round(min(1.0, centre + margin) * 100, 4),
    )


def min_sample_size(
    baseline_rate: float,
    mde: float = 0.01,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    """Minimum sample size per variant for a two-proportion z-test.

    baseline_rate: expected baseline error rate [0..1]
    mde:           minimum detectable effect (absolute, e.g. 0.01 = 1%)
    Returns minimum n per variant (minimum 50).
    """
    baseline_rate = max(1e-6, min(1 - 1e-6, baseline_rate))
    canary_rate = max(1e-6, min(1 - 1e-6, baseline_rate + mde))
    p_bar = (baseline_rate + canary_rate) / 2.0

    z_alpha = _norm_ppf(1.0 - alpha / 2.0)
    z_beta = _norm_ppf(power)

    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_beta * math.sqrt(
            baseline_rate * (1 - baseline_rate) + canary_rate * (1 - canary_rate)
        )
    ) ** 2

    n = numerator / (mde ** 2)
    return max(50, int(math.ceil(n)))


def analyze_significance(
    error_rate_canary: float,
    error_rate_baseline: float,
    latency_canary_ms: float,
    latency_baseline_ms: float,
    sample_size: int,
) -> dict:
    """Full statistical analysis of canary vs baseline metrics.

    Inputs use percent values (0..100) for error rates and ms for latency.
    Returns a dict with significance tests, CIs, required sample size, and summary.
    """
    p_canary = error_rate_canary / 100.0
    p_baseline = error_rate_baseline / 100.0
    n = max(1, sample_size)

    z_test = two_proportion_z_test(p_canary, n, p_baseline, n)
    canary_ci = wilson_ci(p_canary, n)
    baseline_ci = wilson_ci(p_baseline, n)

    latency_pct = (
        (latency_canary_ms - latency_baseline_ms) / latency_baseline_ms * 100.0
        if latency_baseline_ms > 0
        else 0.0
    )

    required_n = min_sample_size(p_baseline, mde=0.01)
    sufficient = sample_size >= required_n

    parts: list[str] = []
    if not sufficient:
        parts.append(f"Insufficient sample (need {required_n}, have {sample_size})")
    if z_test["significant"]:
        parts.append(f"Error rate diff significant [{z_test['confidence']}]")
    else:
        parts.append(f"Error rate diff NOT significant [{z_test['confidence']}]")
    if abs(latency_pct) >= 10:
        direction = "up" if latency_pct > 0 else "down"
        parts.append(f"Latency {direction} {abs(latency_pct):.1f}%")

    return {
        "z_test": z_test,
        "canary_error_ci_95": canary_ci,
        "baseline_error_ci_95": baseline_ci,
        "latency_pct_change": round(latency_pct, 2),
        "required_sample_size": required_n,
        "has_sufficient_sample": sufficient,
        "summary": " | ".join(parts),
    }


# ── Internal math helpers ─────────────────────────────────────────────────────

def _norm_cdf(z: float) -> float:
    """Standard normal CDF using math.erf (accurate to ~7 decimal places)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse normal CDF using Beasley-Springer-Moro initial estimate + Newton refinement."""
    assert 0.0 < p < 1.0, f"p must be in (0, 1), got {p}"

    q = min(p, 1.0 - p)
    t = math.sqrt(-2.0 * math.log(q))
    # Beasley-Springer-Moro rational approximation
    num = 2.515517 + 0.802853 * t + 0.010328 * t * t
    den = 1.0 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t
    x = t - num / den
    if p < 0.5:
        x = -x

    # Two Newton–Raphson refinement steps (halves error at each step)
    _sqrt2pi = math.sqrt(2.0 * math.pi)
    for _ in range(2):
        phi = math.exp(-0.5 * x * x) / _sqrt2pi
        x -= (_norm_cdf(x) - p) / phi

    return x
