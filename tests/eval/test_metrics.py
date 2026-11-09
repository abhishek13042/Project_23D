import math

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from project3d.eval import metrics as m
from project3d.eval import stats


def test_empty_masks_follow_the_empty_mask_rule():
    e = np.zeros((4, 4, 4), bool)
    full = e.copy()
    full[1:3, 1:3, 1:3] = True
    both_empty = m.overlap(e, e)
    assert both_empty["dice"] == 1.0 and both_empty["iou"] == 1.0
    assert math.isnan(both_empty["precision"]) and math.isnan(both_empty["recall"])
    assert m.overlap(full, e)["dice"] == 0.0  # false positive
    assert m.overlap(e, full)["dice"] == 0.0  # complete miss
    assert m.overlap(e, full)["recall"] == 0.0
    assert math.isnan(m.hd95(full, e, (1, 1, 1)))


def test_overlap_scores_match_the_formulas():
    p = np.zeros(10, bool)
    r = np.zeros(10, bool)
    p[:4] = True  # 4 predicted
    r[2:8] = True  # 6 reference, 2 overlap
    o = m.overlap(p, r)
    assert o["dice"] == pytest.approx(4 / 10)
    assert o["iou"] == pytest.approx(2 / 8)
    assert o["precision"] == pytest.approx(2 / 4)
    assert o["recall"] == pytest.approx(2 / 6)


def test_hd95_parallel_planes_uses_spacing():
    a = np.zeros((10, 6, 6), bool)
    b = a.copy()
    a[2] = True
    b[5] = True
    assert m.hd95(a, b, (2.5, 1.0, 1.0)) == pytest.approx(7.5)
    assert m.hd95(a, a, (2.5, 1.0, 1.0)) == 0.0


def _brute_hd95(p, r, sp):
    def surf(x):
        return np.argwhere(m._surface(np.pad(x, 1))) * np.array(sp)
    d = cdist(surf(p), surf(r))
    return max(np.percentile(d.min(1), 95), np.percentile(d.min(0), 95))


def test_hd95_matches_brute_force():
    rng = np.random.default_rng(1)
    from scipy import ndimage
    for _ in range(3):
        p = ndimage.binary_dilation(rng.random((14, 16, 12)) > 0.97, iterations=2)
        r = ndimage.binary_dilation(rng.random((14, 16, 12)) > 0.97, iterations=2)
        sp = (3.0, 0.8, 0.8)
        assert m.hd95(p, r, sp) == pytest.approx(_brute_hd95(p, r, sp))


def test_case_metrics_scores_each_region():
    ref = np.zeros((6, 6, 6), np.uint8)
    ref[1:5, 1:5, 1:5] = 1
    ref[2:4, 2:4, 2:4] = 2
    pred = ref.copy()
    pred[pred == 2] = 3  # tumor predicted as cyst
    row = m.case_metrics(pred, ref, (1.0, 1.0, 1.0))
    assert row["kidney_and_mass_dice"] == 1.0
    assert row["mass_dice"] == 1.0
    assert row["tumor_dice"] == 0.0
    assert row["cyst_dice"] == 0.0  # cyst absent in reference, present in prediction
    assert row["tumor_ref_ml"] == pytest.approx(0.008)
    assert set(m.HECS) < set(m.REGIONS)


def test_bootstrap_ci_brackets_the_mean_and_is_seeded():
    vals = np.linspace(0.5, 1.0, 50)
    lo, hi = stats.bootstrap_ci(vals)
    assert lo < vals.mean() < hi
    assert stats.bootstrap_ci(vals) == [lo, hi]  # seeded
    assert stats.bootstrap_ci(vals[:5]) is None
    d = stats.describe([1.0, float("nan"), 3.0])
    assert d["n"] == 2 and d["n_undefined"] == 1 and d["mean"] == 2.0
