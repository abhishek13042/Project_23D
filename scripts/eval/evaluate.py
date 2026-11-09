"""SPEC 004: score predictions on the locked test set.

Example (Kaggle)::

    python scripts/eval/evaluate.py --pred-dir /kaggle/working/spec004/pred_pp \
        --segs-root <KiTS23 segmentations> --split split.json --role test \
        --out-dir /kaggle/working/spec004/eval

Writes per_case.csv and summary.json. Co-primary metrics are the official KiTS23
Dice and surface Dice, averaged over the three HECs per case, then over cases
(D-012). ``--no-official`` is for local smoke tests only: the summary is then
marked ``primary_valid: false``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.data import features, manifest
from project3d.eval import metrics, stats

CROSSCHECK_TOL = 1e-3  # our Dice vs official Dice; larger means a geometry/orientation bug


def score_case(args: tuple) -> dict:
    """Score one predicted case against its label; returns one per-case row."""
    case_id, pred_path, ref_path, use_official = args
    import nibabel as nib

    why = features.geometry_mismatch(pred_path, ref_path)
    if why:
        raise ValueError(f"{case_id}: prediction/reference geometry mismatch ({why})")
    ref_img = nib.load(str(ref_path))
    ref = np.asanyarray(ref_img.dataobj).astype(np.uint8)
    pred = np.asanyarray(nib.load(str(pred_path)).dataobj).astype(np.uint8)
    bad = set(np.unique(pred).tolist()) - features.VALID_LABELS
    if bad:
        raise ValueError(f"{case_id}: prediction has labels {sorted(bad)}")
    spacing = tuple(float(z) for z in ref_img.header.get_zooms()[:3])
    row = {"case_id": case_id, **metrics.case_metrics(pred, ref, spacing)}
    if use_official:
        from project3d.eval import official

        row.update(official.official_case(pred_path, ref_path))
        row["mean_dice"] = float(np.mean([row[f"{h}_dice_official"] for h in metrics.HECS]))
        row["mean_sd"] = float(np.mean([row[f"{h}_sd_official"] for h in metrics.HECS]))
    else:
        row["mean_dice"] = float(np.mean([row[f"{h}_dice"] for h in metrics.HECS]))
        row["mean_sd"] = float("nan")
    return row


def summarize(rows: list[dict], official: bool) -> dict:
    """Turn per-case rows into the summary: means with 95% CIs per metric and region."""
    def col(key: str) -> list:
        return [r[key] for r in rows]

    out = {
        "n_cases": len(rows),
        "official_evaluator": official,
        "primary_valid": official,
        "primary": {"mean_dice": stats.describe_with_ci(col("mean_dice")),
                    "mean_surface_dice": stats.describe_with_ci(col("mean_sd"))},
        "regions": {},
    }
    for name in metrics.REGIONS:
        reg = {m: stats.describe(col(f"{name}_{m}")) for m in ("dice", "iou", "precision", "recall")}
        reg["dice"]["ci95"] = stats.bootstrap_ci(col(f"{name}_dice"))
        reg["hd95_mm"] = stats.describe(col(f"{name}_hd95_mm"))
        reg["abs_volume_error_ml"] = stats.describe(
            [abs(r[f"{name}_pred_ml"] - r[f"{name}_ref_ml"]) for r in rows])
        reg["n_ref_empty"] = int(sum(r[f"{name}_ref_ml"] == 0 for r in rows))
        if official and name in metrics.HECS:
            reg["dice_official"] = stats.describe_with_ci(col(f"{name}_dice_official"))
            reg["surface_dice_official"] = stats.describe_with_ci(col(f"{name}_sd_official"))
        out["regions"][name] = reg
    if official:
        out["dice_crosscheck_max_abs_diff"] = max(
            abs(r[f"{h}_dice"] - r[f"{h}_dice_official"]) for r in rows for h in metrics.HECS)
    return out


def main(argv: list[str] | None = None) -> int:
    """Score every prediction of one split role and write per-case and summary files."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pred-dir", type=Path, required=True)
    parser.add_argument("--segs-root", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--role", default="test", choices=("test", "val"))
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--np", type=int, default=1, help="worker processes")
    parser.add_argument("--no-official", action="store_true", help="local smoke test only")
    args = parser.parse_args(argv)

    roles = json.loads(args.split.read_text(encoding="utf-8"))["roles"]
    cases = sorted(c for c, r in roles.items() if r == args.role)
    refs = manifest.find_case_files(args.segs_root)
    missing_pred = [c for c in cases if not (args.pred_dir / f"{c}.nii.gz").exists()]
    missing_ref = [c for c in cases if len(refs.get(c, [])) != 1]
    if missing_pred or missing_ref:
        print(f"STOP: missing predictions {missing_pred}; missing/duplicate references {missing_ref}")
        return 1
    official = not args.no_official
    if official:
        from project3d.eval import official as off

        off.check_config()
    jobs = [(c, args.pred_dir / f"{c}.nii.gz", refs[c][0], official) for c in cases]
    if args.np > 1:
        with Pool(args.np) as pool:
            rows = pool.map(score_case, jobs)
    else:
        rows = [score_case(j) for j in jobs]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "per_case.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {"spec": "SPEC 004", "role": args.role, "pred_dir": str(args.pred_dir),
               "split_fingerprint_sha256": json.loads(args.split.read_text())["fingerprint_sha256"],
               **summarize(rows, official)}
    if official:
        summary["kits23_evaluator"] = off.official_version()
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    p = summary["primary"]
    print(f"{args.role}: n={len(rows)}  mean Dice {p['mean_dice'].get('mean', float('nan')):.4f} "
          f"CI {p['mean_dice']['ci95']}  mean surface Dice "
          f"{p['mean_surface_dice'].get('mean', float('nan')):.4f}")
    if official and summary["dice_crosscheck_max_abs_diff"] > CROSSCHECK_TOL:
        print(f"STOP: our Dice differs from the official Dice by "
              f"{summary['dice_crosscheck_max_abs_diff']:.2e}; check orientation/geometry")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
