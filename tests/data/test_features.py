import numpy as np
import pytest
from helpers import make_seg, write_nifti

from project3d.data import features as f


def test_cohort_proxy():
    assert f.cohort_of("case_00000") == "kits21"
    assert f.cohort_of("case_00299") == "kits21"
    assert f.cohort_of("case_00400") == "kits23_new"


def test_volumes_use_physical_spacing(tmp_path):
    p = write_nifti(tmp_path / "case_00007.nii.gz", make_seg(kidney=20, tumor=10, cyst=4),
                    spacing=(0.5, 0.5, 4.0))  # 1 mm^3 per voxel = 0.001 ml
    row = f.case_features("case_00007", p)
    assert row["kidney_ml"] == pytest.approx(0.020)
    assert row["tumor_ml"] == pytest.approx(0.010)
    assert row["cyst_ml"] == pytest.approx(0.004)
    assert row["has_tumor"] and row["has_cyst"]
    assert row["spacing_mm"] == "0.5000x0.5000x4.0000"


def test_rejects_unknown_labels():
    seg = make_seg(tumor=3)
    seg[0, 0, 0] = 7
    with pytest.raises(ValueError, match="unexpected label"):
        f.label_features(seg, (1, 1, 1))


def test_size_bins_tertiles():
    rows = [{"tumor_ml": v, "has_tumor": v > 0} for v in [0, 1, 2, 3, 4, 5, 6]]
    cuts = f.add_size_bins(rows)
    assert [r["size_bin"] for r in rows] == ["none", "small", "small", "medium", "medium", "large", "large"]
    assert cuts == (pytest.approx(8 / 3), pytest.approx(13 / 3))


def test_no_tumor_cases_only():
    rows = [{"tumor_ml": 0.0, "has_tumor": False} for _ in range(3)]
    f.add_size_bins(rows)
    assert {r["size_bin"] for r in rows} == {"none"}
    assert np.isfinite(f.add_size_bins(rows)).all()


def test_geometry_mismatch(tmp_path):
    seg = make_seg(tumor=3)
    img = write_nifti(tmp_path / "img.nii.gz", seg.astype(np.float32))
    same = write_nifti(tmp_path / "same.nii.gz", seg)
    moved = write_nifti(tmp_path / "moved.nii.gz", seg, spacing=(1.0, 1.0, 3.0))
    cropped = write_nifti(tmp_path / "cropped.nii.gz", seg[:, :, :5])
    assert f.geometry_mismatch(img, same) is None
    assert f.geometry_mismatch(img, moved) == "affine differs"
    assert f.geometry_mismatch(img, cropped).startswith("shape")
