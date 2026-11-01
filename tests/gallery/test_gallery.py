import json

import build_gallery
import nibabel as nib
import numpy as np
import select_cases
from helpers import write_nifti

from project3d.data import features
from project3d.eval.metrics import REGIONS


def analysis(n=40):
    per_case = [{"case_id": f"case_{i:05d}", "mean_dice": str(i / (n - 1))} for i in range(n)]
    feats = {r["case_id"]: {"size_bin": "small" if i % 3 == 0 else "large", "has_cyst": str(i % 4 == 0)}
             for i, r in enumerate(per_case)}
    return per_case, feats


def test_selection_fills_every_group_and_keeps_the_worst():
    per_case, feats = analysis()
    rows = select_cases.select(per_case, feats)
    groups = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r["case_id"])
    assert {k: len(v) for k, v in groups.items()} == select_cases.GROUP_SIZES
    assert groups["worst"] == ["case_00000", "case_00001"]
    assert groups["best"] == ["case_00039", "case_00038"]
    assert len({r["case_id"] for r in rows}) == len(rows)
    assert all(feats[c]["size_bin"] == "small" for c in groups["small_tumor"])
    assert all(feats[c]["has_cyst"] == "True" for c in groups["with_cyst"])


def test_selection_does_not_depend_on_row_order():
    per_case, feats = analysis()
    assert select_cases.select(per_case[::-1], feats) == select_cases.select(per_case, feats)


def test_crop_box_adds_a_margin_in_mm_and_stays_inside():
    mask = np.zeros((50, 50, 20), bool)
    mask[20:30, 2:8, 10:12] = True
    box = build_gallery.crop_box(mask, (1.0, 1.0, 5.0), margin_mm=10)
    assert box == (slice(10, 40), slice(0, 18), slice(8, 14))


def fake_row(cid="case_00001"):
    row = {"case_id": cid, "mean_dice": "0.5", "mean_sd": "0.4", "kidney_and_mass_dice_official": "0.9",
           "mass_dice_official": "0.7", "tumor_dice_official": "0.6"}
    for name in REGIONS:
        row |= {f"{name}_dice": "0.8", f"{name}_ref_ml": "12.5", f"{name}_pred_ml": "11.0"}
    row["cyst_dice"] = "nan"
    return row


def build(tmp_path, pred_arr=None):
    ct = np.arange(40 * 40 * 30, dtype=np.float64).reshape(40, 40, 30) % 1000 - 500
    gt = np.zeros((40, 40, 30), np.uint8)
    gt[10:20, 10:20, 10:20] = 1
    gt[12:14, 12:14, 12:14] = 2
    pred = gt.copy() if pred_arr is None else pred_arr
    spacing = (2.0, 2.0, 3.0)
    return build_gallery.build_case(
        {"case_id": "case_00001", "group": "median"}, fake_row(),
        write_nifti(tmp_path / "in" / "ct.nii.gz", ct, spacing),
        write_nifti(tmp_path / "in" / "gt.nii.gz", gt, spacing),
        write_nifti(tmp_path / "in" / "pred.nii.gz", pred, spacing), tmp_path / "out")


def test_cropping_keeps_labels_and_position(tmp_path):
    build(tmp_path)
    folder = tmp_path / "out" / "case_00001"
    full, crop = nib.load(str(tmp_path / "in" / "gt.nii.gz")), nib.load(str(folder / "gt.nii.gz"))
    assert crop.shape == (26, 26, 20)
    # one voxel maps to the same point in space before and after the crop
    assert (crop.affine @ [0, 0, 0, 1] == full.affine @ [2, 2, 5, 1]).all()
    assert (np.asanyarray(crop.dataobj) == np.asanyarray(full.dataobj)[2:28, 2:28, 5:25]).all()
    ct_crop = nib.load(str(folder / "ct.nii.gz"))
    assert ct_crop.get_data_dtype() == np.int16
    assert int(np.asanyarray(ct_crop.dataobj)[0, 0, 0]) == int(
        np.asanyarray(nib.load(str(tmp_path / "in" / "ct.nii.gz")).dataobj)[2, 2, 5])


def test_all_three_volumes_share_shape_and_affine(tmp_path):
    build(tmp_path)
    folder = tmp_path / "out" / "case_00001"
    assert features.geometry_mismatch(folder / "ct.nii.gz", folder / "gt.nii.gz") is None
    assert features.geometry_mismatch(folder / "ct.nii.gz", folder / "pred.nii.gz") is None


def test_a_false_region_stays_inside_the_crop(tmp_path):
    pred = np.zeros((40, 40, 30), np.uint8)
    pred[35, 35, 28] = 1
    meta = build(tmp_path, pred)
    assert meta["crop_shape"][0] > 26


def test_packaged_scores_equal_the_evaluation_row(tmp_path):
    meta = build(tmp_path)
    row = fake_row()
    assert meta["scores"]["mean_dice"] == float(row["mean_dice"])
    assert meta["scores"]["tumor_dice_official"] == float(row["tumor_dice_official"])
    assert meta["volumes_ml"]["tumor"] == {"reference": 12.5, "predicted": 11.0}
    assert meta["regions"]["cyst"]["dice"] is None
    saved = json.loads((tmp_path / "out" / "case_00001" / "meta.json").read_text())
    assert saved["group"] == "median"


def test_a_prediction_with_other_geometry_is_refused(tmp_path):
    other = write_nifti(tmp_path / "p.nii.gz", np.zeros((5, 5, 5), np.uint8))
    ct = write_nifti(tmp_path / "c.nii.gz", np.zeros((6, 6, 6), np.int16))
    try:
        build_gallery.build_case({"case_id": "c", "group": "best"}, fake_row(), ct, ct, other, tmp_path / "o")
    except ValueError as exc:
        assert "match" in str(exc)
    else:
        raise AssertionError("expected a ValueError")


def test_dataset_card_states_the_terms():
    card = build_gallery.DATASET_CARD.format(n=11, margin=15)
    for phrase in ("CC BY-NC-SA 4.0", "KiTS", "crop", "not for clinical use"):
        assert phrase in card
