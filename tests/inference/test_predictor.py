import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
from helpers import write_nifti

from project3d.data import features
from project3d.inference import predictor as pr

ROOT = Path(__file__).resolve().parents[2]


class FakeModel:
    """Stands in for nnU-Net: reads with nibabel and marks a fixed pattern."""

    def read(self, path):
        img = nib.load(str(path))
        return np.asanyarray(img.dataobj)[None], {"affine": img.affine}

    def predict(self, data, properties):
        seg = np.zeros(data.shape[1:], np.int16)
        seg[1:5, 1:5, 1:5] = 1
        seg[2:4, 2:4, 2:4] = 2
        seg[8:12, 8:12, 8:12] = 1
        seg[9, 9, 9] = 3
        seg[14, 14, 14] = 1  # false alarm, removed by the D-021 rule
        return seg

    def write(self, seg, path, properties):
        nib.save(nib.Nifti1Image(seg, properties["affine"]), str(path))


def scan(tmp_path, shape=(16, 16, 16), spacing=(0.5, 0.5, 2.0)):
    return write_nifti(tmp_path / "scan.nii.gz", np.zeros(shape, np.int16), spacing)


def test_geometry_round_trip_and_postprocessing(tmp_path):
    src = scan(tmp_path)
    dst = tmp_path / "out.nii.gz"
    summary = pr.Predictor(FakeModel()).predict_file(src, dst)
    assert features.geometry_mismatch(dst, src) is None
    saved = np.asanyarray(nib.load(str(dst)).dataobj)
    assert saved[14, 14, 14] == 0 and saved[2, 2, 2] == 2
    assert summary["shape"] == [16, 16, 16] and summary["voxel_count"] == 16**3
    assert summary["spacing_mm"] == [0.5, 0.5, 2.0]


def test_a_mismatched_output_is_an_error(tmp_path):
    class Shifted(FakeModel):
        def write(self, seg, path, properties):
            nib.save(nib.Nifti1Image(seg, np.diag([9.0, 9.0, 9.0, 1.0])), str(path))

    with pytest.raises(RuntimeError, match="geometry"):
        pr.Predictor(Shifted()).predict_file(scan(tmp_path), tmp_path / "out.nii.gz")


def test_summary_has_no_file_names(tmp_path):
    summary = pr.Predictor(FakeModel()).predict_file(scan(tmp_path), tmp_path / "out.nii.gz")
    assert "scan" not in json.dumps(summary)


def test_region_volumes_use_the_spacing():
    seg = np.zeros((10, 10, 10), np.uint8)
    seg[:2, :5, :4] = 1  # 40 voxels
    seg[5, 5, :3] = 2  # 3 voxels
    assert pr.region_volumes(seg, (0.5, 1.0, 2.0)) == {"kidney_ml": 0.04, "tumor_ml": 0.003, "cyst_ml": 0.0}


@pytest.mark.parametrize("shape,spacing,why", [
    ((10, 10), (1.0, 1.0), "3D"),
    ((10, 10, 10, 2), (1.0, 1.0, 1.0, 1.0), "3D"),
    ((10, 10, 10), (0.0, 1.0, 1.0), "spacing"),
    ((10, 10, 10), (1.0, float("nan"), 1.0), "spacing"),
    ((10, 10, 10), (1.0, 1.0, 50.0), "spacing"),
    ((1000, 1000, 1000), (1.0, 1.0, 1.0), "limit"),
])
def test_invalid_headers_are_rejected(shape, spacing, why):
    with pytest.raises(pr.InvalidInput, match=why):
        pr.check_header(shape, spacing)


def test_a_file_that_is_not_nifti_is_rejected_before_the_model_runs(tmp_path):
    bad = tmp_path / "bad.nii.gz"
    bad.write_bytes(b"not a scan")

    class Untouched(FakeModel):
        def read(self, path):
            raise AssertionError("the model must not run")

    with pytest.raises(pr.InvalidInput, match="NIfTI"):
        pr.Predictor(Untouched()).predict_file(bad, tmp_path / "out.nii.gz")


def test_default_options_match_the_evaluated_setting():
    record = json.loads((ROOT / "reports/evaluation/spec004/run_record.json").read_text(encoding="utf-8"))
    assert pr.Options().tta is (not record["disable_tta"])
    assert pr.Options().tile_step == 0.5  # nnU-Net's default, used by nnUNetv2_predict_from_modelfolder


def test_tile_step_must_be_valid():
    with pytest.raises(ValueError):
        pr.Options(tile_step=0)


def test_install_trainer_copies_into_nnunet(tmp_path):
    src = tmp_path / "t.py"
    src.write_text("x = 1")
    variants = tmp_path / "variants"
    variants.mkdir()
    assert pr.install_trainer(src, variants).read_text() == "x = 1"
    assert (variants / pr.TRAINER_FILE).exists()
