"""Split nnU-Net preprocessing into shards that fit Kaggle's output limit (D-017).

Preprocessed 3d_fullres KiTS23 is about 50 GB, but one Kaggle notebook can save
about 20 GB. So each shard notebook preprocesses one contiguous group of cases,
sized by the number of voxels after resampling. Cases far larger than the rest
(whole-body scans) are left out of training: one Kaggle worker runs out of RAM on them.
"""

from __future__ import annotations

import json
from pathlib import Path

MAX_MVOX = 350  # resampled size limit in millions of voxels; the median case is about 100


def resampled_mvox(shape: tuple[int, ...], spacing: tuple[float, ...], target: tuple[float, ...]) -> float:
    """Millions of voxels after resampling ``shape`` at ``spacing`` to ``target`` spacing."""
    n = 1.0
    for size, sp, t in zip(shape, spacing, target):
        n *= size * sp / t
    return n / 1e6


def case_mvox(features: list[dict], target: tuple[float, ...]) -> dict[str, float]:
    """Resampled size per case from SPEC 002 ``case_features.csv`` rows (shape/spacing as AxBxC)."""
    out = {}
    for row in features:
        shape = tuple(int(x) for x in row["shape"].split("x"))
        spacing = tuple(float(x) for x in row["spacing_mm"].split("x"))
        out[row["case_id"]] = resampled_mvox(shape, spacing, target)
    return out


def select_cases(roles: dict[str, str], mvox: dict[str, float],
                 max_mvox: float = MAX_MVOX) -> tuple[list[str], list[str]]:
    """Return (cases to preprocess, excluded cases). Only train/val cases; only train cases are excluded."""
    keep, excluded = [], []
    for case in sorted(c for c, r in roles.items() if r != "test"):
        if roles[case] == "train" and mvox[case] > max_mvox:
            excluded.append(case)
        else:
            keep.append(case)
    return keep, excluded


def filter_splits(splits: list[dict[str, list[str]]], excluded: list[str]) -> list[dict[str, list[str]]]:
    drop = set(excluded)
    return [{k: [c for c in v if c not in drop] for k, v in fold.items()} for fold in splits]


def plan_shards(cases: list[str], mvox: dict[str, float], n_shards: int) -> list[list[str]]:
    """Contiguous groups of sorted case IDs with about equal total voxels."""
    cases = sorted(cases)
    total = sum(mvox[c] for c in cases)
    shards: list[list[str]] = [[] for _ in range(n_shards)]
    done = 0.0
    for c in cases:
        k = min(int((done + mvox[c] / 2) / total * n_shards), n_shards - 1)
        shards[k].append(c)
        done += mvox[c]
    return shards


def write_plan(path: Path, roles: dict[str, str], mvox: dict[str, float], n_shards: int,
               max_mvox: float = MAX_MVOX) -> dict:
    keep, excluded = select_cases(roles, mvox, max_mvox)
    plan = {
        "max_mvox": max_mvox, "n_shards": n_shards,
        "excluded": {c: round(mvox[c]) for c in excluded},
        "shards": plan_shards(keep, mvox, n_shards),
    }
    plan["shard_mvox"] = [round(sum(mvox[c] for c in s)) for s in plan["shards"]]
    path.write_text(json.dumps(plan, indent=1))
    return plan
