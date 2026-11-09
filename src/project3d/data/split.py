"""Case-level stratified train/validation/test split (SPEC 002, D-012).

Strata are ``cohort | size_bin | cyst``. Per-stratum counts are allocated by
largest-remainder apportionment, so the global counts hit the target fractions
exactly and every stratum is represented proportionally. Cases are shuffled
within each stratum with a fixed seed.

The saved ``split.json`` is the authority. Its fingerprint is recorded so any
later change is detectable; the split is never regenerated after training.
"""

from __future__ import annotations

import hashlib
import json
import math
import random

ROLES = ("train", "val", "test")


def stratum_key(row: dict) -> str:
    """The stratum a case belongs to, e.g. ``kits23|small|nocyst``."""
    return f"{row['cohort']}|{row['size_bin']}|{'cyst' if row['has_cyst'] else 'nocyst'}"


def _apportion(sizes: dict[str, int], total: int, capacity: dict[str, int]) -> dict[str, int]:
    """Split ``total`` across strata proportionally to ``sizes``, within ``capacity``."""
    n = sum(sizes.values())
    if n == 0 or total == 0:
        return {k: 0 for k in sizes}
    quota = {k: sizes[k] * total / n for k in sizes}
    alloc = {k: min(math.floor(quota[k]), capacity[k]) for k in sizes}
    remaining = total - sum(alloc.values())
    # Largest remainder first; ties broken by stratum name for determinism.
    order = sorted(sizes, key=lambda k: (-(quota[k] - math.floor(quota[k])), k))
    while remaining > 0:
        progressed = False
        for k in order:
            if remaining == 0:
                break
            if alloc[k] < capacity[k]:
                alloc[k] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            raise ValueError("not enough cases to satisfy the requested split")
    return alloc


def make_split(rows: list[dict], seed: int = 42,
               fractions: tuple[float, float, float] = (0.70, 0.15, 0.15)) -> dict[str, str]:
    """Return ``{case_id: role}`` with role in ``train``/``val``/``test``."""
    if abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("fractions must sum to 1")
    ids = [r["case_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate case_id in feature rows")

    strata: dict[str, list[str]] = {}
    for r in rows:
        strata.setdefault(stratum_key(r), []).append(r["case_id"])
    sizes = {k: len(v) for k, v in strata.items()}
    n = len(rows)
    n_test = round(n * fractions[2])
    n_val = round(n * fractions[1])

    test_alloc = _apportion(sizes, n_test, sizes)
    val_alloc = _apportion(sizes, n_val, {k: sizes[k] - test_alloc[k] for k in sizes})

    rng = random.Random(seed)
    roles: dict[str, str] = {}
    for key in sorted(strata):
        members = sorted(strata[key])
        rng.shuffle(members)
        t, v = test_alloc[key], val_alloc[key]
        for i, cid in enumerate(members):
            roles[cid] = "test" if i < t else "val" if i < t + v else "train"
    return dict(sorted(roles.items()))


def fingerprint(roles: dict[str, str]) -> str:
    """SHA-256 of the canonical ``{case_id: role}`` mapping."""
    canon = json.dumps(dict(sorted(roles.items())), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def nnunet_splits(roles: dict[str, str]) -> list[dict[str, list[str]]]:
    """nnU-Net ``splits_final.json`` content: one fold, train vs val. Test is excluded."""
    return [{
        "train": sorted(c for c, r in roles.items() if r == "train"),
        "val": sorted(c for c, r in roles.items() if r == "val"),
    }]


def summary(rows: list[dict], roles: dict[str, str]) -> dict:
    """Counts per role, overall and by each stratification variable."""
    out: dict = {"total": {r: 0 for r in ROLES}}
    for var in ("cohort", "size_bin", "has_cyst"):
        out[var] = {}
    for row in rows:
        role = roles[row["case_id"]]
        out["total"][role] += 1
        for var in ("cohort", "size_bin", "has_cyst"):
            bucket = out[var].setdefault(str(row[var]), {r: 0 for r in ROLES})
            bucket[role] += 1
    return out
