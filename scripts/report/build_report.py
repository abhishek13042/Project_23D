"""SPEC 007: build reports/evaluation/results.md from the saved Kaggle records.

Copy the Kaggle outputs into the repository first (docs/REPRODUCE.md):

    reports/data/spec002_run_record.json        SPEC 002 run_record.json
    reports/training/spec003_run_record.json    SPEC 003 run record (when it exists)
    reports/evaluation/spec004/                 SPEC 004 output without pred_* folders

Then run ``python scripts/report/build_report.py``. Every number in the report
comes from those files; anything missing is written as "pending", never guessed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HECS = ["kidney_and_mass", "mass", "tumor"]
REGIONS = HECS + ["kidney", "cyst"]
PENDING = "*pending*"


def load(path: Path | None) -> dict | None:
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def num(v, digits: int = 3) -> str:
    return PENDING if v is None else f"{v:.{digits}f}"


def mean_ci(d: dict | None) -> str:
    if not d or d.get("mean") is None:
        return PENDING
    ci = d.get("ci95")
    return f"{d['mean']:.3f} (95% CI {ci[0]:.3f}–{ci[1]:.3f})" if ci else f"{d['mean']:.3f} (no CI, n < 10)"


def median_iqr(d: dict | None, digits: int = 3) -> str:
    if not d or d.get("median") is None:
        return "–"
    return f"{d['median']:.{digits}f} [{d['q1']:.{digits}f}, {d['q3']:.{digits}f}]"


def setup_section(prep: dict | None, train: dict | None, run: dict | None) -> list[str]:
    def row(label, value):
        return f"| {label} | {PENDING if value is None else value} |"

    totals = (prep or {}).get("split_totals")
    split = (f"{totals.get('train')}/{totals.get('val')}/{totals.get('test')} (train/val/test)"
             if totals else None)
    lines = ["## 1. Setup", "", "| Item | Value |", "|---|---|",
             row("Data", "KiTS23 v0.1.4, 489 labeled cases"),
             row("Split", split),
             row("Split fingerprint", (prep or {}).get("split_fingerprint_sha256")),
             row("nnU-Net", (prep or {}).get("nnunetv2")),
             row("Configuration", "3d_fullres, fold 0 (D-012)"),
             row("3d_fullres patch / spacing", None if not prep else
                 f"{prep.get('fullres_patch_size')} / {prep.get('fullres_spacing')}")]
    if train:
        for k, v in train.items():
            if k != "spec":
                lines.append(row(f"Training: {k}", v))
    else:
        lines.append(row("Training (SPEC 003)", None))
    if run:
        lines += [row("Test-time augmentation", "off" if run.get("disable_tta") else "on (mirroring)"),
                  row("Post-processing (chosen on validation)",
                      "applied" if run.get("postprocessing_applied") else "not applied"),
                  row("Evaluator", run.get("kits23_evaluator")),
                  row("GPU / inference hours", f"{run.get('gpu')} / {run.get('predict_hours')}")]
    return lines + [""]


def headline_section(pp: dict | None, raw: dict | None) -> list[str]:
    n = pp["n_cases"] if pp else None
    lines = [f"## 2. Headline result (internal test set, n = {n if n else PENDING})", ""]
    if pp and not pp.get("primary_valid", False):
        lines += ["> **Not valid:** these numbers were made without the official evaluator.", ""]
    lines += ["| Predictions | Mean Dice (3 HECs) | Mean surface Dice (3 HECs) |", "|---|---|---|"]
    for name, s in (("post-processed (primary)", pp), ("raw", raw)):
        p = (s or {}).get("primary", {})
        lines.append(f"| {name} | {mean_ci(p.get('mean_dice'))} | {mean_ci(p.get('mean_surface_dice'))} |")
    lines += ["", "Per case: average of the three HEC scores; then average over cases. CIs: case "
              "bootstrap, 10 000 resamples. This is an internal split of the public training "
              "cases, so it is **not** comparable to the KiTS23 challenge leaderboard.", ""]
    return lines


def regions_section(pp: dict | None) -> list[str]:
    lines = ["## 3. Per region (post-processed)", ""]
    if not pp:
        return lines + [PENDING, ""]
    lines += ["| Region | Official Dice | Official surface Dice |", "|---|---|---|"]
    for h in HECS:
        r = pp["regions"][h]
        lines.append(f"| {h} | {mean_ci(r.get('dice_official'))} | {mean_ci(r.get('surface_dice_official'))} |")
    lines += ["", "Secondary metrics, median [IQR] over cases. HD95 is only defined when both "
              "masks are non-empty; *n HD95* counts those cases.", "",
              "| Region | Dice | Precision | Recall | HD95 mm | n HD95 | Abs. volume error ml | empty ref |",
              "|---|---|---|---|---|---|---|---|"]
    for name in REGIONS:
        r = pp["regions"][name]
        lines.append(f"| {name} | {median_iqr(r['dice'])} | {median_iqr(r['precision'])} | "
                     f"{median_iqr(r['recall'])} | {median_iqr(r['hd95_mm'], 1)} | {r['hd95_mm']['n']} | "
                     f"{median_iqr(r['abs_volume_error_ml'], 1)} | {r['n_ref_empty']} |")
    return lines + [""]


def checks_section(prep: dict | None, pp: dict | None, run: dict | None) -> list[str]:
    lines = ["## 4. Integrity checks", ""]
    fp_prep = (prep or {}).get("split_fingerprint_sha256")
    fp_eval = (pp or {}).get("split_fingerprint_sha256")
    if fp_prep and fp_eval:
        ok = fp_prep == fp_eval
        lines.append(f"- Split fingerprint, SPEC 002 vs SPEC 004: {'match' if ok else '**MISMATCH**'}")
    else:
        lines.append(f"- Split fingerprint, SPEC 002 vs SPEC 004: {PENDING}")
    diff = (pp or {}).get("dice_crosscheck_max_abs_diff")
    lines.append(f"- Our Dice vs official Dice, max difference: "
                 f"{PENDING if diff is None else f'{diff:.1e} (limit 1e-3)'}")
    lines.append(f"- Test cases scored: {PENDING if not pp else pp['n_cases']}")
    return lines + [""]


def build(prep_path: Path, train_path: Path, eval_dir: Path, out: Path) -> str:
    prep, train = load(prep_path), load(train_path)
    pp, raw = load(eval_dir / "eval_pp" / "summary.json"), load(eval_dir / "eval_raw" / "summary.json")
    run = load(eval_dir / "run_record.json")
    analysis = eval_dir / "analysis" / "analysis.md"
    lines = ["# Results — nnU-Net v2 on KiTS23 (internal test set)", "",
             "Generated by `scripts/report/build_report.py` from the saved run records. "
             "Do not edit by hand.", ""]
    lines += setup_section(prep, train, run)
    lines += headline_section(pp, raw)
    lines += regions_section(pp)
    lines += checks_section(prep, pp, run)
    lines += ["## 5. Case analysis (SPEC 005)", ""]
    if analysis.exists():
        rel = Path(os.path.relpath(analysis, out.parent)).as_posix()
        lines += [f"See [{rel}]({rel}) for groups by tumor size, cyst, cohort and volume, "
                  "and the figures next to it.", ""]
    else:
        lines += [PENDING, ""]
    lines += ["## 6. Limitations", "",
              "One model, one fold, a shortened 100-epoch schedule (D-012), and an internal "
              "test split. See [docs/limitations.md](../../docs/limitations.md) and the "
              "[model card](../release/model_card.md).", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prep-record", type=Path, default=ROOT / "reports/data/spec002_run_record.json")
    ap.add_argument("--train-record", type=Path, default=ROOT / "reports/training/spec003_run_record.json")
    ap.add_argument("--eval-dir", type=Path, default=ROOT / "reports/evaluation/spec004")
    ap.add_argument("--out", type=Path, default=ROOT / "reports/evaluation/results.md")
    args = ap.parse_args(argv)
    text = build(args.prep_record, args.train_record, args.eval_dir, args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {args.out} ({text.count(PENDING)} items pending)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
