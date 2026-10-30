import nibabel as nib
import numpy as np
import postprocess
from helpers import write_nifti

from project3d.data import features
from project3d.eval.postprocess import keep_largest_regions


def blobs() -> np.ndarray:
    seg = np.zeros((30, 30, 30), np.uint8)
    seg[2:10, 2:10, 2:10] = 1  # largest region, with a tumor inside
    seg[4:6, 4:6, 4:6] = 2
    seg[15:21, 15:21, 15:21] = 1  # second region, with a cyst touching its edge
    seg[15:17, 15:17, 15:17] = 3
    seg[25:28, 25:28, 25:28] = 1  # false alarm
    return seg


def test_keeps_the_two_largest_regions_with_their_labels():
    seg = blobs()
    out = keep_largest_regions(seg)
    assert out[26, 26, 26] == 0
    assert (out[:22, :22, :22] == seg[:22, :22, :22]).all()
    assert out.dtype == seg.dtype


def test_regions_are_measured_across_labels():
    # kidney and tumor touching form one region, so they survive together
    seg = np.zeros((20, 20, 20), np.uint8)
    seg[0:3, 0:3, 0:3] = 1
    seg[3:6, 0:3, 0:3] = 2
    seg[10:14, 10:14, 10:14] = 1
    seg[17:19, 17:19, 17:19] = 1
    out = keep_largest_regions(seg)
    assert (out[0:6, 0:3, 0:3] == seg[0:6, 0:3, 0:3]).all()
    assert out[18, 18, 18] == 0


def test_diagonal_contact_counts_as_connected():
    seg = np.zeros((10, 10, 10), np.uint8)
    seg[1, 1, 1] = seg[2, 2, 2] = 1
    seg[5, 5, 5] = 1
    seg[8, 8, 8] = 1
    assert keep_largest_regions(seg, n=1).sum() == 2


def test_two_regions_or_fewer_are_unchanged():
    seg = blobs()
    seg[25:28, 25:28, 25:28] = 0
    assert (keep_largest_regions(seg) == seg).all()
    empty = np.zeros((5, 5, 5), np.uint8)
    assert (keep_largest_regions(empty) == empty).all()


def test_cli_keeps_geometry(tmp_path):
    pred, out = tmp_path / "pred", tmp_path / "out"
    pred.mkdir()
    src = pred / "case_00001.nii.gz"
    write_nifti(src, blobs())
    assert postprocess.main(["--pred-dir", str(pred), "--out-dir", str(out)]) == 0
    dst = out / src.name
    assert not features.geometry_mismatch(dst, src)
    saved = np.asanyarray(nib.load(str(dst)).dataobj)
    assert saved.dtype == np.uint8 and saved[26, 26, 26] == 0 and saved[5, 5, 3] == 1


def test_cli_stops_on_an_empty_folder(tmp_path):
    assert postprocess.main(["--pred-dir", str(tmp_path), "--out-dir", str(tmp_path / "o")]) == 1
