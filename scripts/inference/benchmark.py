"""SPEC 008: measure speed and quality of the inference settings, on validation cases only.

Each setting runs in its own process, so its peak memory is measured on its own. The test
set is never touched: the case list comes from the split's validation role (D-014).

Example (Kaggle)::

    python scripts/inference/benchmark.py --model-dir model_package --images-root <images> \
        --segs-root <segmentations> --split split.json --training-validation fold_0/validation \
        --out reports/release/inference_benchmark.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts" / "eval")]

from project3d.data import manifest
from project3d.eval.postprocess import keep_largest_regions
from project3d.inference.predictor import LABELS, NnUNetModel, Options, Predictor

SETTINGS = {
    "full": Options(),
    "no_tta": Options(tta=False),
    "no_tta_step_0.75": Options(tta=False, tile_step=0.75),
}
N_CASES = 6
MATCH_DICE = 0.99  # SPEC 008: default settings must reproduce the training validation result


def choose_cases(roles: dict[str, str], n: int = N_CASES) -> list[str]:
    """Evenly spaced validation cases, so the choice can't favour easy ones."""
    val = sorted(c for c, r in roles.items() if r == "val")
    return [val[i] for i in np.linspace(0, len(val) - 1, min(n, len(val))).astype(int)]


def label_dice(a: np.ndarray, b: np.ndarray) -> float:
    """Mean Dice over the labels present in either volume; 1.0 if both are empty."""
    scores = []
    for label in LABELS.values():
        x, y = a == label, b == label
        if x.any() or y.any():
            scores.append(2 * float((x & y).sum()) / float(x.sum() + y.sum()))
    return float(np.mean(scores)) if scores else 1.0


def summarize(name: str, options: Options, rows: list[dict], peak_gpu_gb: float, peak_cpu_gb: float) -> dict:
    seconds = [r["seconds"] for r in rows]
    return {"setting": name, "tta": options.tta, "tile_step": options.tile_step, "n_cases": len(rows),
            "seconds_per_case_mean": round(statistics.mean(seconds), 1),
            "seconds_per_case_max": round(max(seconds), 1),
            "mean_dice": statistics.mean(r["mean_dice"] for r in rows),
            "mean_surface_dice": statistics.mean(r["mean_sd"] for r in rows),
            "peak_gpu_gb": round(peak_gpu_gb, 2), "peak_cpu_gb": round(peak_cpu_gb, 2), "per_case": rows}


def run_setting(name: str, args: argparse.Namespace, cases: list[str]) -> dict:
    import resource

    import evaluate
    import nibabel as nib
    import torch

    from project3d.eval import official

    official.check_config()
    options = SETTINGS[name]
    images, segs = manifest.find_case_files(args.images_root), manifest.find_case_files(args.segs_root)
    predictor = Predictor(NnUNetModel(args.model_dir, options), options)
    torch.cuda.reset_peak_memory_stats()
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            dst = Path(tmp) / f"{case}.nii.gz"
            start = time.time()
            summary = predictor.predict_file(images[case][0], dst)
            row = {"case_id": case, "seconds": round(time.time() - start, 1), "voxel_count": summary["voxel_count"]}
            scored = evaluate.score_case((case, dst, segs[case][0], True))
            row.update(mean_dice=scored["mean_dice"], mean_sd=scored["mean_sd"])
            if name == "full" and args.training_validation:
                done = nib.load(str(args.training_validation / f"{case}.nii.gz"))
                mine = nib.load(str(dst))
                row["dice_vs_training_validation"] = label_dice(
                    keep_largest_regions(np.asanyarray(done.dataobj).astype(np.uint8)),
                    np.asanyarray(mine.dataobj).astype(np.uint8))
            rows.append(row)
            print(name, json.dumps(row), flush=True)
    return summarize(name, options, rows, torch.cuda.max_memory_allocated() / 1e9,
                     resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--images-root", type=Path, required=True)
    ap.add_argument("--segs-root", type=Path, required=True)
    ap.add_argument("--split", type=Path, required=True)
    ap.add_argument("--training-validation", type=Path, help="SPEC 003 fold_0/validation folder")
    ap.add_argument("--n-cases", type=int, default=N_CASES)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--only", choices=list(SETTINGS), help=argparse.SUPPRESS)  # one setting, one process
    args = ap.parse_args(argv)

    split = json.loads(args.split.read_text(encoding="utf-8"))
    cases = choose_cases(split["roles"], args.n_cases)
    if args.only:
        args.out.write_text(json.dumps(run_setting(args.only, args, cases)), encoding="utf-8")
        return 0

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for name in SETTINGS:
            part = Path(tmp) / f"{name}.json"
            cmd = [sys.executable, __file__, *(sys.argv[1:] if argv is None else argv), "--only", name]
            cmd[cmd.index("--out") + 1] = str(part)
            subprocess.run(cmd, check=True)
            results.append(json.loads(part.read_text(encoding="utf-8")))

    matches = [r["dice_vs_training_validation"] for r in results[0]["per_case"]
               if "dice_vs_training_validation" in r]
    record = {"spec": "SPEC 008", "role": "val", "cases": cases,
              "split_fingerprint_sha256": split["fingerprint_sha256"],
              "settings": results, "min_dice_vs_training_validation": min(matches) if matches else None}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2), encoding="utf-8")
    for r in results:
        print(f"{r['setting']}: {r['seconds_per_case_mean']} s per case, mean Dice {r['mean_dice']:.4f}, "
              f"surface Dice {r['mean_surface_dice']:.4f}, GPU {r['peak_gpu_gb']} GB, CPU {r['peak_cpu_gb']} GB")
    if matches and min(matches) < MATCH_DICE:
        print(f"STOP: default settings differ from the training validation result ({min(matches):.4f})")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
