"""Per-case label features used to stratify the split (D-012).

Only segmentations are read. Labels: 0 background, 1 kidney, 2 tumor, 3 cyst.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

VALID_LABELS = {0, 1, 2, 3}
KITS21_LAST_ID = 299  # cases 0-299 are the KiTS21 cohort; 400+ were added in KiTS23
SIZE_BINS = ("none", "small", "medium", "large")


def cohort_of(case_id: str) -> str:
    """Cohort proxy for contrast phase (D-010, D-012); not a phase label."""
    return "kits21" if int(case_id.split("_")[1]) <= KITS21_LAST_ID else "kits23_new"


def label_features(seg: np.ndarray, spacing_mm: tuple[float, ...]) -> dict:
    """Volumes in millilitres and presence flags from a label array."""
    present = {int(v) for v in np.unique(seg)}
    unknown = present - VALID_LABELS
    if unknown:
        raise ValueError(f"unexpected label values {sorted(unknown)}")
    counts = np.bincount(seg.ravel().astype(np.int64), minlength=4)
    voxel_ml = float(np.prod(spacing_mm)) / 1000.0
    return {
        "kidney_ml": round(counts[1] * voxel_ml, 3),
        "tumor_ml": round(counts[2] * voxel_ml, 3),
        "cyst_ml": round(counts[3] * voxel_ml, 3),
        "has_tumor": bool(counts[2] > 0),
        "has_cyst": bool(counts[3] > 0),
    }


def case_features(case_id: str, seg_path: str | Path) -> dict:
    """Read one segmentation and return its features plus header geometry."""
    import nibabel as nib

    img = nib.load(str(seg_path))
    seg = np.asanyarray(img.dataobj)
    if not np.all(np.mod(seg, 1) == 0):
        raise ValueError(f"{case_id}: non-integer label values")
    seg = seg.astype(np.uint8)
    spacing = tuple(float(z) for z in img.header.get_zooms()[:3])
    row = {"case_id": case_id, "cohort": cohort_of(case_id),
           "shape": "x".join(map(str, seg.shape)),
           "spacing_mm": "x".join(f"{s:.4f}" for s in spacing)}
    row.update(label_features(seg, spacing))
    return row


def geometry_mismatch(image_path: str | Path, seg_path: str | Path, atol: float = 1e-3) -> str | None:
    """Compare image and mask headers (no voxel data read). None if they match."""
    import nibabel as nib

    img, seg = nib.load(str(image_path)), nib.load(str(seg_path))
    if img.shape[:3] != seg.shape[:3]:
        return f"shape {img.shape[:3]} vs {seg.shape[:3]}"
    if not np.allclose(img.affine, seg.affine, atol=atol):
        return "affine differs"
    return None


def add_size_bins(rows: list[dict]) -> tuple[float, float]:
    """Add ``size_bin`` in place: tertiles of tumor volume among tumor cases.

    Cases without tumor get ``none``. Returns the two cut points (ml) so they
    can be recorded with the split.
    """
    vols = np.array([r["tumor_ml"] for r in rows if r["has_tumor"]], dtype=float)
    if vols.size == 0:
        cuts = (0.0, 0.0)
    else:
        q1, q2 = np.quantile(vols, [1 / 3, 2 / 3])
        cuts = (float(q1), float(q2))
    for r in rows:
        if not r["has_tumor"]:
            r["size_bin"] = "none"
        elif r["tumor_ml"] <= cuts[0]:
            r["size_bin"] = "small"
        elif r["tumor_ml"] <= cuts[1]:
            r["size_bin"] = "medium"
        else:
            r["size_bin"] = "large"
    return cuts
