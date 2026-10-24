"""Secondary per-case metrics (SPEC 004).

The co-primary Dice and surface Dice come from the official KiTS23 evaluator
(see ``official.py``). This module adds the secondary metrics from
docs/evaluation.md, with the official empty-mask rule for Dice and IoU:
both empty -> 1, exactly one empty -> 0. Precision, recall and HD95 are
undefined (NaN) when their denominator mask is empty; counts are reported.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

# Official KiTS hierarchical evaluation classes first, then the remaining single classes.
HECS = {"kidney_and_mass": (1, 2, 3), "mass": (2, 3), "tumor": (2,)}
REGIONS = {**HECS, "kidney": (1,), "cyst": (3,)}
# Copied from kits23.configuration.labels; official.check_config() asserts they still match.
SD_TOLERANCES_MM = {"kidney_and_mass": 1.0330772532390826, "mass": 1.1328796488598762,
                    "tumor": 1.1498198361434828}


def region_mask(seg: np.ndarray, labels: tuple[int, ...]) -> np.ndarray:
    return np.isin(seg, labels)


def overlap(pred: np.ndarray, ref: np.ndarray) -> dict:
    """Dice, IoU, precision and recall for two boolean masks."""
    tp = int(np.count_nonzero(pred & ref))
    n_pred, n_ref = int(np.count_nonzero(pred)), int(np.count_nonzero(ref))
    if n_pred == 0 and n_ref == 0:
        dice = iou = 1.0
    elif n_pred == 0 or n_ref == 0:
        dice = iou = 0.0
    else:
        dice = 2 * tp / (n_pred + n_ref)
        iou = tp / (n_pred + n_ref - tp)
    return {"dice": dice, "iou": iou,
            "precision": tp / n_pred if n_pred else float("nan"),
            "recall": tp / n_ref if n_ref else float("nan")}


def _surface(mask: np.ndarray) -> np.ndarray:
    return mask & ~ndimage.binary_erosion(mask, border_value=0)


def hd95(pred: np.ndarray, ref: np.ndarray, spacing_mm: tuple[float, ...]) -> float:
    """95th-percentile symmetric Hausdorff distance in mm (max of the two directions).

    NaN when either mask is empty. Computed inside the bounding box of both
    masks, which holds every surface voxel, so distances are unchanged.
    """
    if not pred.any() or not ref.any():
        return float("nan")
    idx = np.argwhere(pred | ref)
    lo, hi = np.maximum(idx.min(0) - 1, 0), idx.max(0) + 2
    box = tuple(slice(a, b) for a, b in zip(lo, hi))
    p = np.pad(pred[box], 1)
    r = np.pad(ref[box], 1)
    sp, sr = _surface(p), _surface(r)
    dist_to_r = ndimage.distance_transform_edt(~sr, sampling=spacing_mm)
    dist_to_p = ndimage.distance_transform_edt(~sp, sampling=spacing_mm)
    return float(max(np.percentile(dist_to_r[sp], 95), np.percentile(dist_to_p[sr], 95)))


def case_metrics(pred_seg: np.ndarray, ref_seg: np.ndarray, spacing_mm: tuple[float, ...]) -> dict:
    """All secondary metrics for one case, flattened as ``<region>_<metric>``."""
    if pred_seg.shape != ref_seg.shape:
        raise ValueError(f"shape {pred_seg.shape} vs {ref_seg.shape}")
    voxel_ml = float(np.prod(spacing_mm)) / 1000.0
    out: dict = {}
    for name, labels in REGIONS.items():
        p, r = region_mask(pred_seg, labels), region_mask(ref_seg, labels)
        for k, v in overlap(p, r).items():
            out[f"{name}_{k}"] = v
        out[f"{name}_hd95_mm"] = hd95(p, r, spacing_mm)
        out[f"{name}_ref_ml"] = round(float(np.count_nonzero(r)) * voxel_ml, 3)
        out[f"{name}_pred_ml"] = round(float(np.count_nonzero(p)) * voxel_ml, 3)
    return out
