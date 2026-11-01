import json

import nibabel as nib
import numpy as np
import pytest
import service
from helpers import write_nifti
from test_predictor import FakeModel

from project3d.inference.predictor import InvalidInput


def scan(tmp_path, shape=(20, 20, 20), spacing=(1.0, 1.0, 1.0), name="ct.nii.gz"):
    return write_nifti(tmp_path / name, np.zeros(shape, np.int16), spacing)


def header_only(tmp_path, shape, spacing=(1.0, 1.0, 1.0)):
    """A file that claims a huge shape, with no voxel data behind it."""
    path = tmp_path / "huge.nii"
    header = nib.Nifti1Header()
    header.set_data_shape(shape)
    header.set_data_dtype(np.int16)
    header.set_zooms(spacing)
    header["magic"] = b"n+1"
    header["vox_offset"] = 352
    path.write_bytes(header.binaryblock + bytes(4))
    return path


def test_a_good_scan_passes(tmp_path):
    service.check_upload(scan(tmp_path))


@pytest.mark.parametrize("name", ["ct.mha", "ct.dcm", "ct.nii.zip"])
def test_other_file_types_are_refused(tmp_path, name):
    path = tmp_path / name
    path.write_bytes(b"x")
    with pytest.raises(InvalidInput, match="NIfTI"):
        service.check_upload(path)


def test_a_broken_file_is_refused(tmp_path):
    path = tmp_path / "ct.nii.gz"
    path.write_bytes(b"not a scan")
    with pytest.raises(InvalidInput, match="could not be read"):
        service.check_upload(path)


def test_a_large_file_is_refused_by_its_size(tmp_path):
    with pytest.raises(InvalidInput, match="limit"):
        service.check_upload(scan(tmp_path), max_mb=0.000001)


def test_a_file_claiming_too_many_voxels_is_refused_from_its_header(tmp_path):
    with pytest.raises(InvalidInput, match="voxels"):
        service.check_upload(header_only(tmp_path, (1024, 1024, 1024)))


def test_a_4d_image_and_a_bad_spacing_are_refused(tmp_path):
    with pytest.raises(InvalidInput, match="3D"):
        service.check_upload(write_nifti(tmp_path / "time.nii.gz", np.zeros((9, 9, 9, 2), np.int16), (1.0, 1.0, 1.0)))
    with pytest.raises(InvalidInput, match="spacing"):
        service.check_upload(scan(tmp_path, spacing=(1.0, 1.0, 50.0)))


def test_small_scan_gets_the_minimum_gpu_time(tmp_path):
    assert service.gpu_seconds(scan(tmp_path)) == service.MIN_GPU_SECONDS


def test_limit_sized_scan_is_capped(tmp_path):
    path = header_only(tmp_path, (512, 512, 760), (0.8, 0.8, 1.0))
    assert service.gpu_seconds(path) == service.MAX_GPU_SECONDS


def test_gpu_time_grows_with_the_voxels_the_model_sees(tmp_path):
    typical = service.gpu_seconds(header_only(tmp_path, (512, 512, 100), (0.8, 0.8, 3.0)))
    larger = service.gpu_seconds(header_only(tmp_path, (512, 512, 200), (0.8, 0.8, 3.0)))
    assert service.MIN_GPU_SECONDS <= typical < larger <= service.MAX_GPU_SECONDS


def test_thick_slices_count_as_the_slices_they_become():
    thin = service.resampled_voxels((100, 100, 100), service.TARGET_SPACING_MM)
    assert thin == pytest.approx(1e6)
    assert service.resampled_voxels((100, 100, 100), (2.0, 0.78125, 0.78125)) == pytest.approx(2e6)


def test_api_returns_a_segmentation_and_a_summary_with_no_file_name(tmp_path):
    src = scan(tmp_path, name="patient_smith.nii.gz")
    out, summary = service.segment_file(FakeModel(), src, tmp_path)
    assert out.name == service.RESULT_NAME and out.exists()
    assert nib.load(str(out)).shape == (20, 20, 20)
    assert summary["notice"] == service.DISCLAIMER
    assert set(summary["volumes_ml"]) == {"kidney_ml", "tumor_ml", "cyst_ml"}
    assert "smith" not in json.dumps(summary)


@pytest.mark.parametrize(("exc", "code"), [
    (InvalidInput("Too big"), "INVALID_INPUT: Too big"),
    (RuntimeError("You have exceeded your free GPU quota"), "QUOTA_EXCEEDED:"),
    (RuntimeError("queue is full"), "BUSY:"),
    (RuntimeError("cuda error in /tmp/gradio/abc/patient_smith.nii.gz"), "FAILED:"),
])
def test_errors_have_a_stable_code(exc, code):
    text = service.error_text(exc)
    assert text.startswith(code)
    assert "smith" not in text
