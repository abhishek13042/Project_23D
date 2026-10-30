"""SPEC 005 / E-005: performance by case characteristics, plus figures.

Example::

    python scripts/eval/case_analysis.py --per-case eval/per_case.csv \
        --case-features spec002/case_features.csv --images-root <images> \
        --segs-root <segmentations> --pred-dir pred_pp --out-dir analysis

Writes analysis.json, analysis.md and figures/ (box plots; best, median and
worst overlays). No GPU needed.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.data import manifest
from project3d.eval import analysis, figures


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--per-case", type=Path, required=True)
    ap.add_argument("--case-features", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--images-root", type=Path, help="needed for overlay figures")
    ap.add_argument("--segs-root", type=Path)
    ap.add_argument("--pred-dir", type=Path)
    args = ap.parse_args(argv)

    rows = analysis.join_rows(read_csv(args.per_case), read_csv(args.case_features))
    result = analysis.analyse(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    figdir = args.out_dir / "figures"
    made = [figures.boxplot_by_group(rows, "size_bin", "tumor_dice", analysis.SIZE_ORDER,
                                     figdir / "tumor_dice_by_size_bin.png"),
            figures.boxplot_by_group(rows, "cohort", "mean_dice", ["kits21", "kits23_new"],
                                     figdir / "mean_dice_by_cohort.png")]
    examples = analysis.pick_examples(rows)
    result["examples"] = examples
    if args.images_root and args.segs_root and args.pred_dir:
        import nibabel as nib

        imgs = manifest.find_case_files(args.images_root)
        segs = manifest.find_case_files(args.segs_root)
        score = {r["case_id"]: r["mean_dice"] for r in rows}
        for kind, cid in examples.items():
            ref_img = nib.load(str(segs[cid][0]))
            spacing = tuple(float(z) for z in ref_img.header.get_zooms()[:3])
            made.append(figures.overlay_figure(
                np.asanyarray(nib.load(str(imgs[cid][0])).dataobj, dtype=np.float32),
                np.asanyarray(ref_img.dataobj).astype(np.uint8),
                np.asanyarray(nib.load(str(args.pred_dir / f"{cid}.nii.gz")).dataobj).astype(np.uint8),
                spacing, f"{kind}: {cid}  mean Dice {score[cid]:.3f}",
                figdir / f"overlay_{kind}_{cid}.png"))
    result["figures"] = [p.name for p in made]
    (args.out_dir / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (args.out_dir / "analysis.md").write_text(analysis.to_markdown(result), encoding="utf-8")
    print(f"analysis: {len(rows)} cases, {len(made)} figures -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
