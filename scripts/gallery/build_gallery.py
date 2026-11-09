"""SPEC 009: crop and package the selected test cases for the public gallery.

Example (Kaggle)::

    python scripts/gallery/build_gallery.py --cases gallery_cases.json --per-case eval_pp/per_case.csv \
        --images-root <images> --segs-root <segmentations> --pred-dir pred_pp --out-dir gallery

Uses the evaluated predictions: nothing is predicted again. Each case folder holds ct.nii.gz,
pred.nii.gz, gt.nii.gz and meta.json. ``index.json`` lists all the cases for the website.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.data import features, manifest
from project3d.eval.metrics import REGIONS

if TYPE_CHECKING:
    from nibabel.spatialimages import SpatialImage

MARGIN_MM = 15.0
MAX_CASE_MB = 40  # the worst case is kept whatever its size; a false region makes its crop large
MAX_TOTAL_MB = 300
SCORES = ("mean_dice", "mean_sd", "kidney_and_mass_dice_official", "mass_dice_official", "tumor_dice_official")
VOLUMES = ("kidney", "tumor", "cyst")

DATASET_CARD = """---
license: cc-by-nc-sa-4.0
pretty_name: KiTS23 segmentation demo gallery
tags:
  - medical-imaging
  - ct
  - kidney
  - segmentation
size_categories:
  - n<1K
---

# KiTS23 segmentation demo gallery

> Research demo, not for clinical use.

{n} CT cases from the internal test set of a KiTS23 nnU-Net project, for a public 3D viewer. The
cases were chosen by a fixed rule, and the worst results are included on purpose.

Each case folder holds:

| File | Content |
|---|---|
| `ct.nii.gz` | The CT, cropped |
| `pred.nii.gz` | The model's evaluated prediction, post-processed (0 background, 1 kidney, 2 tumor, 3 cyst) |
| `gt.nii.gz` | The KiTS23 expert annotation |
| `meta.json` | Case ID, selection group, scores and region volumes |

**Crop:** each scan is cropped to the box around the true and predicted foreground, plus {margin:g} mm
on every side. CT, prediction and annotation share one shape and affine. Scores and volumes in
`meta.json` were measured on the full scan.

## Credit and license

These files are derived from KiTS23 v0.1.4 and are shared under CC BY-NC-SA 4.0: non-commercial
use only, shared under the same terms. If you use them, cite KiTS23:

> Heller N, et al. The KiTS21 Challenge: Automatic segmentation of kidneys, renal tumors, and
> renal cysts in corticomedullary-phase CT. arXiv:2307.01984. <https://github.com/neheller/kits23>

The predictions come from nnU-Net v2 (Isensee et al., Nature Methods 2021).
"""


def crop_box(mask: np.ndarray, spacing: tuple, margin_mm: float = MARGIN_MM) -> tuple[slice, ...]:
    """Box around the mask, with a margin in millimetres, kept inside the volume."""
    hits = np.argwhere(mask)
    if hits.size == 0:
        return tuple(slice(0, n) for n in mask.shape)
    box = []
    for axis, size in enumerate(mask.shape):
        pad = math.ceil(margin_mm / float(spacing[axis]))
        box.append(slice(max(int(hits[:, axis].min()) - pad, 0), min(int(hits[:, axis].max()) + 1 + pad, size)))
    return tuple(box)


def _save_crop(img: SpatialImage, box: tuple[slice, ...], dtype: npt.DTypeLike, path: Path) -> None:
    import nibabel as nib

    crop = img.slicer[box]  # updates the affine, so the crop stays in the right place in space
    data = np.round(np.asanyarray(crop.dataobj)).astype(dtype)
    out = nib.Nifti1Image(data, crop.affine)
    out.set_data_dtype(dtype)
    nib.save(out, str(path))


def case_meta(row: dict, group: str, shape: tuple, spacing: tuple) -> dict:
    """Scores and volumes copied from per_case.csv, which comes from the evaluation."""
    def number(key: str) -> float | None:
        value = float(row[key])
        return None if math.isnan(value) else value

    return {"case_id": row["case_id"], "group": group,
            "scores": {key: number(key) for key in SCORES},
            "regions": {name: {"dice": number(f"{name}_dice")} for name in REGIONS},
            "volumes_ml": {name: {"reference": number(f"{name}_ref_ml"), "predicted": number(f"{name}_pred_ml")}
                           for name in VOLUMES},
            "crop_shape": [int(n) for n in shape], "spacing_mm": [float(s) for s in spacing[:3]]}


def build_case(case: dict, row: dict, ct_path: Path, gt_path: Path, pred_path: Path, out_dir: Path) -> dict:
    """Crop the CT, label and prediction around the kidneys and describe the case."""
    import nibabel as nib

    for other in (gt_path, pred_path):
        why = features.geometry_mismatch(ct_path, other)
        if why:
            raise ValueError(f"{case['case_id']}: {other.name} doesn't match the CT ({why})")
    ct, gt, pred = (nib.load(str(p)) for p in (ct_path, gt_path, pred_path))
    spacing = tuple(float(z) for z in ct.header.get_zooms()[:3])
    # the predicted foreground counts too, or a false region outside the kidneys would be hidden
    mask = (np.asanyarray(gt.dataobj) > 0) | (np.asanyarray(pred.dataobj) > 0)
    box = crop_box(mask, spacing)
    folder = out_dir / case["case_id"]
    folder.mkdir(parents=True, exist_ok=True)
    _save_crop(ct, box, np.int16, folder / "ct.nii.gz")
    _save_crop(gt, box, np.uint8, folder / "gt.nii.gz")
    _save_crop(pred, box, np.uint8, folder / "pred.nii.gz")
    meta = case_meta(row, case["group"], tuple(s.stop - s.start for s in box), spacing)
    size_mb = sum(p.stat().st_size for p in folder.glob("*.nii.gz")) / 1e6
    if size_mb > MAX_CASE_MB:
        raise ValueError(f"{case['case_id']} is {size_mb:.1f} MB, over the {MAX_CASE_MB} MB limit")
    meta["size_mb"] = round(size_mb, 2)
    (folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> int:
    """Build the gallery files for every selected case."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--per-case", type=Path, required=True)
    parser.add_argument("--images-root", type=Path, required=True)
    parser.add_argument("--segs-root", type=Path, required=True)
    parser.add_argument("--pred-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    with open(args.per_case, newline="", encoding="utf-8") as fh:
        scores = {r["case_id"]: r for r in csv.DictReader(fh)}
    images, segs = manifest.find_case_files(args.images_root), manifest.find_case_files(args.segs_root)
    metas = []
    for case in cases:
        cid = case["case_id"]
        metas.append(build_case(case, scores[cid], images[cid][0], segs[cid][0],
                                args.pred_dir / f"{cid}.nii.gz", args.out_dir))
        print(f"{cid} {case['group']}: {metas[-1]['size_mb']} MB, crop {metas[-1]['crop_shape']}", flush=True)
    total = sum(m["size_mb"] for m in metas)
    if total > MAX_TOTAL_MB:
        print(f"STOP: gallery is {total:.0f} MB, over the {MAX_TOTAL_MB} MB limit")
        return 1
    (args.out_dir / "index.json").write_text(json.dumps(metas, indent=2), encoding="utf-8")
    (args.out_dir / "README.md").write_text(DATASET_CARD.format(n=len(metas), margin=MARGIN_MM), encoding="utf-8",
                                            newline="\n")
    print(f"gallery: {len(metas)} cases, {total:.0f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
