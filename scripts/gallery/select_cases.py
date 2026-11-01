"""SPEC 009: choose the gallery cases by a fixed rule, so they can't be picked to flatter the model.

Example (Kaggle)::

    python scripts/gallery/select_cases.py --per-case eval_pp/per_case.csv \
        --case-features case_features.csv --out gallery_cases.json

Groups are filled in this order, and a case appears only once:
worst, best, median, small tumor, with cyst. Worst comes first so it can't lose a case.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

GROUP_SIZES = {"worst": 2, "best": 2, "median": 3, "small_tumor": 2, "with_cyst": 2}


def _is_true(value) -> bool:
    return str(value).strip().lower() in ("1", "true")


def select(per_case: list[dict], features: dict[str, dict]) -> list[dict]:
    """Return ``{"case_id", "group"}`` rows, using ``mean_dice`` and the SPEC 002 features."""
    score = {r["case_id"]: float(r["mean_dice"]) for r in per_case}
    by_score = sorted(score, key=lambda c: (score[c], c))
    chosen: dict[str, str] = {}

    def take(group: str, ordered: list[str]) -> None:
        for case in [c for c in ordered if c not in chosen][:GROUP_SIZES[group]]:
            chosen[case] = group

    def nearest_median(cases: list[str]) -> list[str]:
        mid = statistics.median(score[c] for c in cases)
        return sorted(cases, key=lambda c: (abs(score[c] - mid), c))

    take("worst", by_score)
    take("best", by_score[::-1])
    take("median", nearest_median(by_score))
    take("small_tumor", nearest_median([c for c in by_score if features[c]["size_bin"] == "small"]))
    take("with_cyst", nearest_median([c for c in by_score if _is_true(features[c]["has_cyst"])]))
    return [{"case_id": c, "group": g} for c, g in chosen.items()]


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--per-case", type=Path, required=True)
    ap.add_argument("--case-features", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    features = {r["case_id"]: r for r in read_csv(args.case_features)}
    rows = select(read_csv(args.per_case), features)
    args.out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"selected {len(rows)} cases: {rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
