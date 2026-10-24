"""Per-case distribution summaries and bootstrap confidence intervals."""

from __future__ import annotations

import numpy as np

N_BOOT = 10_000
MIN_CASES_FOR_CI = 10  # below this a CI is not meaningful; reported as None


def describe(values) -> dict:
    """n, mean, median, IQR, 10th percentile, min and max, ignoring NaN (counted)."""
    a = np.asarray(values, dtype=float)
    ok = a[~np.isnan(a)]
    out = {"n": int(ok.size), "n_undefined": int(a.size - ok.size)}
    if ok.size == 0:
        return out
    q10, q1, med, q3 = np.percentile(ok, [10, 25, 50, 75])
    out.update(mean=float(ok.mean()), median=float(med), q1=float(q1), q3=float(q3),
               p10=float(q10), min=float(ok.min()), max=float(ok.max()))
    return out


def bootstrap_ci(values, n_boot: int = N_BOOT, seed: int = 42, alpha: float = 0.05):
    """Percentile bootstrap CI of the mean over cases; None if too few cases."""
    a = np.asarray(values, dtype=float)
    a = a[~np.isnan(a)]
    if a.size < MIN_CASES_FOR_CI:
        return None
    rng = np.random.default_rng(seed)
    means = a[rng.integers(0, a.size, size=(n_boot, a.size))].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return [float(lo), float(hi)]


def describe_with_ci(values, **kw) -> dict:
    return {**describe(values), "ci95": bootstrap_ci(values, **kw)}
