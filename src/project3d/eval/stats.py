"""Per-case distribution summaries and bootstrap confidence intervals."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt

N_BOOT = 10_000
MIN_CASES_FOR_CI = 10  # below this a CI is not meaningful; reported as None


def describe(values: npt.ArrayLike) -> dict:
    """n, mean, median, IQR, 10th percentile, min and max, ignoring NaN (counted)."""
    scores = np.asarray(values, dtype=float)
    ok = scores[~np.isnan(scores)]
    out = {"n": int(ok.size), "n_undefined": int(scores.size - ok.size)}
    if ok.size == 0:
        return out
    q10, q1, med, q3 = np.percentile(ok, [10, 25, 50, 75])
    out.update(mean=float(ok.mean()), median=float(med), q1=float(q1), q3=float(q3),
               p10=float(q10), min=float(ok.min()), max=float(ok.max()))
    return out


def bootstrap_ci(values: npt.ArrayLike, n_boot: int = N_BOOT, seed: int = 42,
                 alpha: float = 0.05) -> list[float] | None:
    """Percentile bootstrap CI of the mean over cases; None if too few cases."""
    scores = np.asarray(values, dtype=float)
    scores = scores[~np.isnan(scores)]
    if scores.size < MIN_CASES_FOR_CI:
        return None
    rng = np.random.default_rng(seed)
    means = scores[rng.integers(0, scores.size, size=(n_boot, scores.size))].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return [float(lo), float(hi)]


def describe_with_ci(values: npt.ArrayLike, **bootstrap_options: Any) -> dict:
    """``describe`` plus the bootstrap 95% CI of the mean."""
    return {**describe(values), "ci95": bootstrap_ci(values, **bootstrap_options)}
